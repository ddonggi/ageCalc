# AgeCalc 배포 가이드

AWS EC2 Ubuntu, Nginx, Gunicorn, MySQL, systemd 기준의 설치·배포 예시입니다. 아래 경로·계정·서비스 설정은 실행 전에 실제 서버와 대조합니다. 이 문서 열람은 운영 변경 승인에 해당하지 않습니다.

[문서 목차](docs/README.md) · [개발 환경](docs/DEVELOPMENT.md) · [공개 정책](docs/operations/runtime-policy.md)

기능 개발은 확인된 pre-release에서 수행하고, 승인된 main 병합·push 후 운영에서 `git pull --ff-only`를 실행합니다. 필요한 마이그레이션·재시작·검증은 승인된 배포 계획에 따릅니다. 대상 커밋·실행 계정·DB 변경·백업·복구·중단 조건을 먼저 기록합니다.

## 1. 배포 구조
```mermaid
flowchart TB
    Internet[Internet] --> Nginx[Nginx TLS reverse proxy]
    Nginx --> Socket[/Unix socket: /run/agecalc/agecalc.sock/]
    Socket --> Gunicorn[Gunicorn agecalc.service]
    Gunicorn --> Flask[Flask app.py]
    Flask --> MySQL[(Local MySQL)]
    Flask --> Static[Static files]
    Timer[agecalc-rss.timer] --> RSSService[agecalc-rss.service]
    RSSService --> Scheduler[scripts/rss_blog_scheduler.py]
    Scheduler --> MySQL
    Scheduler --> OpenAI[OpenAI text/image APIs]
```

## 2. 서버 준비
### EC2 권장값
- OS: Ubuntu LTS
- Instance: `t3a.small` 이상 권장
- Inbound: `22`는 관리자 IP만, `80`/`443`은 전체
- MySQL을 같은 서버에서만 쓰면 `3306`은 외부에 열지 않습니다.

### 기본 패키지
```bash
ssh -i <KEY.pem> ubuntu@<EC2_PUBLIC_IP>
sudo apt-get update
sudo apt-get install -y nginx git curl htop bzip2 tar ca-certificates
```

## 3. 앱 계정과 코드 배치
```bash
sudo adduser --disabled-password --gecos "" agecalc
sudo mkdir -p /srv/apps
sudo chown -R agecalc:agecalc /srv/apps
cd /srv/apps
git clone <REPO_URL> agecalc
sudo chown -R agecalc:agecalc /srv/apps/agecalc
```

아래는 운영 계정·경로 예시입니다. 기능 수정은 운영 폴더가 아닌 확인된 개발 작업 트리에서 하며, 운영 스크립트 실행은 해당 작업 권한을 확인합니다.

```bash
sudo -iu agecalc
cd /srv/apps/agecalc
```

서비스 재시작, Nginx reload, systemd 설정 반영은 `ubuntu` 계정에서 `sudo`로 실행합니다.

## 4. Python 런타임
### micromamba 설치
```bash
curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest \
  | sudo tar -xvj -C /usr/local/bin --strip-components=1 bin/micromamba
```

### 환경 생성
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
micromamba create -y -p /srv/apps/agecalc/.micromamba/envs/agecalc -f environment.yml
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/pip install -r requirements.txt
exit
```

## 5. MySQL
### 설치
```bash
sudo apt update
sudo apt install -y mysql-server
sudo systemctl enable mysql
sudo systemctl start mysql
sudo systemctl status mysql
```

### DB와 계정
```bash
sudo mysql
```

```sql
CREATE DATABASE IF NOT EXISTS agecalc
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER IF NOT EXISTS 'agecalc_user'@'localhost'
  IDENTIFIED BY 'CHANGE_ME_STRONG_PASSWORD';

GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX
  ON agecalc.* TO 'agecalc_user'@'localhost';

FLUSH PRIVILEGES;
EXIT;
```

연결 확인:
```bash
mysql -u agecalc_user -p -h 127.0.0.1 -D agecalc -e "SELECT NOW() AS now_time;"
```

## 6. 환경 변수
운영 환경 변수는 `/srv/apps/agecalc/.env.rss`에 둡니다. 이 파일은 앱 서비스와 RSS 스케줄러가 같이 읽습니다.

```bash
sudo -iu agecalc
cd /srv/apps/agecalc
cp .env.rss.example .env.rss
chmod 600 .env.rss
```

필수 또는 권장 값:
- `DATABASE_URL`: MySQL 연결 문자열
- `AGECALC_ENV`: 운영에서는 반드시 `production`
- `OPENAI_API_KEY`: OpenAI 글/이미지 생성
- `OPENAI_MODEL`: 기본값 `gpt-4.1-mini`
- `OPENAI_IMAGE_MODEL`: 기본값 `gpt-image-1`
- `BLOG_BASE_URL`: 기본값 `https://agecalc.cloud`
- `BLOG_REVIEW_TOKEN`: 토큰 기반 검토 링크
- `BLOG_DRAFT_PASSWORD`: `/blog/drafts` 접근 비밀번호
- `COUPANG_PARTNERS_ENABLED`: 승인 모드가 해제된 경우에만 제휴 노출 가능. [공개 정책](docs/operations/runtime-policy.md) 참조
- `SMTP_*`: draft 생성 알림 메일
- `FLASK_SECRET_KEY`: Flask 세션 서명 키

기존 운영 환경도 배포 전에 `AGECALC_ENV=production`과 충분히 긴 `FLASK_SECRET_KEY`를 추가해야 합니다. MySQL 또는 PostgreSQL 연결을 사용하는데 세션 키가 없으면 앱은 안전을 위해 시작하지 않습니다.

민감 정보는 저장소에 커밋하지 않습니다.

## 7. Gunicorn systemd 서비스
현재 앱은 `agecalc.service`로 실행합니다.

`/etc/systemd/system/agecalc.service`
```ini
[Unit]
Description=Gunicorn (agecalc, micromamba)
After=network.target

[Service]
User=agecalc
Group=www-data
WorkingDirectory=/srv/apps/agecalc
Environment="PATH=/srv/apps/agecalc/.micromamba/envs/agecalc/bin"
EnvironmentFile=/srv/apps/agecalc/.env.rss
RuntimeDirectory=agecalc
RuntimeDirectoryMode=0755
ExecStart=/srv/apps/agecalc/.micromamba/envs/agecalc/bin/gunicorn app:app \
  --bind unix:/run/agecalc/agecalc.sock \
  --workers 2 --threads 2 --timeout 30 --keep-alive 5 \
  --max-requests 1000 --max-requests-jitter 200
Restart=always

[Install]
WantedBy=multi-user.target
```

적용:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now agecalc.service
sudo systemctl status agecalc.service --no-pager
```

코드 변경 반영:
```bash
sudo systemctl restart agecalc.service
```

## 8. Nginx와 SSL
프로젝트의 `nginx/agecalc.conf`를 서버 설정으로 반영합니다.

```bash
sudo cp /srv/apps/agecalc/nginx/agecalc.conf /etc/nginx/conf.d/agecalc.conf
sudo nginx -t
sudo systemctl reload nginx
```

Let's Encrypt:
```bash
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d agecalc.cloud -d www.agecalc.cloud
```

확인:
```bash
curl --unix-socket /run/agecalc/agecalc.sock http://localhost/health
curl -I https://agecalc.cloud/health
```

### SSL 인증서 만료/갱신 대응

인증서 확인·Certbot 복구·갱신·타이머 점검은 [TLS 인증서 운영 안내](docs/operations/tls-certificates.md)를 참고하세요.

## 9. RSS 블로그 스케줄러
### 현재 production 스케줄
아래는 기존 운영 구성 예시입니다. 저장소 timer는 09:00·12:00·19:00을 정의하지만 타임존은 서버 설정에 따라 달라집니다. 설치된 timer/service의 시간대·활성화 상태·실행 인자를 확인하세요.

실행당 초안 1개를 생성하는 명령 예시:
```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python \
  /srv/apps/agecalc/scripts/rss_blog_scheduler.py run \
  --limit 1 --status draft --provider openai --model gpt-4.1-mini
```

### RSS 소스 등록
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rss_blog_scheduler.py import-sources --file scripts/rss_sources.example.json
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rss_blog_scheduler.py list-sources
exit
```

### 1회 실행
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rss_blog_scheduler.py run --limit 1 --status draft --provider openai --model gpt-4.1-mini
exit
```

### systemd timer 등록
```bash
sudo cp /srv/apps/agecalc/systemd/agecalc-rss.service /etc/systemd/system/agecalc-rss.service
sudo cp /srv/apps/agecalc/systemd/agecalc-rss.timer /etc/systemd/system/agecalc-rss.timer
sudo systemctl daemon-reload
sudo systemctl enable --now agecalc-rss.timer
sudo systemctl status agecalc-rss.timer --no-pager
```

수동 트리거와 로그:
```bash
sudo systemctl start agecalc-rss.service
sudo journalctl -u agecalc-rss.service -n 200 --no-pager
```

## 10. 블로그 공개 기준

본문 길이·소제목·출처·대표 이미지·상태 전환 기준은 [블로그 품질 및 공개 절차](docs/BLOG_WORKFLOW.md#current-quality-gates)에서 관리합니다. 초안 검토·공개 권한은 배포 권한과 별도로 확인합니다. 공개 후 검색 색인은 [공개 정책](docs/operations/runtime-policy.md)을 함께 따릅니다.

## 11. 배포 후 검증
- `/health` 응답 `200`
- `/sitemap.xml` 응답 정상
- 핵심 계산기 페이지 정상
- `/about`, `/contact`, `/references`, `/privacy`, `/terms` 접근 가능
- `/blog`는 공개 글 수뿐 아니라 승인 모드·블로그 색인 플래그를 함께 확인: [공개 정책](docs/operations/runtime-policy.md)
- `/blog/<slug>`는 `published` 글만 접근 가능
- `/blog/drafts`는 비밀번호 세션 필요
- `/static/generated/blog-covers/` 이미지 파일 로드 가능

애드센스 재검토 전 사전점검:
```bash
cd /srv/apps/agecalc
set -a
source .env.rss
set +a
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/adsense_preflight.py
```

이 명령은 로컬 Flask 라우트의 사이트맵·noindex·광고 코드·robots.txt·ads.txt 등을 점검하며 외부 운영 URL의 실응답을 검사하지 않습니다. 앱 import 전에 DB와 환경을 명시적으로 확인하세요. 위 운영 환경 source 예시는 승인된 운영 검증에만 사용하며 개발 환경에서는 [DB 격리 안내](docs/DEVELOPMENT.md)를 따릅니다.

DB 테이블 확인:
```bash
mysql -u agecalc_user -p -h 127.0.0.1 -D agecalc -e "SHOW TABLES;"
```

예상 테이블:
- `feed_sources`
- `feed_items`
- `generated_posts`
- `post_sources`
- `page_feedback` (블로그 외 페이지 피드백 모델)

## 12. 문제 해결
- MySQL 접속 실패: `sudo systemctl status mysql`, `ss -lntp | grep 3306`, `DATABASE_URL` 확인
- Gunicorn 미기동: `sudo journalctl -u agecalc.service -n 200 --no-pager`
- Nginx 502: `/run/agecalc/agecalc.sock` 존재 여부와 `sudo nginx -t` 확인
- RSS 생성 실패: `sudo journalctl -u agecalc-rss.service -n 200 --no-pager`
- OpenAI 생성 결과가 짧음: `needs_review`로 저장되는 것이 정상입니다. `scripts/rewrite_blog_posts.py --status all --all --attempts 2 --apply --publish-on-pass --demote-failed-published`로 기존 글을 보강하거나 프롬프트/토큰 설정을 조정합니다.
- draft 공개 실패: `/blog/drafts/<slug>`의 오류 메시지에서 본문 길이, 대표 이미지, 출처, 내부 링크 누락 여부를 확인합니다.

## 13. 운영 체크리스트
- [ ] DNS가 `agecalc.cloud`와 `www.agecalc.cloud`에 연결됨
- [ ] SSL 인증서 발급 완료
- [ ] `agecalc.service` 정상 실행
- [ ] `agecalc-rss.timer` 활성화
- [ ] MySQL 연결/권한 확인
- [ ] `.env.rss` 권한 `600`
- [ ] 블로그 공개 전 draft 검수
- [ ] `scripts/adsense_preflight.py` 통과
- [ ] sitemap과 robots.txt 확인
- [ ] 로그 모니터링 확인
