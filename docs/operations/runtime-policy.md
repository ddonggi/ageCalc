# 공개 및 운영 정책

[문서 목차](../README.md) · [배포 가이드](../../DEPLOYMENT_GUIDE.md)

2026-11-04에 `f11630e`의 코드와 저장소 문서를 기준으로 정리했습니다. 아래는 설정 간 관계이며 현재 서버 환경값을 측정한 기록이 아닙니다.

## 광고·색인·제휴

| 설정 또는 조건 | 동작 |
| --- | --- |
| `ADSENSE_REVIEW_MODE=true` | 승인 검토 구성. 블로그와 해당 라이프 허브의 공개 색인·탐색을 제한하며 제휴를 차단 |
| `BLOG_PUBLIC_INDEXING_ENABLED=true` | 블로그 공개 색인을 허용하는 조건 중 하나. 승인 모드 해제와 최소 공개 글 수 조건도 필요 |
| `BLOG_INDEX_MIN_POSTS` | 블로그 공개 색인에 필요한 공개 글 수. 코드 기본값은 3이며 개수만으로 판정하지 않음 |
| `COUPANG_PARTNERS_ENABLED=true` | 승인 모드가 해제돼야 제휴 노출 가능 |
| `ADSENSE_CLIENT_ID` | 광고 로더 설정. 값이 있어도 페이지별 광고 제외 정책 적용 |

공개 URL과 광고 허용은 같은 조건이 아닙니다. [app.py](../../app.py)의 `_adsense_is_enabled_for_path()`는 공휴일 달력, 개인정보 보호 도구, 초안·검토 경로 등에 별도 제외 규칙을 적용합니다. AdSense 승인 여부와 코드의 review 플래그도 구분합니다.

## 사이트맵과 결과 URL

[page_registry.py](../../content/page_registry.py)와 [i18n.py](../../content/i18n.py)의 등록·공개 조건에 따라 동적으로 생성합니다. URL 수를 고정된 운영 기준으로 복사하지 않습니다. 쿼리 결과의 canonical·noindex·허용 목록은 [쿼리 URL 정책](seo-query-index-policy.md), 변경 이력은 [SEO 변경 기록](seo-change-log.md)을 따릅니다.

## 환경 파일과 RSS

앱과 스케줄러는 프로젝트의 `.env.rss`를 읽습니다. 비밀값은 Git·문서·로그에 남기지 않습니다. DB 설정은 모듈 import 전에 확정해야 하므로 개발 환경은 [개발 안내](../DEVELOPMENT.md)를 따릅니다.

저장소 [RSS timer](../../systemd/agecalc-rss.timer)는 09:00·12:00·19:00 OnCalendar를 정의합니다. 타임존을 명시하지 않은 systemd 시간은 서버 시간대의 영향을 받습니다. 실제 운영 시간대·timer 활성화 여부·실행당 생성 수는 설치된 timer/service를 확인합니다.

RSS 명령·품질 기준은 [블로그 워크플로](../BLOG_WORKFLOW.md), 서비스 설치·재시작은 [배포 가이드](../../DEPLOYMENT_GUIDE.md)에 둡니다.

## 과거 기록

[AdSense 기준선](adsense-baseline-2026-06.md)은 승인 전후의 날짜별 이력입니다. 당시 수치·서비스 상태·검증 통과 수를 현재 운영 상태로 재사용하지 않습니다.
