# 🚀 만 나이 계산기 배포 가이드

## 📋 배포 전 필수 설정

### 1. 구글 애드센스 설정
```html
<!-- HTML에서 다음 부분을 실제 값으로 교체 -->
data-ad-client="ca-pub-YOUR_PUBLISHER_ID"  <!-- 실제 Publisher ID로 교체 -->
data-ad-slot="YOUR_AD_SLOT_ID"             <!-- 실제 Ad Slot ID로 교체 -->
```

**설정 방법:**
1. [Google AdSense](https://www.google.com/adsense) 가입
2. 사이트 승인 후 Publisher ID 발급
3. 광고 단위 생성 후 Ad Slot ID 발급
4. HTML 코드에 실제 값 입력

### 2. 구글 애널리틱스 설정
```html
<!-- HTML에서 다음 부분을 실제 값으로 교체 -->
gtag('config', 'GA_MEASUREMENT_ID');  <!-- 실제 GA ID로 교체 -->
```

**설정 방법:**
1. [Google Analytics](https://analytics.google.com/) 계정 생성
2. 속성 생성 후 측정 ID 발급
3. HTML 코드에 실제 측정 ID 입력

### 3. 구글 검색 콘솔 인증
```html
<!-- HTML에서 다음 부분을 실제 값으로 교체 -->
<meta name="google-site-verification" content="YOUR_VERIFICATION_CODE" />
```

**설정 방법:**
1. [Google Search Console](https://search.google.com/search-console) 접속
2. 도메인 추가 후 인증 코드 발급
3. HTML 코드에 실제 인증 코드 입력

### 4. 네이버 웹마스터 도구 인증
```html
<!-- HTML에서 다음 부분을 실제 값으로 교체 -->
<meta name="naver-site-verification" content="YOUR_NAVER_VERIFICATION_CODE" />
```

**설정 방법:**
1. [네이버 서치어드바이저](https://searchadvisor.naver.com/) 접속
2. 사이트 등록 후 인증 코드 발급
3. HTML 코드에 실제 인증 코드 입력

## 🌐 도메인 설정

### 1. robots.txt 수정
```txt
# robots.txt에서 실제 도메인으로 교체
Sitemap: https://yourdomain.com/sitemap.xml
```

### 2. sitemap.xml 수정
```xml
<!-- sitemap.xml에서 실제 도메인으로 교체 -->
<loc>https://yourdomain.com/</loc>
<loc>https://yourdomain.com/static/css/style.css</loc>
<loc>https://yourdomain.com/static/js/age-calculator.js</loc>
```

### 3. 사이트맵 자동 생성
```bash
python generate_sitemap.py
# 도메인 입력 후 자동으로 sitemap.xml 생성
```

## 🔒 보안 및 성능 최적화

### 1. HTTPS 설정
- SSL 인증서 설치 필수
- 모든 HTTP 요청을 HTTPS로 리다이렉트

### 2. 캐싱 설정
```nginx
# nginx.conf 예시
location ~* \.(css|js|png|jpg|jpeg|gif|ico|svg)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
}
```

### 3. 압축 설정
```nginx
# nginx.conf 예시
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
```

## 📱 모바일 최적화

### 1. 반응형 이미지
- `og-image.png`: 1200x630px (소셜 미디어 공유용)
- `favicon.ico`: 16x16, 32x32px
- `apple-touch-icon.png`: 180x180px

### 2. 메타 뷰포트
```html
<meta name="viewport" content="width=device-width, initial-scale=1.0">
```

## 🚀 배포 단계

### 1. 코드 최적화
```bash
# 불필요한 파일 제거
rm -rf __pycache__/
rm -rf .git/
rm -rf .vscode/
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_secret_key_here
```

### 3. 서버 업로드
```bash
# 파일 업로드
scp -r ageCalc/ user@your-server:/var/www/
```

### 4. 서버 설정
```bash
# 권한 설정
chmod 755 /var/www/ageCalc
chmod 644 /var/www/ageCalc/*.py
chmod 644 /var/www/ageCalc/static/css/*.css
chmod 644 /var/www/ageCalc/static/js/*.js
```

## 📊 모니터링 및 유지보수

### 1. 로그 모니터링
```bash
# Flask 로그 확인
tail -f /var/log/flask/agecalc.log

# nginx 로그 확인
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 2. 성능 모니터링
- Google PageSpeed Insights
- GTmetrix
- WebPageTest

### 3. 정기 업데이트
- 사이트맵 자동 생성 스케줄링
- 로그 파일 로테이션
- 보안 업데이트 적용

## 🔧 문제 해결

### 1. 광고가 표시되지 않는 경우
- AdSense 계정 상태 확인
- 사이트 승인 상태 확인
- 광고 차단기 비활성화 확인

### 2. 애널리틱스가 작동하지 않는 경우
- GA 측정 ID 확인
- 쿠키 동의 상태 확인
- 네트워크 연결 상태 확인

### 3. SEO 성능 저하
- 사이트맵 제출 상태 확인
- robots.txt 설정 확인
- 메타 태그 유효성 검사

## 📞 지원 및 문의

배포 관련 문제가 발생하면 다음을 확인하세요:
1. 로그 파일 확인
2. 브라우저 개발자 도구 확인
3. 서버 상태 확인
4. 도메인 DNS 설정 확인

---

**🚀 성공적인 배포를 위한 체크리스트:**
- [ ] 구글 애드센스 설정 완료
- [ ] 구글 애널리틱스 설정 완료
- [ ] 구글 검색 콘솔 인증 완료
- [ ] 네이버 웹마스터 도구 인증 완료
- [ ] 도메인 설정 완료
- [ ] HTTPS 설정 완료
- [ ] 사이트맵 생성 및 제출 완료
- [ ] 성능 테스트 완료
- [ ] 모바일 최적화 확인 완료
