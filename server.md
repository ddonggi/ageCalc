### 서버 생성 & 기본 셋업

AWS EC2 인스턴스 생성 (Ubuntu LTS)

t3a.small (2vCPU/2GB) 이상 추천

보안그룹: 80/443 허용, SSH(22)는 필요 시만

기본 패키지 설치
```
sudo apt-get update
sudo apt-get install -y nginx git curl htop
```

도메인 → EC2 IP 매핑 (Route53 or Cloudflare)

---


0) 공통 ― 폴더 구조 & 환경 정의
```css
/srv/apps
  ├─ apps/
  │   ├─ site-a/
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
name: sitea
channels:
  - conda-forge
dependencies:
  - python=3.12
  - pip
  - pip:
      - flask==3.0.3
      - gunicorn==22.0.0
```

- sample app.py (공통)
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

1) Non-Docker (추천: 단일 EC2 + Nginx + systemd)
1-1. micromamba 설치 (Ubuntu)
```bash
cd /tmp
curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest | tar -xvj bin/micromamba
sudo mv bin/micromamba /usr/local/bin/micromamba
micromamba --help  # 동작 확인
```

1-2. 사이트별 리눅스 계정/환경 생성
```bash
# site-a 사용자
sudo adduser --disabled-password --gecos "" sitea
sudo -iu sitea bash << 'EOF'
mkdir -p ~/.mamba ~/.cache/mamba /srv/apps/apps/site-a
cd /srv/apps/apps/site-a

# 환경 생성(프로젝트 로컬에)
micromamba create -y -p /srv/apps/apps/site-a/.micromamba/envs/sitea -f environment.yml
# 의존성 확인
/srv/apps/apps/site-a/.micromamba/envs/sitea/bin/python -V
EOF

# site-b도 동일
```

> 포인트: 활성화(activate) 없이 .../envs/sitea/bin/... 절대 경로로 실행하면 깔끔합니다.

1-3. systemd 유닛 (사이트별)
/etc/systemd/system/sitea.service
```ìni
[Unit]
Description=Gunicorn (site-a, micromamba)
After=network.target

[Service]
User=sitea
Group=www-data
WorkingDirectory=/srv/apps/apps/site-a
Environment="PATH=/srv/apps/apps/site-a/.micromamba/envs/sitea/bin"
# gunicorn_conf.py 있으면 -c 로 주입 가능
ExecStart=/srv/apps/apps/site-a/.micromamba/envs/sitea/bin/gunicorn app:app \
  --bind unix:/run/sitea.sock \
  --workers 4 --threads 2 --timeout 30 --keep-alive 5 \
  --max-requests 1000 --max-requests-jitter 200
RuntimeDirectory=sitea
RuntimeDirectoryMode=0755
Restart=always

[Install]
WantedBy=multi-user.target

sudo systemctl daemon-reload
sudo systemctl enable --now sitea
sudo systemctl status sitea
```

1-4. Nginx 리버스 프록시 (vhost)
/srv/apps/infra/nginx/conf.d/site-a.conf
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
    proxy_pass http://unix:/run/sitea.sock;
  }

  location /health { proxy_pass http://unix:/run/sitea.sock; }
}
```

적용:
```sh
sudo nginx -t && sudo systemctl reload nginx
```

1-5. HTTPS

쉬움: Cloudflare 프록시 사용(오렌지 구름 ON) → 원서버는 80만 열어도 OK

직접: `sudo snap install core; sudo snap refresh core; sudo snap install --classic certbot`
```sh
sudo certbot --nginx -d calc1.example.com
```

---

2) Docker 루트 (micromamba 베이스 이미지)
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