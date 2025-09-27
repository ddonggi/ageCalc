### 서버 생성 & 기본 셋업

AWS EC2 인스턴스 생성 (Ubuntu LTS)

t3a.small (2vCPU/2GB) 이상 추천

보안그룹: 80/443 허용, SSH(22)는 필요 시만

- 내 인스턴스 아키텍처 확인
```sh
uname -m
# x86_64 이면 intel/amd, aarch64 이면 ARM(Graviton)

# x86_64
``` 

기본 패키지 설치
```sh
sudo apt-get update
sudo apt-get install -y nginx git curl htop bzip2 tar ca-certificates
```

도메인 → EC2 IP 매핑 (Route53 or Cloudflare)

---


0) 공통 ― 폴더 구조 & 환경 정의
```css
/srv/
  ├─ apps/
  │   ├─ agecalc/
  │   │   ├─ app.py
  │   │   ├─ environment.yml
  │   │   └─ gunicorn_conf.py   # 선택
  │   └─ site-b/ (동일 구조)
  └─ infra/
      └─ nginx/
          ├─ nginx.conf
          └─ conf.d/
              ├─ site-a.conf
              └─ site-b.conf
```
- sample environment.yml (두 사이트 공통으로 써도 됨)
```yml
name: ageCalc
channels:
  - conda-forge
  - defaults
dependencies:
  - python=3.12
  - flask=2.3.3
  - werkzeug=2.3.7
  - gunicorn=21.2.0
  - pip
  - pip:
      # pip 전용 패키지가 있으면 여기에 추가
```


- sample 
sudo vi app.py (공통)
```python
from flask import Flask
app = Flask(__name__)

@app.get("/health")
def health():
    return {"ok": True}, 200

@app.get("/")
def home():
    return "Hello from Flask (micromamba)!"
```

### 1) Non-Docker (추천: 단일 EC2 + Nginx + systemd)
1-1. micromamba 설치 (Ubuntu) 공용으로 사용
```bash
# 아키텍처 확인: uname -m (x86_64 또는 aarch64)
# /usr/local/bin (모든 계정 PATH에 기본 포함됨)에 설치
curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest \
  | sudo tar -xvj -C /usr/local/bin --strip-components=1 bin/micromamba

# tar (grandchild): bzip2: Cannot exec: No such file or directory
# tar (grandchild): Error is not recoverable: exiting now

micromamba --help # 동작 확인
micromamba --version
2.3.2
```

1-2. 사이트별 리눅스 계정/환경 생성
각 사이트별로 리눅스 계정 분리 → 격리된 환경 관리가 깔끔합니다.
```bash
# site-a (agecalc) 계정 생성
sudo adduser --disabled-password --gecos "" agecalc

# 관리자 권한으로 디렉터리 생성
sudo mkdir -p /srv/apps/agecalc
sudo chown -R agecalc:agecalc /srv/apps/agecalc

sudo -iu agecalc
cd /srv/apps/agecalc

# 환경 생성
micromamba create -y -p /srv/apps/agecalc/.micromamba/envs/agecalc -f environment.yml

# 실행 확인
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -V

#To activate this environment, use:

micromamba activate /srv/apps/agecalc/.micromamba/envs/agecalc

#Or to execute a single command in this environment, use:

micromamba run -p /srv/apps/agecalc/.micromamba/envs/agecalc mycommand

# site-b도 동일
```
> 포인트: 활성화(activate) 없이 .../envs/agecalc/bin/... 절대 경로로 실행하면 깔끔합니다.

1-3. systemd 유닛 (사이트별)
우분투 계정으로 진행
sudo vi /etc/systemd/system/agecalc.service
```ìni
[Unit]
Description=Gunicorn (agecalc, micromamba)
After=network.target

[Service]
User=agecalc
Group=www-data
WorkingDirectory=/srv/apps/agecalc
Environment="PATH=/srv/apps/agecalc/.micromamba/envs/agecalc/bin"
ExecStart=/srv/apps/agecalc/.micromamba/envs/agecalc/bin/gunicorn app:app \
  --bind unix:/run/agecalc.sock \
  --workers 4 --threads 2 --timeout 30 --keep-alive 5 \
  --max-requests 1000 --max-requests-jitter 200
RuntimeDirectory=agecalc
RuntimeDirectoryMode=0755
Restart=always

[Install]
WantedBy=multi-user.target
```

```
sudo systemctl daemon-reload
sudo systemctl enable --now agecalc
sudo systemctl status agecalc
```

1-4. Nginx 리버스 프록시 (vhost)
sudo vi /srv/apps/infra/nginx/conf.d/agecalc.conf
```bash
server {
  listen 80;
  server_name calc1.example.com;

  # (선택) HSTS는 443 구성 후 켜기
  # add_header Strict-Transport-Security "max-age=31536000" always;

  location / {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_pass http://unix:/run/agecalc.sock;
  }

  location /health { 
    proxy_pass http://unix:/run/agecalc.sock; 
  }
}
```

적용:
```sh
sudo nginx -t && sudo systemctl reload nginx
# nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
# nginx: configuration file /etc/nginx/nginx.conf test is successful
```

- 앱 정상 작동 확인
  - curl --unix-socket /run/agecalc/agecalc.sock http://localhost/health

1-5. HTTPS SSL 적용 - (도메인 연결 완료 후.)
Let's Encrypt
certbot 설치:
```
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
```
SSL 인증서 발급 (Nginx 플러그인 사용):
```
sudo certbot --nginx -d calc1.example.com -d www.calc1.example.com
```

자동 갱신 확인:
```
sudo systemctl list-timers | grep certbot
```
---
Nginx가 먼저 요청을 받아서, 도메인/경로에 따라 어떤 app.py(Gunicorn 프로세스)로 보낼지를 결정합니다.

--- 

운영 팁

로그 확인:

앱: journalctl -u agecalc -f

Nginx: /var/log/nginx/error.log

배포 업데이트:

새 코드 배포 → systemctl restart agecalc

### 2) Docker 루트 (micromamba 베이스 이미지)
2-1. Dockerfile
```bash
# syntax=docker/dockerfile:1
FROM mambaorg/micromamba:1.5.8

# 작업 디렉터리
WORKDIR /app
# 환경 정의 복사 & 설치
COPY environment.yml /tmp/environment.yml
RUN micromamba create -y -n appenv -f /tmp/environment.yml && micromamba clean --all --yes
# 환경 활성화 없이 절대경로로 실행할 것이므로 PATH만 보강
ENV PATH=/opt/conda/envs/appenv/bin:$PATH

# 앱 복사
COPY . /app

# 비root 유저
USER $MAMBA_USER

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD wget -qO- http://127.0.0.1:8000/health || exit 1

CMD ["gunicorn","app:app","-b","0.0.0.0:8000","--workers","4","--threads","2","--timeout","30","--keep-alive","5","--max-requests","1000","--max-requests-jitter","200"]
```

2-2. docker-compose.yml (여러 사이트 + Nginx)
```bash
version: "3.9"
services:
  site_a:
    build: ./apps/site-a
    container_name: site_a
    restart: always

  site_b:
    build: ./apps/site-b
    container_name: site_b
    restart: always

  nginx:
    image: nginx:1.27
    container_name: edge
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./infra/nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./infra/nginx/conf.d:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro   # certbot 병행 시
    depends_on:
      - site_a
      - site_b
    restart: always
```

2-3. Nginx vhost (컨테이너 이름으로 proxy)
```bash
/srv/apps/infra/nginx/conf.d/site-a.conf

server {
  listen 80;
  server_name calc1.example.com;

  location / {
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_pass http://site_a:8000;
  }

  location /health { proxy_pass http://site_a:8000/health; }
}
```
2-4. 배포 명령
```bash
docker compose build
docker compose up -d
docker compose ps
curl -I http://calc1.example.com/health
```
---
3) 운영 팁 (공통)

- 로그:
  - Non-Docker: journalctl -u sitea -f, Nginx /var/log/nginx/access.log
  - Docker: docker logs -f site_a, docker logs -f edge

- 성능 튜닝: workers = CPU 코어 × 2~4, I/O 혼합이면 --threads 2

- 안정화: --max-requests/--max-requests-jitter로 메모리 누수 대비

- 캐시: Nginx proxy_cache(짧은 TTL) + 정적은 S3/CloudFront

- 보안: EC2 보안그룹은 80/443만, SSH는 SSM; 비밀은 SSM Parameter Store

- 여러 사이트: 도메인별 vhost/서비스를 그대로 복제(이름/포트/소켓만 변경)