# AgeCalc

Flask 기반 나이 계산기, 생활 기준표, 미니게임, RSS 블로그 자동화 웹 애플리케이션입니다.

## 서비스 링크
- Production: [https://agecalc.cloud](https://agecalc.cloud)
- Health check: [https://agecalc.cloud/health](https://agecalc.cloud/health)
- Sitemap: [https://agecalc.cloud/sitemap.xml](https://agecalc.cloud/sitemap.xml)

## 문서 안내
- 배포/운영: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
- 블로그 DB 스키마: [BLOG_POSTS_SCHEMA.md](BLOG_POSTS_SCHEMA.md)
- 아키텍처/흐름도: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 블로그 자동화/검수 기준: [docs/BLOG_WORKFLOW.md](docs/BLOG_WORKFLOW.md)
- Mermaid 원본: [docs/diagrams](docs/diagrams)

## 현재 주요 기능
- 만나이 계산: 양력/음력 생일, 기준일, 다음 생일까지 남은 기간
- 생활형 나이 표: 출생년도별 나이표, 학년 계산, 입학 연도, 나이 차이, 100일, 생일 D-Day
- 아이/가족 계산: 아이 개월 수, 부모·자녀 나이 관계
- 반려동물 계산: 강아지/고양이 나이, 반려동물 개월 수
- 기준/안내 페이지: 운영 원칙, 계산 기준, 문의, 개인정보처리방침, 이용약관, FAQ
- 미니게임: 숫자 맞추기, 스네이크, 틱택토, 가위바위보, 님, 퐁, 행맨, 메모리 매치, 커넥트4, 라이츠아웃, 지뢰찾기, 사이먼, 2048, 블랙잭, 브레이크아웃, 하노이, 피그, 오목, 리버시, 도트 앤 박스, 만칼라, 마스터마인드, 전쟁, 배틀십, 체커, 15퍼즐, 페그 솔리테어, 야추
- 블로그 자동화: RSS 수집, OpenAI 재창작, 커버 이미지 생성, 초안 검수, 수동 공개

## 전체 흐름
```mermaid
flowchart LR
    User[사용자] --> Nginx[Nginx]
    Nginx --> Gunicorn[Gunicorn]
    Gunicorn --> Flask[Flask app.py]
    Flask --> Pages[계산기/안내/미니게임]
    Flask --> Blog[블로그 공개/초안/검토]
    Flask --> MySQL[(MySQL)]
    Timer[systemd timer] --> Scheduler[RSS scheduler]
    Scheduler --> RSS[RSS sources]
    Scheduler --> OpenAI[OpenAI text/image]
    Scheduler --> MySQL
```

## 주요 라우트
### 공개 페이지
- `/`: 메인 허브
- `/age`: 만나이 계산기
- `/birth-year-age-table`: 출생년도별 나이표
- `/school-grade-calculator`: 학년 계산기
- `/school-entry-year-table`: 초등학교 입학 연도표
- `/age-gap-calculator`: 나이 차이 계산기
- `/100-day-calculator`: 100일 계산기
- `/baby-months-table`: 아이 개월 수 표
- `/annual-age-calculator`: 연도별 나이 계산기
- `/age-comparison-table`: 나이 비교표
- `/grade-age-table`: 학년별 나이표
- `/pet-age-table`: 반려동물 나이표
- `/korean-age-guide`: 한국나이 기준 안내
- `/pet-months-table`: 반려동물 개월 수 표
- `/grade-birth-year-table`: 학년별 출생년도표
- `/birth-year-zodiac-table`: 출생년도별 띠 표
- `/college-entry-year-calculator`: 대학 입학 연도 계산기
- `/birthday-dday-calculator`: 생일 D-Day 계산기
- `/dog`, `/cat`, `/baby-months`, `/d-day`, `/parent-child`
- `/about`, `/contact`, `/references`, `/privacy`, `/terms`, `/guide`, `/faq`
- `/sitemap.xml`, `/health`

### 블로그
- `/blog`: 공개 글 목록. 공개 글이 `BLOG_INDEX_MIN_POSTS` 기본값 3개 미만이면 `noindex, nofollow` 처리됩니다.
- `/blog/<slug>`: `published` 글 상세
- `/blog/drafts`: 비밀번호 기반 초안/검토 목록
- `/blog/drafts/<slug>`: 초안/검토 상세
- `/blog/drafts/<slug>/publish`: `draft` 글 공개. 2,500자 이상, 대표 이미지, 출처, 내부 링크 등 검수 통과가 필요합니다.
- `/blog/review/<id>`: 토큰 기반 검토 상세
- `/blog/review/<id>/approve`: 토큰 기반 공개 승인

### 미니게임
- `/minigames` 및 `/minigames/<game>` 형태의 게임 페이지
- 미니게임은 현재 애드센스 승인 안정성을 위해 sitemap에서 제외되고 `noindex` 대상으로 관리됩니다.

## 기술 스택
- Backend: Flask, Gunicorn
- DB/ORM: SQLAlchemy 2.x, PyMySQL, MySQL 운영 / SQLite 로컬 fallback
- Frontend: Jinja2, HTML, CSS, JavaScript
- Automation: systemd timer, RSS/Atom parser, OpenAI Responses API, OpenAI Images API
- Infra: Ubuntu, Nginx, Let's Encrypt

## 프로젝트 구조
```text
agecalc/
├── app.py
├── db.py
├── controllers/
├── models/
│   ├── age_calculator.py
│   └── blog_models.py
├── scripts/
│   ├── rss_blog_scheduler.py
│   ├── rewrite_blog_posts.py
│   └── adsense_blog_review.py
├── templates/
├── static/
├── systemd/
├── nginx/
├── docs/
├── tests/
├── requirements.txt
├── environment.yml
├── readme.md
├── BLOG_POSTS_SCHEMA.md
└── DEPLOYMENT_GUIDE.md
```

## 로컬 실행
### Python 환경 준비
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

운영 서버의 micromamba 환경을 직접 사용할 때:
```bash
source /srv/apps/agecalc/.micromamba/etc/profile.d/micromamba.sh
micromamba activate agecalc
python --version
```

활성화 없이 실행:
```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python --version
```

### DB 설정
`DATABASE_URL`이 없으면 SQLite `data/app.db`를 사용합니다. 운영에서는 MySQL을 사용합니다.

```bash
export DATABASE_URL='mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/agecalc?charset=utf8mb4'
```

### 앱 실행
```bash
python app.py
```

기본 포트는 `8000`입니다.

## RSS 블로그 자동화
스크립트는 프로젝트 루트의 `.env.rss`를 자동으로 읽습니다.

```bash
python scripts/rss_blog_scheduler.py import-sources --file scripts/rss_sources.example.json
python scripts/rss_blog_scheduler.py list-sources
python scripts/rss_blog_scheduler.py run --limit 1 --status draft --provider openai --model gpt-4.1-mini
```

운영 서버에서 직접 실행:
```bash
sudo -iu agecalc
cd /srv/apps/agecalc
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/rss_blog_scheduler.py run --limit 1 --status draft --provider openai --model gpt-4.1-mini
```

현재 블로그 공개용 기준:
- 생성 목표: HTML 제외 한글 기준 `2,700자 이상`
- 최소 본문 길이: HTML 제외 `2,500자`
- 최소 소제목: `h2`/`h3` 5개
- 필수 요소: 실제 원문 URL, AgeCalc 내부 계산기 링크, 대표 이미지
- 실패 시: `draft`가 아니라 `needs_review`로 보관

기존 글의 누락된 커버 이미지 보정:
```bash
python scripts/rss_blog_scheduler.py backfill-covers --status draft --limit 2
```

기존 `needs_review` 글 재작성:
```bash
python scripts/rewrite_blog_posts.py --limit 5 --apply --model gpt-4.1-mini
```

기존 전체 글을 보강하고 검수 통과 글을 자동 공개:
```bash
python scripts/rewrite_blog_posts.py --status all --all --attempts 2 --apply --publish-on-pass --demote-failed-published --model gpt-4.1-mini
```

## 운영 메모
- 앱과 스케줄러는 `/srv/apps/agecalc/.env.rss`를 공유합니다.
- 민감 정보는 저장소에 커밋하지 않고 `.env.rss` 또는 systemd 환경 파일에서 관리합니다.
- `agecalc-rss.timer`는 현재 production 기준 매일 `09:00`, `12:00`, `19:00` KST에 실행되며 실행당 초안 1개 생성을 시도합니다.
- 앱 코드 변경 후 production 반영은 `ubuntu` 계정에서 `sudo systemctl restart agecalc.service`를 실행합니다.
