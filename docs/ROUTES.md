# 주요 라우트
## 공개 페이지
- `/`: 메인 허브
- `/age`: 만나이 계산기
- `/birth-year-age-table`: 출생년도별 나이표
- `/school-grade-calculator`: 학년 계산기
- `/school-entry-year-table`: 통합 학년 계산기로 이동하는 영구 리디렉션
- `/age-gap-calculator`: 나이 차이 계산기
- `/100-day-calculator`: 100일 계산기
- `/baby-months-table`: 아이 개월 수 표
- `/annual-age-calculator`: 연도별 나이 계산기
- `/age-comparison-table`: 나이 비교표
- `/grade-age-table`: 학년별 출생년도표로 이동하는 영구 리디렉션
- `/pet-age-table`: 반려동물 나이표
- `/korean-age-guide`: 한국나이 기준 안내
- `/pet-months-table`: 반려동물 개월 수 표
- `/grade-birth-year-table`: 학년별 출생년도표
- `/birth-year-zodiac-table`: 출생년도별 띠 표
- `/college-entry-year-calculator`: 대학 입학 연도 계산기
- `/birthday-dday-calculator`: 생일 D-Day 계산기
- `/dog`, `/cat`, `/baby-months`, `/d-day`, `/parent-child`
- `/days-between-dates`, `/date-add-subtract-calculator`, `/lunar-birthday-calculator`
- `/en`, `/ja`, `/es`, `/pt-br`, `/zh-cn` 접두사의 지원 계산기와 지역별 전용 계산기
- `/about`, `/contact`, `/references`, `/privacy`, `/terms`, `/guide`, `/faq`
- `/sitemap.xml`, `/health`

## 블로그
- `/blog`: 공개 글 목록. `ADSENSE_REVIEW_MODE=true`이면 게시물 수와 관계없이 `noindex, nofollow` 처리되고 sitemap과 메뉴에서 제외됩니다.
- `/blog/<slug>`: `published` 글 상세
- `/blog/drafts`: 비밀번호 기반 초안/검토 목록
- `/blog/drafts/<slug>`: 초안/검토 상세
- `/blog/drafts/<slug>/publish`: `draft` 글 공개. 2,500자 이상, 대표 이미지, 출처, 내부 링크 등 검수 통과가 필요합니다.
- `/blog/review/<id>`: 토큰 기반 검토 상세
- `/blog/review/<id>/approve`: 토큰 기반 공개 승인

## 종료된 미니게임
- 이전 `/minigames/` 경로는 현재 공개되지 않으며 404를 반환합니다.
- 공개 탐색과 sitemap에도 미니게임 링크를 포함하지 않습니다.


## 문서 범위와 근거

이 목록은 주요 경로 안내이며 전체 URL 목록이나 현재 서버의 색인 결과가 아닙니다. 최신 라우트는 [app.py](../app.py), 공개 대상은 [page registry](../content/page_registry.py), 다국어는 [i18n 안내](operations/i18n.md)를 확인합니다. 블로그 노출에는 [공개 정책](operations/runtime-policy.md)의 추가 조건이 적용됩니다.

[메인 README](../readme.md) · [문서 목차](README.md)
