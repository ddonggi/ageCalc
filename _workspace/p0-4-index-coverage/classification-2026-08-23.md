# Google 색인 제외·404 분류 — 2026-08-23

Search Console에서 2026-08-23에 내보낸 6개 상세 URL CSV를 현재 저장소 정책 및 운영 응답과 대조했습니다. 원본 CSV는 `_data/`에 보존하고 Git에는 포함하지 않습니다.

## 요약

| Search Console 사유 | URL 수 | 의도 | 관찰 | 수정 |
|---|---:|---:|---:|---:|
| noindex 제외 | 79 | 74 | 5 | 0 |
| 리디렉션이 포함된 페이지 | 5 | 5 | 0 | 0 |
| 크롤링됨-현재 미색인 | 5 | 2 | 3 | 0 |
| 발견됨-현재 미색인 | 4 | 0 | 4 | 0 |
| 찾을 수 없음(404) | 92 | 91 | 1 | 0 |
| 적절한 canonical이 있는 대체 페이지 | 8 | 8 | 0 | 0 |
| 합계 | 193 | 180 | 13 | 0 |

현재 코드나 라우팅을 즉시 수정해야 하는 URL은 확인되지 않았습니다. 이전 집계의 `noindex 66`, `404 91`, `대체 canonical 21`과 이번 상세 CSV 수는 Search Console 갱신 시점 차이로 달라졌으며, 이번 분류는 실제 내보내기 193행을 기준으로 합니다.

## 의도된 제외

- 결과형 쿼리 18개: 기본 canonical 및 `noindex,follow` 정책 또는 대체 canonical 정책과 일치합니다.
- 리디렉션 5개: `http→https`, `www→비-www`, 구형 `/annual-age-calculator?year&month&day`→기본 URL 이동으로 모두 의도된 정규화입니다.
- 미니게임 28개: 전체 미니게임 `noindex,nofollow` 정책과 일치합니다.
- `/guides/pet-age-table-guide`: 대표 `/pet-age-table`로 canonical 병합된 가이드입니다.
- 블로그 카테고리 1개: 공개 글 수 기준 미달일 때 적용되는 `noindex,follow`와 일치합니다.
- 과거 자동 생성 블로그: noindex 목록 32개, 404 목록 87개, 크롤링됨-미색인 1개는 현재 공개 콘텐츠 청사진에서 제외된 글입니다.
- 과거 도구 `/corrected-age`, `/siblings`의 비-www·www 4개는 현재 404이며 내부 링크와 사이트맵 대상이 아닙니다.
- `/rss.xml`은 피드 문서이므로 일반 HTML 검색 결과 색인을 요구하지 않습니다.

## 관찰 대상 13개

### 현재 정상 신호이며 재처리 대기

- `/age/`, `/health/`: 현재 각각 전용 허브로 301 이동합니다. 과거 noindex 상태가 보고서에서 사라지는지만 확인합니다.
- `/family/`, `/pets/`: 현재 200, self-canonical이며 noindex가 없습니다.
- `www`의 `/d-day`, `/baby-months`, `/terms`: 현재 비-www URL로 301 이동합니다.
- `/age-tools/`, `/generations/`, `/guides/baby-months-calculation-guide`, `/guides/school-grade-birth-year-guide`: 현재 200, self-canonical, index 허용이며 각 하위 사이트맵에도 포함됩니다. 발견됨-미색인은 수정 없이 재크롤링을 관찰합니다.

### 발행 의도 확인 필요

- `/blog/2026-man-age-guide`: 현재 콘텐츠 청사진에는 있으나 운영 공개 조건을 충족하지 않아 404입니다.
- `/blog/early-birth-school-grade-guide`: 현재 콘텐츠 청사진에는 있으나 운영에서는 404이며 과거 noindex 기록이 남아 있습니다.

두 글은 자동 리디렉션하거나 다시 발행하지 않습니다. 운영자가 향후 발행할 대표 글인지, 폐기할 글인지 결정한 뒤 처리합니다. 폐기한다면 현재 404를 유지하고 관련 글 후보 링크가 공개 HTML에 노출되지 않는지만 계속 검사합니다.

## 후속 확인

1. Search Console에서 별도의 수정 검증 요청은 하지 않습니다. 현재 13개 관찰 URL은 다음 크롤링 결과를 기다립니다.
2. 2026-09-23 전후 같은 6개 보고서를 다시 내려받아 `관찰` URL이 의도된 사유로 이동했는지 비교합니다.
3. 공개 핵심 페이지가 새로 noindex·404 목록에 들어오거나, 301·canonical 도착지가 달라질 때만 코드 수정 대상으로 전환합니다.
4. 블로그 두 글의 발행 여부는 사이트 운영 결정이므로 P0-4 기술 수정과 분리합니다.

행별 판정은 `classification-2026-08-23.csv`에 기록했습니다.
