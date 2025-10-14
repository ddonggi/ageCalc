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
/etc/
  └─ nginx/
      ├─ nginx.conf
      └─ conf.d/
            ├─ agecalc.conf
            └─ site-b.conf
```

- mamba용 environment.yml (두 사이트 공통으로 써도 됨)
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

1-2. 사이트별 리눅스 계정
각 사이트별로 리눅스 계정 분리 → 격리된 환경 관리가 깔끔합니다.
```bash
# site-a (agecalc) 계정 생성
sudo adduser --disabled-password --gecos "" agecalc

# 관리자 권한으로 디렉터리 생성
sudo mkdir -p /srv/apps/
git clone 후 
sudo chown -R agecalc:agecalc /srv/apps/

sudo -iu agecalc
cd /srv/apps/agecalc

```


- 환경 생성
```
# environment.yml 기반 환경 생성
micromamba create -y -p /srv/apps/agecalc/.micromamba/envs/agecalc -f environment.yml

# 실행 확인
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -V

# 앱 requirements.txt 다운
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/pip install -r requirements.txt

# Flask 앱 단독 실행 (개발 서버)
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python app.py
# 운영용 (Gunicorn)
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/gunicorn app:app --bind 0.0.0.0:8000

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

# 🔸 RuntimeDirectory를 쓰면 /run/agecalc/ 를 자동 생성/정리
RuntimeDirectory=agecalc
RuntimeDirectoryMode=0755

# 🔸 소켓을 /run/agecalc/agecalc.sock 에 만들기
ExecStart=/srv/apps/agecalc/.micromamba/envs/agecalc/bin/gunicorn app:app \
  --bind unix:/run/agecalc/agecalc.sock \
  --workers 2 --threads 2 --timeout 30 --keep-alive 5 \
  --max-requests 1000 --max-requests-jitter 200

# (문제 원인 파악용) 필요시 잠깐 디버그
# ExecStart=/srv/apps/agecalc/.micromamba/envs/agecalc/bin/gunicorn app:app \
#   --bind unix:/run/agecalc/agecalc.sock --log-level debug

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
sudo vi /etc/nginx/conf.d/agecalc.conf
```bash
server {
  listen 443 ssl;
  listen [::]:443 ssl;
  server_name agecalc.cloud www.agecalc.cloud;

  ssl_certificate /etc/letsencrypt/live/agecalc.cloud/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/agecalc.cloud/privkey.pem;

  location / {
    proxy_pass http://unix:/run/agecalc/agecalc.sock;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }

  location /health {
    proxy_pass http://unix:/run/agecalc/agecalc.sock;
  }
}

# HTTP 요청은 HTTPS로 리다이렉트
server {
  listen 80;
  listen [::]:80;
  server_name agecalc.cloud www.agecalc.cloud;
  return 301 https://$host$request_uri;
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

Sat 2025-09-27 21:17:00 UTC 11h left       n/a                         n/a          snap.certbot.renew.timer       snap.certbot.renew.service
```

### robots, sitemap 매핑
/etc/nginx/conf.d/agecalc.conf 
```
location = /robots.txt {
  alias /srv/apps/agecalc/static/robots.txt;
  default_type text/plain;
}

location = /sitemap.xml {
  alias /srv/apps/agecalc/static/sitemap.xml;
  default_type application/xml;
}
```

`sudo nginx -t && sudo systemctl reload nginx`

---
Nginx가 먼저 요청을 받아서, 도메인/경로에 따라 어떤 app.py(Gunicorn 프로세스)로 보낼지를 결정합니다.

만약 기본 nginx 만 나온다면
1) 기본 사이트 비활성화

기본 서버블록이 먼저 잡혀서 기본 페이지가 보일 수 있어요.

sudo unlink /etc/nginx/sites-enabled/default  # 기본 사이트 끄기

--- 

운영 팁

로그 확인:

앱: journalctl -u agecalc -f

Nginx: /var/log/nginx/error.log

배포 업데이트:

새 코드 배포 → sudo systemctl restart agecalc

---
1) 운영 팁 (공통)

- 로그:
  - Non-Docker: journalctl -u sitea -f, Nginx /var/log/nginx/access.log
  - Docker: docker logs -f site_a, docker logs -f edge

- 성능 튜닝: workers = CPU 코어 × 2~4, I/O 혼합이면 --threads 2

- 안정화: --max-requests/--max-requests-jitter로 메모리 누수 대비

- 캐시: Nginx proxy_cache(짧은 TTL) + 정적은 S3/CloudFront

- 보안: EC2 보안그룹은 80/443만, SSH는 SSM; 비밀은 SSM Parameter Store

- 여러 사이트: 도메인별 vhost/서비스를 그대로 복제(이름/포트/소켓만 변경)