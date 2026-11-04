# AgeCalc

Flask 기반 나이·날짜 계산기, 생활 기준표, 다국어 도구와 RSS 블로그 자동화 웹 애플리케이션입니다.

[서비스](https://agecalc.cloud) · [상태 확인](https://agecalc.cloud/health) · [사이트맵](https://agecalc.cloud/sitemap.xml)

## 주요 기능

- 만나이·연나이·출생연도별 나이, 학년·입학연도·학번 계산
- 아기 개월수, 부모·자녀 나이 관계, 고양이·강아지 나이 계산
- 100일·기념일·생일 D-day, 날짜 차이·날짜 이동·음력 생일 계산
- 다국어 계산기와 지역별 날짜 기준 안내
- RSS 기반 블로그 초안 생성, 품질 검수와 공개 관리

## 문서 안내

| 필요한 작업 | 문서 |
| --- | --- |
| 전체 문서 찾기·현재 지침과 과거 기록 구분 | [문서 목차](docs/README.md) |
| 개발 환경·DB 격리·실행·검증 | [개발 안내](docs/DEVELOPMENT.md) |
| 구성 요소·요청 흐름·프로젝트 구조 | [아키텍처](docs/ARCHITECTURE.md) |
| 계산기·블로그·이전 URL 확인 | [주요 라우트](docs/ROUTES.md) |
| 담당자·승인·작업 트리·보고 규칙 | [팀 운영 규칙](docs/TEAM_RULES.md) |
| 작업을 맡기는 시작 프롬프트 | [팀 운영 시작 프롬프트](docs/TEAM_OPERATIONS.md) |
| 서버 설치·배포·복구 점검 | [배포 가이드](DEPLOYMENT_GUIDE.md) |
| 광고·블로그 색인·제휴 플래그 | [공개 및 운영 정책](docs/operations/runtime-policy.md) |
| RSS 생성·검수·재작성·게시 | [블로그 워크플로](docs/BLOG_WORKFLOW.md) |
| 블로그 테이블·모델 | [DB 스키마](BLOG_POSTS_SCHEMA.md) |
| canonical·쿼리 URL 정책 | [SEO 색인 정책](docs/operations/seo-query-index-policy.md) |

## 시작하기

1. [팀 운영 규칙](docs/TEAM_RULES.md)과 해당 작업의 사용자 승인 범위를 확인합니다.
2. [개발 안내](docs/DEVELOPMENT.md)에 따라 작업 트리와 독립된 개발 DB를 준비합니다.
3. 변경할 영역의 문서를 [목차](docs/README.md)에서 찾고 해당 검증을 선택합니다.

## 팀 운영 규칙

상세 규칙은 [팀 운영 규칙](docs/TEAM_RULES.md)에 모았습니다. 기존 문서의 `readme.md#팀-운영-규칙` 링크를 위해 이 제목을 유지합니다.

기존 작업 보존, 확인된 pre-release에서 개발, 운영 DB와 개발 DB 분리, Phase별 명시적 승인 및 승인 후 배포 원칙을 따릅니다. 이 README나 과거 배포 기록만으로 현재 운영 설정을 단정하지 않습니다.

## 기술 스택

Flask·Gunicorn / SQLAlchemy·MySQL / Jinja2·HTML·CSS·JavaScript / Nginx·systemd.
로컬 DB fallback은 SQLite이며 실행 전에 개발 DB를 명시적으로 설정합니다.

문서 추가·수정 기준은 [문서 관리 원칙](docs/README.md#문서-관리-원칙)을 참고하세요.
