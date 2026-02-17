# AgeCalc

Flask 기반 나이 계산/미니게임/블로그 웹 애플리케이션입니다.

## 문서 안내
- 개발/로컬 실행: `readme.md`
- 배포/운영(AWS EC2, Nginx, MySQL): `DEPLOYMENT_GUIDE.md`

## 현재 주요 기능
- 만나이 계산(양력/음력)
- 강아지/고양이 나이 환산
- 아이 개월 수 계산
- 부모·자녀 나이 관계 계산
- 미니게임(스네이크, 틱택토)
- 블로그 목록/상세/페이징

## 라우트
- `/` 메인
- `/age` 만나이
- `/dog` 강아지 나이
- `/cat` 고양이 나이
- `/baby-months` 아이 개월 수
- `/parent-child` 부모·자녀
- `/blog` 블로그 목록
- `/blog/<slug>` 블로그 상세
- `/minigames` 미니게임 목록
- `/minigames/snake` 스네이크
- `/minigames/tictactoe` 틱택토
- `/health` 헬스체크

## 기술 스택
- Backend: Flask 2.3.3
- DB/ORM: SQLAlchemy 2.x, PyMySQL
- Frontend: Jinja2 템플릿, HTML/CSS/JS

## 프로젝트 구조
```text
ageCalc/
├── app.py
├── db.py
├── controllers/
├── models/
│   ├── age_calculator.py
│   └── blog_models.py
├── templates/
├── static/
├── requirements.txt
├── environment.yml
├── nginx/
│   └── agecalc.conf
├── readme.md
└── DEPLOYMENT_GUIDE.md
```

## 로컬 실행
### 1) Python 환경 준비
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) DB 설정
- 기본값: `DATABASE_URL` 미설정 시 SQLite(`data/app.db`) 사용
- MySQL 사용 시:
```bash
export DATABASE_URL='mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/agecalc?charset=utf8mb4'
```

### 3) 실행
```bash
python app.py
```
- 기본 실행 포트: `8000`
- 접속: `http://localhost:8000`

## 참고
- 블로그 테이블은 앱 시작 시 SQLAlchemy `create_all`로 자동 생성됩니다.
- 운영 배포에서는 `python app.py` 대신 `gunicorn` + `systemd` + `nginx` 구성을 사용하세요.
