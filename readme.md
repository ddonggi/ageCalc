# 만 나이 계산기

Flask를 사용하여 MVC 패턴으로 구현된 만 나이 계산 웹 애플리케이션입니다.

## 🏗️ 프로젝트 구조 (MVC 패턴)

```
ageCalc/
├── models/                 # Model (데이터 및 비즈니스 로직)
│   ├── __init__.py
│   └── age_calculator.py  # 나이 계산 로직
├── controllers/            # Controller (요청 처리)
│   ├── __init__.py
│   └── age_controller.py  # 나이 계산 요청 처리
├── views/                  # View (표시 로직)
│   └── templates/         # HTML 템플릿
│       └── index.html     # 메인 페이지
├── static/                 # 정적 파일
│   └── css/
│       └── style.css      # 스타일시트
├── app.py                 # Flask 메인 애플리케이션
├── requirements.txt        # Python 의존성
└── readme.md              # 프로젝트 설명서
```

## 🚀 설치 및 실행

1. **micromamba 환경 활성화 및 pip 설치**
   ```bash
   conda activate ageCalc
   conda install pip
   ```

2. **의존성 설치**
   ```bash
   pip install -r requirements.txt
   ```

3. **애플리케이션 실행**
   ```bash
   python app.py
   ```

3. **브라우저에서 접속**
   ```
   http://localhost:5000
   ```

## ✨ 주요 기능

- **정확한 만 나이 계산**: 생년월일을 입력하면 정확한 만 나이를 계산
- **사용자 친화적 UI**: 직관적이고 아름다운 웹 인터페이스
- **반응형 디자인**: 모바일과 데스크톱 모두 지원
- **에러 처리**: 잘못된 입력에 대한 적절한 에러 메시지

## 🔧 MVC 패턴 구현

### Model (`models/age_calculator.py`)
- 나이 계산 비즈니스 로직
- 날짜 파싱 및 검증
- 순수한 계산 함수들

### Controller (`controllers/age_controller.py`)
- 사용자 요청 처리
- Model과 View 간의 중재
- 입력 검증 및 결과 포맷팅

### View (`templates/index.html`)
- 사용자 인터페이스
- 결과 표시
- 반응형 HTML 구조

## 🎨 UI 특징

- 그라데이션 배경과 카드 스타일 디자인
- 부드러운 애니메이션과 호버 효과
- 직관적인 폼 입력과 결과 표시
- 모바일 최적화된 반응형 레이아웃

## 📱 사용법

1. 생년월일을 선택하거나 입력
2. "나이 계산하기" 버튼 클릭
3. 정확한 만 나이 확인

## 🛠️ 기술 스택

- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3
- **아키텍처**: MVC 패턴
- **스타일링**: CSS Grid, Flexbox, CSS Variables

## 🔍 SEO 최적화

### 메타 태그
- 제목, 설명, 키워드 최적화
- Open Graph 및 Twitter Card 지원
- 한국어 지역화 메타 태그

### 사이트맵
- `sitemap.xml` 자동 생성
- 정적 리소스 포함
- 우선순위 및 업데이트 빈도 설정

### Robots.txt
- 검색 엔진 크롤링 규칙
- 이미지 크롤링 허용
- 사이트맵 위치 안내

### SEO 설정 방법
1. **도메인 설정**: `robots.txt`와 `sitemap.xml`의 URL을 실제 도메인으로 수정
2. **사이트맵 생성**: `python generate_sitemap.py` 실행하여 최신 사이트맵 생성
3. **Google Search Console**: 사이트맵 제출 및 검색 성능 모니터링
4. **메타 태그 확인**: 브라우저 개발자 도구에서 메타 태그 확인

### 권장 이미지
- `static/images/og-image.png` (1200x630px)
- `favicon.ico` (16x16, 32x32px)
- `apple-touch-icon.png` (180x180px)