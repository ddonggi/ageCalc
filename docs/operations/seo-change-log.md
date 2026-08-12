# SEO 변경 기록

검색 메타데이터와 색인 정책을 바꿀 때 실제 변경일과 검증 결과를 기록합니다. `lastmod`는 본문·FAQ·계산 설명이 실제로 바뀐 페이지만 갱신합니다.

## 2026-08-13

### 공개 URL 정규화

| 유형 | 기존 URL | 대표 URL | 처리 |
|---|---|---|---|
| 만나이 계산기 | `/age` | `/age` | 기존 계산기 URL 유지 |
| 나이 도구 허브 | `/age/` | `/age-tools/` | 기존 URL에서 신규 허브로 301 |
| 상태 확인 API | `/health` | `/health` | 기존 API URL 유지 |
| 건강 도구 허브 | `/health/` | `/health-tools/` | 기존 URL에서 신규 허브로 301 |
| 슬래시 없는 공개 페이지 | `/about/` 등 | `/about` 등 registry canonical | GET·HEAD 요청을 301로 정규화하고 쿼리 문자열 유지 |
| 기존 trailing-slash 허브 | `/family` 등 | `/family/` 등 | Flask의 기존 308 유지 |

알 수 없는 trailing-slash URL과 `/llms.txt/`는 404를 유지합니다. 내부 메뉴·홈·breadcrumb·관련 도구와 비검토 모드 사이트맵은 신규 허브 canonical만 사용합니다. 본문·FAQ·계산 설명은 바뀌지 않아 registry `lastmod`는 갱신하지 않았습니다.

상태 확인 API `/health`는 기존 `200 application/json` 응답을 유지하면서 GET·HEAD 응답에 `X-Robots-Tag: noindex, nofollow`를 추가했습니다. 사용자용 건강 도구 허브 `/health-tools/`와 사이트맵 정책은 변경하지 않았습니다.

### 쿼리 URL 색인 범위 축소

실제 URL별 성과가 확인된 `/birth-year-age-table?year=2010`과 학번 2024·2025·2026만 self-canonical/index로 유지했습니다. 학년별 결과 URL과 그 외 유효 결과 URL은 기본 canonical과 `noindex,follow`로 통합했습니다. 학번 예시 콘텐츠는 색인 allowlist와 분리해 유지하며, 자세한 근거는 `docs/operations/seo-query-index-policy.md`에 기록했습니다. 본문과 계산 기준은 바뀌지 않아 sitemap `lastmod`는 갱신하지 않았습니다.

### 결과형 쿼리 정규화

결과형 GET URL 전반에 허용 키, 단일 값, 정규 정수 형식과 범위 검사를 적용했습니다. 완전한 유효 결과만 200으로 제공하고 P0-2 allowlist 외 결과에는 기본 canonical과 `X-Robots-Tag: noindex, follow`를 함께 적용합니다. 빈 값, 일부 입력, 중복·추가 키, 범위 밖 값과 모호한 표기는 기본 URL로 302 처리합니다. 계산 결과와 표의 산식은 변경하지 않았으며 sitemap `lastmod`도 유지했습니다.

### 구조화 데이터 정합성

공개 registry 59페이지와 self-canonical 결과 URL의 JSON-LD 문법, WebPage 단일성, canonical·Open Graph·breadcrumb URL 일치를 계약 테스트로 고정했습니다. 병합 예정 가이드는 대표 페이지 canonical에 구조화 데이터도 맞췄고, `/age`와 `/faq`의 FAQPage 답변은 화면에 실제 표시되는 문구와 동일하게 정리했습니다. 사용자에게 보이는 의미와 계산 콘텐츠는 바뀌지 않아 sitemap `lastmod`는 유지했습니다.

### 이미지 SEO·접근성

공개 페이지 공통 후원 QR에 실제 500×500 크기를 지정하고, 블로그 목록·카테고리·상세 대표 이미지는 1200×630으로 예약했습니다. 외부 프로모션은 확인한 실제 크기를 데이터로 관리하며, 장식용 제휴 배너는 빈 alt를 유지하는 대신 링크에 접근 가능한 이름을 추가했습니다. 일반 도구의 1200×630 브랜드 OG fallback과 블로그 고유 대표 이미지 정책은 유지했습니다. 본문 의미는 바뀌지 않아 sitemap `lastmod`는 갱신하지 않았습니다.

## 2026-08-11

| URL | 기존 title | 변경 title | H1·본문·FAQ | canonical / robots | lastmod |
|---|---|---|---|---|---|
| `/grade-birth-year-table` | 학년별 출생연도표 | 학년별 출생연도표 \| 중1·고1은 몇 년생? | 선택 학년 직답, 빠른년생·학적 예외 FAQ | 기본 URL index, 유효 학년 변형 self-canonical/index, 잘못된 값 302 | 변경 |
| `/grade-age-table` | 학년 기준 나이표 | 학년별 나이표 \| 중1·중3·고1·고3은 몇 살? | 선택 학년 나이 직답, 생일·학적 차이 FAQ | 기본 URL index, 유효 학년 변형 self-canonical/index, 잘못된 값 302 | 변경 |
| `/school-grade-calculator` | 학년 계산기 \| 출생년도별 현재 학년 확인 | 학년 계산기 \| 출생연도별 현재 학년 확인 | 현재 학년과 학년도 기준 설명 유지·보강 | 유효 연도 200/noindex + 기본 canonical, 잘못된 값 302 | 변경 |
| `/school-entry-year-table` | 입학년도 계산기 \| 초중고 입학년도 계산표 | 입학년도 계산기 \| 출생연도별 초·중·고 입학년도 | 현재 학년과 다른 입학 시점 의도 명시 | 유효 연도 200/noindex + 기본 canonical, 잘못된 값 302 | 변경 |
| `/birth-year-age-table` | 몇년생 몇살? 출생년도별 나이표 | 몇년생 몇살? 출생연도별 만나이·연나이 표 | 생일 정보가 없을 때의 만나이 범위와 FAQ 보강 | `year=2010` self-canonical/index, 다른 유효 연도 noindex, 잘못된 값 302 | 변경 |
| `/age` | 만나이 계산기 - 양력/음력 생일 완벽 지원 | 만나이 계산기 \| 생년월일·음력 생일로 현재 나이 계산 | 기존 visible FAQ·FAQPage 유지, 양력·음력 설명 강화 | 기본 URL index/canonical 유지 | 변경 |
| `/annual-age-calculator` | 연나이 계산기 | 연나이 계산기 \| 출생연도만으로 올해 연나이 확인 | 출생연도만 쓰는 공식과 만나이 차이 FAQ | 기본 URL index/canonical 유지 | 변경 |
| `/100-day-calculator` | 100일 계산기 | 100일 계산기 \| 시작일 포함 100일째·기념일 날짜 계산 | 시작일 포함, 월말·윤년, 아기·커플 FAQ | 쿼리 입력은 기본 URL로 302, 기본 URL index | 변경 |
| `/college-entry-year-calculator` | 26학번 몇년생? 26학번 나이·대학교 학번 계산기 | 학번 계산기 \| 몇 학번·학번 나이·몇년생 확인 | 허용 학번별 동적 H1·직답, 재수·편입 예외 설명 유지 | 2020·2022·2024~2026 self-canonical/index, 다른 유효 연도 noindex, 잘못된 값 302 | 변경 |

사이트맵에는 기본 URL만 유지합니다. 네이버 연관검색어는 제공된 실제 목록이 생기기 전까지 자동 생성하거나 삽입하지 않으며, `content/editorial_metadata.py`의 페이지별 `primary`, `section`, `faq` 슬롯만 비워 둡니다.

색인 허용 쿼리 URL의 발견 경로도 보강했습니다. 학년별 나이표와 학년별 출생연도표의 각 학년을 표준 `<a href>` 링크로 연결하고, 학번 계산기의 색인 허용 학번(2026·2025·2024·2022·2020)을 대표 예시에서 연결합니다. 쿼리 URL은 사이트맵에 추가하지 않으며 기존 self-canonical, `index,follow`, `noindex,follow` 정책을 유지합니다.
