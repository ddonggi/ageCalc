# SSL 인증서 만료·갱신 대응
HTTPS 접속 시 인증서 만료 오류가 보이면 먼저 현재 인증서 상태와 만료일을 확인합니다.

```bash
sudo certbot certificates
openssl s_client -connect agecalc.cloud:443 -servername agecalc.cloud </dev/null 2>/dev/null | openssl x509 -noout -dates
```

`sudo: certbot: command not found`가 나오지만 `/etc/letsencrypt/live/agecalc.cloud/fullchain.pem` 파일이 존재한다면, 인증서 설정은 남아 있고 Certbot 실행 파일만 사라졌거나 PATH 연결이 끊긴 상태일 가능성이 큽니다. 먼저 설치 위치를 확인합니다.

```bash
command -v certbot
ls -l /snap/bin/certbot /usr/bin/certbot /usr/local/bin/certbot
snap list certbot
dpkg -l | grep certbot
```

Snap Certbot이 남아 있으면 직접 실행하거나 `/usr/bin/certbot` 링크를 복구합니다.

```bash
sudo /snap/bin/certbot certificates
sudo ln -sf /snap/bin/certbot /usr/bin/certbot
sudo certbot certificates
```

Certbot이 완전히 제거된 상태라면 다시 설치합니다. 기존 `/etc/letsencrypt` 디렉터리는 삭제하지 않습니다.

```bash
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot
sudo certbot certificates
```

`/usr/bin/certbot -> /snap/bin/certbot` 심볼릭 링크만 있고 `snap: command not found` 또는 `/snap/bin/certbot: No such file or directory`가 나오면, Snap이 제거되어 Certbot 링크가 깨진 상태입니다. 이 경우 Snap을 먼저 복구한 뒤 Certbot을 다시 설치합니다.

```bash
sudo apt update
sudo apt install -y snapd
sudo systemctl enable --now snapd.socket
sudo snap install core
sudo snap refresh core
sudo snap install --classic certbot
sudo ln -sf /snap/bin/certbot /usr/bin/certbot
sudo certbot certificates
```

Certbot 자동 갱신이 정상 동작하는지 dry-run으로 점검합니다.

```bash
sudo certbot renew --dry-run
```

dry-run이 성공하면 실제 갱신을 실행하고 Nginx 설정을 검증한 뒤 reload합니다.

```bash
sudo certbot renew
sudo nginx -t
sudo systemctl reload nginx
curl -I https://agecalc.cloud/health
```

갱신이 실패하거나 인증서가 누락된 경우에는 Nginx 플러그인으로 다시 발급합니다.

```bash
sudo certbot --nginx -d agecalc.cloud -d www.agecalc.cloud
sudo nginx -t
sudo systemctl reload nginx
```

자동 갱신 타이머도 함께 확인합니다. Snap으로 설치한 경우와 OS 패키지로 설치한 경우 서비스 이름이 다를 수 있습니다.

```bash
systemctl list-timers | grep -E 'certbot|snap.certbot'
systemctl status snap.certbot.renew.timer
systemctl status certbot.timer
```

`certbot.timer` 또는 `snap.certbot.renew.timer` 중 존재하는 타이머가 active 상태여야 합니다. 갱신 후에도 브라우저에서 만료 인증서가 계속 보이면 Nginx reload 여부, `/etc/letsencrypt/live/agecalc.cloud/fullchain.pem` 경로, CDN/프록시 캐시 사용 여부를 순서대로 확인합니다.


[배포 가이드](../../DEPLOYMENT_GUIDE.md) · [문서 목차](../README.md)
