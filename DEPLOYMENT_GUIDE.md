# AgeCalc 배포 가이드 (AWS EC2 + Nginx + Gunicorn + MySQL)

이 문서는 **현재 프로젝트 소스 기준**으로 작성되었습니다.

## 1. 배포 아키텍처
- OS: Ubuntu LTS (EC2)
- App: Flask (`app.py`)
- WSGI: Gunicorn (unix socket: `/run/agecalc/agecalc.sock`)
- Reverse Proxy: Nginx (`nginx/agecalc.conf` 기반)
- DB: MySQL (EC2 로컬 설치 기준)

## 2. 서버 준비

### 2.1 EC2 생성
- 인스턴스: `t3a.small` 이상 권장
- 보안그룹 인바운드
  - `22` (관리자 IP만)
  - `80`, `443` (전체)
  - 같은 서버에서 MySQL 사용 시 `3306`은 열지 않음

### 2.2 접속 및 기본 패키지
```bash
ssh -i <KEY.pem> ubuntu@<EC2_PUBLIC_IP>
sudo apt-get update
sudo apt-get install -y nginx git curl htop bzip2 tar ca-certificates
```

## 3. 앱 배치

### 3.1 앱 사용자/디렉터리
```bash
sudo adduser --disabled-password --gecos "" agecalc
sudo mkdir -p /srv/apps
sudo chown -R agecalc:agecalc /srv/apps
```

### 3.2 코드 배치
- 리포지토리를 `/srv/apps/agecalc`에 배치
- 예시
```bash
cd /srv/apps
git clone <REPO_URL> agecalc
sudo chown -R agecalc:agecalc /srv/apps/agecalc
```

## 4. Python 런타임/의존성

### 4.1 (권장) micromamba 사용
```bash
curl -L https://micro.mamba.pm/api/micromamba/linux-64/latest \
  | sudo tar -xvj -C /usr/local/bin --strip-components=1 bin/micromamba
```

### 4.2 환경 생성 및 패키지 설치
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
micromamba create -y -p /srv/apps/agecalc/.micromamba/envs/agecalc -f environment.yml
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/pip install -r requirements.txt
```

## 5. MySQL 직접 설치 (EC2 동일 서버)

### 5.1 설치/시작
```bash
sudo apt update
sudo apt install -y mysql-server
sudo systemctl enable mysql
sudo systemctl start mysql
sudo systemctl status mysql
```

### 5.2 초기 보안
```bash
sudo mysql_secure_installation
```
권장:
- Remove anonymous users: `Y`
- Disallow root login remotely: `Y`
- Remove test database: `Y`
- Reload privilege tables: `Y`

### 5.3 DB/계정 생성
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

### 5.4 연결 확인
```bash
mysql -u agecalc_user -p -h 127.0.0.1 -D agecalc -e "SELECT NOW() AS now_time;"
```

## 6. systemd 서비스 등록 (Gunicorn)

`/etc/systemd/system/agecalc.service`
```ini
[Unit]
Description=Gunicorn (agecalc)
After=network.target

[Service]
User=agecalc
Group=www-data
WorkingDirectory=/srv/apps/agecalc
Environment="PATH=/srv/apps/agecalc/.micromamba/envs/agecalc/bin"
Environment="DATABASE_URL=mysql+pymysql://agecalc_user:CHANGE_ME_STRONG_PASSWORD@127.0.0.1:3306/agecalc?charset=utf8mb4"
RuntimeDirectory=agecalc
RuntimeDirectoryMode=0755
ExecStart=/srv/apps/agecalc/.micromamba/envs/agecalc/bin/gunicorn app:app \
  --bind unix:/run/agecalc/agecalc.sock \
  --workers 2 --threads 2 --timeout 30 --keep-alive 5
Restart=always

[Install]
WantedBy=multi-user.target
```

적용:
```bash
sudo systemctl daemon-reload
sudo systemctl enable --now agecalc
sudo systemctl status agecalc
```

## 7. Nginx 설정

프로젝트의 `nginx/agecalc.conf`를 서버 설정으로 반영합니다.

```bash
sudo cp /srv/apps/agecalc/nginx/agecalc.conf /etc/nginx/conf.d/agecalc.conf
sudo nginx -t
sudo systemctl reload nginx
```

체크:
```bash
curl --unix-socket /run/agecalc/agecalc.sock http://localhost/health
curl -I https://<YOUR_DOMAIN>/health
```

## 8. SSL (Let's Encrypt)
```bash
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
sudo certbot --nginx -d <YOUR_DOMAIN> -d www.<YOUR_DOMAIN>
```

## 9. 배포 후 검증
- 앱 헬스체크: `/health` 응답 `200`
- 정적 파일: `/static/...` 정상 로드
- 블로그 목록: `/blog` 접근 가능
- 블로그 상세: `/blog/<slug>` 접근 가능
- DB 테이블 확인:
```bash
mysql -u agecalc_user -p -h 127.0.0.1 -D agecalc -e "SHOW TABLES;"
```
예상 테이블:
- `generated_posts`
- `feed_sources`
- `feed_items`
- `post_sources`

## 10. 문제 해결
- `Access denied for user`
  - 계정 host(`localhost`), 비밀번호, `DATABASE_URL` 확인
- `Can't connect to MySQL server`
  - `sudo systemctl status mysql`
  - `ss -lntp | grep 3306`
- Gunicorn 미기동
  - `sudo journalctl -u agecalc -n 200 --no-pager`
- Nginx 502
  - 소켓 존재 확인: `/run/agecalc/agecalc.sock`
  - `sudo systemctl status agecalc --no-pager`
  - `sudo journalctl -u agecalc -n 200 --no-pager`
  - `curl --unix-socket /run/agecalc/agecalc.sock http://localhost/health`
  - `sudo nginx -t`
  - `sudo tail -n 200 /var/log/nginx/error.log`

## 11. 운영 체크리스트
- [ ] 도메인 DNS 연결 완료
- [ ] SSL 인증서 발급 완료
- [ ] `agecalc.service` 정상 실행
- [ ] MySQL 연결/권한 확인
- [ ] 블로그/계산기/미니게임 라우트 점검
- [ ] 로그 모니터링 설정
