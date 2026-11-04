# 개발 환경과 검증

[메인 README](../readme.md) · [문서 목차](README.md)

## 작업 위치와 사전 확인

`git status -sb`, `git worktree list`, `git branch -vv`로 경로·브랜치·기존 변경을 확인합니다. 개발은 확인된 pre-release 작업 트리에서 수행합니다. 원격 추적 정보는 마지막 fetch 시점의 정보이며 현재 원격 상태를 보장하지 않습니다.

## Python 환경

개발 작업 트리 루트에서 실행합니다.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

의존성 기준은 [requirements.txt](../requirements.txt)와 [environment.yml](../environment.yml)입니다. 기존 micromamba 환경을 사용할 때는 해당 경로의 실행 파일과 버전을 먼저 확인합니다. 운영용 절대 경로를 개발 기본값으로 사용하지 않습니다.

## DB와 환경 분리

[db.py](../db.py)는 import 시 DB 엔진을 만들고 [app.py](../app.py)는 시작 시 `init_db()`를 호출합니다. 환경변수는 **앱 또는 검증 스크립트를 import하기 전** 설정해야 합니다. 앱은 프로젝트의 `.env.rss`도 읽으므로 운영 파일을 개발 작업 트리에 복사하거나 source하지 않습니다.

다음은 운영 환경 파일이 없는 개발 작업 트리에서 사용하는 로컬 예시입니다.

```bash
export AGECALC_ENV=development
export DATABASE_URL='sqlite:///:memory:'
export BLOG_BASE_URL='http://127.0.0.1:8123'
export ADSENSE_REVIEW_MODE=true
export BLOG_PUBLIC_INDEXING_ENABLED=false
export COUPANG_PARTNERS_ENABLED=false
export ADSENSE_CLIENT_ID=''
```

메모리 DB는 프로세스 종료 시 사라집니다. 저장이 필요하면 개발 전용 SQLite 파일이나 별도 개발 DB를 명시합니다. `DATABASE_URL`을 생략하면 저장소의 `data/app.db`로 fallback하므로 격리 검증을 생략하지 않습니다.

## 실행

위 환경을 확인한 뒤 로컬 루프백으로 실행합니다.

```bash
python -m flask --app app run --host 127.0.0.1 --port 8123
```

포트 사용 여부는 먼저 확인합니다. `python app.py`는 현재 코드상 debug 모드로 `0.0.0.0:8000`에 바인딩하므로 운영 실행 방법으로 사용하지 않습니다. 개발용 HTTP에서는 secure 세션 쿠키 때문에 블로그 로그인 검증이 제한될 수 있습니다. 인증 검증에는 별도 HTTPS 개발 환경을 사용하고 운영 쿠키 정책을 낮추지 않습니다.

## 검증 진입점

DB 격리와 스크립트 부작용을 확인한 뒤 변경 범위에 맞춰 선택합니다.

```bash
python -m unittest discover -s tests -v
node --test tests/global-calculations.test.js
python scripts/adsense_preflight.py
python scripts/content_quality_audit.py --format text
git diff --check
```

문서만 바꾼 경우 파일 경로·상대 링크·앵커·요구사항·diff를 확인하며 앱과 DB를 실행하지 않습니다. Python/JavaScript 테스트 통과를 실제 서버·광고·검색 색인 검증 결과로 대신하지 않습니다.

## 운영 작업

실제 서비스 계정, 작업 경로, DB, 실행 파일을 확인하는 절차는 [배포 가이드](../DEPLOYMENT_GUIDE.md)에 있습니다. 실행·생성·재작성·게시 스크립트는 각각 별도의 부작용과 권한 범위를 갖습니다.
