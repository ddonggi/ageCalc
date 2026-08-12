# 쿼리 URL 색인 정책

확인일: 2026-08-13

사이트맵에는 기본 canonical URL만 등록합니다. 사용자가 선택한 계산 결과는 기능상 접근할 수 있지만, URL별 검색 수요와 고유 콘텐츠가 함께 확인된 변형만 self-canonical 및 index 대상으로 둡니다.

| URL 유형 | 정책 | 근거 |
|---|---|---|
| 기본 도구 URL | self-canonical, index | 각 도구의 대표 검색 의도와 전체 표·설명 제공 |
| `/birth-year-age-table?year=2010` | self-canonical, index | 네이버 클릭 2,485, 노출 163,005, CTR 1.5% |
| 그 외 유효한 출생연도 | 기본 canonical, `noindex,follow` | 선택 결과만 달라지고 URL별 수요 근거 미확인 |
| 학년표의 유효 `stage+grade` | 기본 canonical, `noindex,follow` | 네이버에서 확인된 URL이 빈 `grade`였으며 유효 학년별 URL 성과는 미확인 |
| 학번 `year=2024`, `2025`, `2026` | self-canonical, index | 네이버에서 각 URL의 클릭·노출 확인 |
| 그 외 유효한 학번 연도 | 기본 canonical, `noindex,follow` | 검색어 수요는 일부 확인됐지만 URL별 성과와 고유 콘텐츠 근거가 부족 |

빈 값, 중복·추가 파라미터, 범위 밖 값과 `2024~2026` 같은 모호한 값은 별도 문서가 되지 않도록 기본 URL로 정규화합니다. 학번 예시 콘텐츠는 색인 allowlist와 분리해 유지합니다. 이 변경은 본문·FAQ·계산 기준을 바꾸지 않으므로 sitemap `lastmod`를 갱신하지 않습니다.
