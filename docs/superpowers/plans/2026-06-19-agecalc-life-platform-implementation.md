# AgeCalc Life Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 현재 AgeCalc를 AdSense 승인 가능성이 높은 나이 기반 라이프 플랫폼으로 전환하고, 3개월 안에 기존 콘텐츠 품질 개선·8개 허브·15개 고수요 기능·최소 AI 기능을 안전하게 출시한다.

**Architecture:** 기존 Flask/Jinja 단일 앱과 URL은 유지하면서 페이지 메타데이터, 허브 구성, 계산 로직, 공식 기준 데이터를 별도 모듈로 분리한다. 모든 신규 URL은 중앙 페이지 레지스트리의 `indexable`과 `release_batch` 값으로 sitemap·내부링크·광고 노출을 통제하며, 날짜 계산은 결정적 Python 함수가 담당하고 AI는 검증된 결과의 설명만 담당한다.

**Tech Stack:** Python 3, Flask 2.3, Jinja2, vanilla JavaScript/CSS, SQLAlchemy, MySQL/SQLite fallback, unittest, OpenAI Responses API, Google Search Console 수동 운영

---

## 1. 실행 범위와 작업 트랙

이 계획은 독립 배포 가능한 6개 트랙으로 나눈다.

| 트랙 | 범위 | 선행 조건 | 완료 시 독립 배포 |
|---|---|---|---|
| A | AdSense 승인 기반 정리 | 없음 | 가능 |
| B | 공통 SEO·IA 인프라 | A1~A3 | 가능 |
| C | 기존 핵심 20개 URL 심층화 | B1~B5 | 가능 |
| D | 신규 고수요 기능 15개 | B1~B6 | 3개 배치로 가능 |
| E | AI 최소 기능 3개 | D1 또는 기존 계산 결과 | 가능 |
| F | 4~6개월 성장 기능 | C·D 성과 데이터 | 기능별 가능 |

### 작업 상태 정의

- `P0`: AdSense 재심사 전에 완료
- `P1`: 재심사 전후 3개월 내 완료
- `P2`: Search Console 성과 확인 후 4~6개월에 실행
- 각 Task는 테스트 통과와 커밋까지 하나의 완료 단위다.
- 운영 배포, 서비스 재시작, Search Console 제출, AdSense 재심사는 별도 승인 후 수행한다.

## 2. 파일 구조 결정

### 유지하는 기존 핵심 파일

| 파일 | 역할 |
|---|---|
| `app.py` | Flask 앱 초기화, 기존 라우트, 공통 context processor |
| `content/guide_pages.py` | 기존 정적 가이드 콘텐츠 |
| `templates/partials/header.html` | 전역 탐색 |
| `templates/partials/footer.html` | 신뢰·정책 링크 |
| `static/css/style.css` | 공통 UI |
| `tests/test_public_pages.py` | 공개 페이지·sitemap·광고 회귀 테스트 |
| `scripts/adsense_preflight.py` | 승인 전 정적 검사 |

### 새로 만드는 모듈

| 파일 | 책임 |
|---|---|
| `content/page_registry.py` | 모든 공개 페이지의 slug, endpoint, hub, title, indexable, release batch, 관련 링크 |
| `content/hub_pages.py` | 8개 허브의 소개·대표 링크·질문·출처 |
| `content/editorial_metadata.py` | 작성자·검수자·기준일·출처·면책 데이터 |
| `content/official_sources.py` | YMYL 페이지 공식 출처와 확인일 |
| `services/date_calculators.py` | 살아온 일수, 생일, 기념일, 출산·월령 날짜 계산 |
| `services/education_calculators.py` | 학년·입학·졸업 계산 |
| `services/retirement_calculators.py` | 연금 수령 연령·정년 날짜 계산 |
| `services/health_calculators.py` | 건강검진·영유아 검진 대상 계산 |
| `services/life_timeline.py` | 검증된 계산 결과를 생애 타임라인 이벤트로 조합 |
| `services/ai_explanations.py` | OpenAI 호출, 구조화 출력, moderation, 실패 처리 |
| `templates/hub-detail.html` | 8개 허브 공통 템플릿 |
| `templates/partials/breadcrumbs.html` | 화면·JSON-LD Breadcrumb |
| `templates/partials/editorial-meta.html` | 작성·검수·수정·출처 표시 |
| `templates/partials/related-paths.html` | 계산 전·결과 기반·인접 도구 링크 |
| `templates/partials/calculator-shell.html` | 신규 계산기 공통 콘텐츠 순서 |
| `tests/test_page_registry.py` | 레지스트리 무결성 |
| `tests/test_date_calculators.py` | 일반 날짜 계산 |
| `tests/test_education_calculators.py` | 교육 계산 |
| `tests/test_retirement_calculators.py` | 연금·정년 계산 |
| `tests/test_health_calculators.py` | 건강검진 계산 |
| `tests/test_life_timeline.py` | 타임라인 구성 |
| `tests/test_ai_explanations.py` | AI 구조화 출력·실패 처리 |
| `scripts/content_quality_audit.py` | 색인 페이지 품질 게이트 검사 |
| `scripts/gsc_weekly_review.py` | GSC CSV를 허브·상태별로 집계 |

### 신규 템플릿 파일

기능별 템플릿은 공통 partial을 사용하되 검색 의도별 고유 본문을 유지한다.

```text
templates/calculators/
├── days-lived.html
├── next-birthday.html
├── birth-year-from-age.html
├── due-date.html
├── pregnancy-weeks.html
├── baby-days.html
├── first-birthday.html
├── graduation-year.html
├── couple-anniversary.html
├── milestone-birthday.html
├── pension-age.html
├── retirement-date.html
├── health-checkup-year.html
├── infant-checkup.html
└── life-timeline.html
```

## 3. 의존성 순서

```text
A1 → A2 → A3
          ↓
 B1 → B2 → B3 → B4 → B5 → B6
                    ↓
 C1 → C2 → C3 → C4 → C5
                    ↓
 D1 → D2 → D3 → D4
              ↓
             E1 → E2 → E3

C5 + D4 + 4주 GSC 데이터 → F1 → F2 → F3 → F4
```

---

## 트랙 A. AdSense 승인 기반 정리

### Task A1 [P0]: 기준선과 보호 테스트 고정

**Files**

- Modify: `tests/test_public_pages.py`
- Modify: `tests/test_adsense_preflight.py`
- Create: `docs/operations/adsense-baseline-2026-06.md`

- [ ] 현재 sitemap URL 수, index/noindex 경로, 블로그·미니게임 상태를 기준선 문서에 기록한다.
- [ ] 공통 쿠팡 레일이 비활성일 때 모든 핵심 페이지에서 렌더링되지 않는 테스트를 추가한다.
- [ ] sitemap URL이 200, canonical, index 가능 상태인지 검사하는 현재 테스트를 기준선으로 고정한다.
- [ ] 다음 명령으로 변경 전 전체 테스트를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests -v
```

**Expected:** 모든 기존 테스트 PASS.

- [ ] 승인 프리플라이트를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/adsense_preflight.py --format text
```

**Expected:** `PASS checked_pages=50 sitemap_urls=50`.

- [ ] 기준선 문서와 테스트만 커밋한다.

```bash
git add tests/test_public_pages.py tests/test_adsense_preflight.py docs/operations/adsense-baseline-2026-06.md
git commit -m "test: record adsense approval baseline"
```

**완료 조건:** 후속 변경으로 index·광고 상태가 의도치 않게 바뀌면 테스트가 실패한다.

### Task A2 [P0]: 전역 쿠팡 레일 제거와 제휴 노출 정책 적용

**Files**

- Modify: `app.py`
- Modify: `templates/partials/header.html`
- Modify: `static/css/style.css`
- Modify: `tests/test_public_pages.py`
- Retain unused until cleanup decision: `templates/partials/coupang_carousel.html`

- [ ] `coupang_carousel_enabled` context 값을 제거하거나 항상 `False`로 설정하는 실패 테스트를 먼저 작성한다.
- [ ] 헤더에서 `partials/coupang_carousel.html` include를 제거한다.
- [ ] `.coupang-ad-aside`, `.coupang-ad-rail`, 모바일 재배치 규칙이 다른 레이아웃에 영향을 주지 않는지 확인한 뒤 전역 레일 전용 CSS를 제거한다.
- [ ] 페이지별 제휴 partial은 기본 비활성 상태를 유지하고, 블로그 상세 외 공개 페이지에 자동 삽입되지 않는 테스트를 유지한다.
- [ ] 관련 테스트를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_coupang_ad_aside_hides_when_disabled \
  tests.test_public_pages.PublicPageTests.test_coupang_page_sections_no_longer_render_affiliate_blocks -v
```

**Expected:** PASS.

- [ ] 전체 공개 페이지 테스트를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_public_pages -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add app.py templates/partials/header.html static/css/style.css tests/test_public_pages.py
git commit -m "fix: remove global affiliate rail from public pages"
```

**완료 조건:** 모바일·데스크톱 첫 화면에서 전역 쿠팡 레일이 렌더링되지 않고 광고 승인 스크립트는 유지된다.

### Task A3 [P0]: 현재 50개 URL 감사 레지스트리 작성

**Files**

- Create: `content/page_registry.py`
- Create: `tests/test_page_registry.py`
- Create: `docs/content/page-audit-2026-06.csv`
- Modify: `app.py`

- [ ] 현재 `PUBLIC_SITEMAP_ENDPOINTS`, `GUIDE_PAGES`, 기존 페이지를 레지스트리 항목으로 옮기는 테스트를 작성한다.
- [ ] 각 항목에 다음 필드를 필수로 정의한다.

```python
{
    "endpoint": "age",
    "path": "/age",
    "hub": "age",
    "search_intent": "생년월일 기준 현재 만나이 계산",
    "content_action": "strengthen",
    "indexable": True,
    "release_batch": "existing",
    "priority": "core",
    "related_endpoints": (
        "birth_year_age_table",
        "annual_age_calculator",
        "birthday_dday_calculator",
    ),
}
```

- [ ] `content_action`은 `keep`, `strengthen`, `merge`, `noindex` 네 값만 허용한다.
- [ ] endpoint, path, search intent 중복을 검사하는 테스트를 작성한다.
- [ ] CSV에 50개 공개 URL의 현재 상태, 처리 결정, 고유 정보 요소, 출처 필요 여부를 기록한다.
- [ ] `app.py`의 sitemap 생성이 레지스트리의 `indexable=True` 항목을 읽도록 바꾸기 전, 기존 50개 URL과 동일한 결과를 반환하는 테스트를 작성한다.
- [ ] 레지스트리 전환 후 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_page_registry \
  tests.test_public_pages.PublicPageTests.test_dynamic_sitemap_includes_static_guides_and_excludes_blog_by_default -v
```

**Expected:** PASS, sitemap URL 집합 변경 없음.

- [ ] 커밋한다.

```bash
git add content/page_registry.py tests/test_page_registry.py docs/content/page-audit-2026-06.csv app.py
git commit -m "refactor: centralize public page indexing registry"
```

**완료 조건:** 공개·색인·허브·관련 링크 정책이 한 파일에서 검증 가능하다.

---

## 트랙 B. 공통 SEO·IA 인프라

### Task B1 [P0]: 8개 허브 데이터와 라우트 구축

**Files**

- Create: `content/hub_pages.py`
- Create: `templates/hub-detail.html`
- Modify: `app.py`
- Modify: `content/page_registry.py`
- Modify: `tests/test_public_pages.py`

- [ ] `age`, `family`, `education`, `anniversary`, `retirement`, `health`, `pets`, `generations` 8개 허브가 200을 반환하는 실패 테스트를 작성한다.
- [ ] 허브마다 title, description, intro, primary endpoints, supporting endpoints, FAQ, source policy를 정의한다.
- [ ] `/age/`, `/family/`, `/education/`, `/anniversary/`, `/retirement/`, `/health/`, `/pets/`, `/generations/` 라우트를 추가한다.
- [ ] 허브 템플릿에 H1, 소개, 대표 도구, 심층 가이드, 관련 허브, 운영 기준 링크를 렌더링한다.
- [ ] 빈 허브로 보이지 않도록 기존 endpoint를 각 허브에 배정한다.
- [ ] 8개 허브를 `release_batch="foundation"`으로 레지스트리에 등록한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_life_hub_pages_are_public \
  tests.test_page_registry -v
```

**Expected:** 8개 허브 200, canonical·H1·description 존재.

- [ ] 커밋한다.

```bash
git add content/hub_pages.py content/page_registry.py templates/hub-detail.html app.py tests/test_public_pages.py
git commit -m "feat: add eight age-based life hubs"
```

### Task B2 [P0]: 전역 내비게이션을 라이프 허브 중심으로 변경

**Files**

- Modify: `app.py`
- Modify: `templates/partials/header.html`
- Modify: `templates/index.html`
- Modify: `static/css/style.css`
- Modify: `tests/test_public_pages.py`

- [ ] 헤더 최상위 항목이 8개 허브 또는 모바일에서 동일한 허브 그룹을 제공하는 테스트를 작성한다.
- [ ] 기존 계산기·표·안내 세 그룹을 허브 중심 정보 구조로 교체한다.
- [ ] 데스크톱 메뉴에는 사용 빈도가 높은 4개 허브를 직접 노출하고 나머지는 전체 메뉴에서 제공한다.
- [ ] 모바일 메뉴에는 8개 허브를 모두 노출하되 각 허브의 대표 링크를 3개 이하로 제한한다.
- [ ] 홈페이지 섹션을 8개 허브 소개 카드로 재구성하고 기존 모든 도구 링크는 각 허브에서 접근 가능하게 한다.
- [ ] 키보드 탐색, `aria-expanded`, focus-visible 상태를 검증한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_header_uses_life_hub_navigation \
  tests.test_public_pages.PublicPageTests.test_home_page_links_all_life_hubs -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add app.py templates/partials/header.html templates/index.html static/css/style.css tests/test_public_pages.py
git commit -m "feat: reorganize navigation around life hubs"
```

### Task B3 [P0]: Breadcrumb와 구조화 데이터 표준화

**Files**

- Create: `templates/partials/breadcrumbs.html`
- Modify: `templates/hub-detail.html`
- Modify: 핵심 20개 템플릿
- Modify: `tests/test_public_pages.py`

- [ ] 홈을 제외한 모든 핵심 페이지에서 화면 Breadcrumb와 `BreadcrumbList` JSON-LD가 존재하는 테스트를 작성한다.
- [ ] Breadcrumb 데이터는 `page_registry`의 hub와 title을 사용해 context processor에서 생성한다.
- [ ] 허브 페이지는 `홈 > 허브`, 상세 페이지는 `홈 > 허브 > 페이지` 구조를 사용한다.
- [ ] canonical과 Breadcrumb URL이 동일한 절대 URL을 가리키게 한다.
- [ ] 기존 SoftwareApplication·FAQPage JSON-LD와 충돌하지 않도록 별도 script 블록으로 렌더링한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_core_pages_render_breadcrumb_schema -v
```

**Expected:** 핵심 페이지 샘플 전부 PASS.

- [ ] 커밋한다.

```bash
git add templates/partials/breadcrumbs.html templates app.py tests/test_public_pages.py
git commit -m "feat: add consistent breadcrumbs and schema"
```

### Task B4 [P0]: 작성·검수·출처 메타데이터 표준화

**Files**

- Create: `content/editorial_metadata.py`
- Create: `content/official_sources.py`
- Create: `templates/partials/editorial-meta.html`
- Modify: `templates/references.html`
- Modify: 핵심 20개 템플릿
- Modify: `tests/test_public_pages.py`

- [ ] 핵심 20개 페이지에 작성자, 검수자, 기준 확인일, 최종 수정일, 출처가 표시되는 실패 테스트를 작성한다.
- [ ] 일반 계산기에는 `AgeCalc 편집팀` 검수와 계산 기준 출처를 연결한다.
- [ ] YMYL 페이지는 기관명, 원문 URL, 확인일, 면책문구를 필수로 요구하도록 데이터 검증 함수를 작성한다.
- [ ] `editorial-meta.html`에 보이는 메타데이터와 `dateModified`, `author`, `reviewedBy` 구조화 데이터를 렌더링한다.
- [ ] `references.html`에서 페이지별 출처 정책과 수정 요청 경로를 설명한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_core_pages_render_editorial_metadata \
  tests.test_public_pages.PublicPageTests.test_ymyl_pages_require_official_sources -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add content/editorial_metadata.py content/official_sources.py templates/partials/editorial-meta.html templates/references.html templates tests/test_public_pages.py
git commit -m "feat: standardize editorial trust metadata"
```

### Task B5 [P0]: 문맥형 관련 링크 컴포넌트 구축

**Files**

- Create: `templates/partials/related-paths.html`
- Modify: `content/page_registry.py`
- Modify: `app.py`
- Modify: 핵심 20개 템플릿
- Modify: `tests/test_page_registry.py`
- Modify: `tests/test_public_pages.py`

- [ ] 모든 core 페이지가 상위 허브 1개와 관련 endpoint 3개 이상을 가지는 레지스트리 테스트를 작성한다.
- [ ] related link를 `before_calculation`, `after_result`, `adjacent_tools`, `official_sources` 네 그룹으로 전달한다.
- [ ] 계산 전 링크는 기준 가이드, 결과 후 링크는 다음 라이프 이벤트, 인접 도구는 같은 입력을 재사용할 수 있는 페이지로 구성한다.
- [ ] 결과 기반 링크를 지원하는 페이지에는 서버 결과 객체의 `recommended_endpoints`를 우선 렌더링한다.
- [ ] 동일 페이지 자기 링크와 중복 href를 제거한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_page_registry.PageRegistryTests.test_core_pages_have_contextual_links \
  tests.test_public_pages.PublicPageTests.test_core_pages_render_contextual_links -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add content/page_registry.py templates/partials/related-paths.html app.py templates tests/test_page_registry.py tests/test_public_pages.py
git commit -m "feat: add contextual internal link paths"
```

### Task B6 [P0]: 허브별 sitemap index 전환

**Files**

- Modify: `app.py`
- Modify: `static/robots.txt`
- Modify: `scripts/adsense_preflight.py`
- Modify: `tests/test_public_pages.py`
- Modify: `tests/test_adsense_preflight.py`

- [ ] `/sitemap.xml`이 `sitemapindex`를 반환하고 9개 하위 sitemap을 가리키는 실패 테스트를 작성한다.
- [ ] `/sitemaps/core.xml`, `/sitemaps/<hub>.xml`, `/sitemaps/guides.xml` 라우트를 추가한다.
- [ ] 각 하위 sitemap은 레지스트리의 `hub`, `indexable`, `release_batch`를 기준으로 URL을 생성한다.
- [ ] query string, fragment, noindex, minigame, 비공개 blog URL이 포함되지 않는 테스트를 작성한다.
- [ ] `lastmod`는 레지스트리 또는 가이드의 실제 수정일만 사용한다.
- [ ] preflight가 sitemap index를 순회해 모든 URL을 검사하도록 확장한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_adsense_preflight \
  tests.test_public_pages.PublicPageTests.test_sitemap_index_groups_public_pages -v
```

**Expected:** PASS.

- [ ] 프리플라이트를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/adsense_preflight.py --format text
```

**Expected:** PASS와 전체 공개 URL 검사 수 출력.

- [ ] 커밋한다.

```bash
git add app.py static/robots.txt scripts/adsense_preflight.py tests/test_public_pages.py tests/test_adsense_preflight.py
git commit -m "feat: split sitemap by life hub"
```

---

## 트랙 C. 기존 핵심 콘텐츠 심층화

### Task C1 [P0]: 공통 콘텐츠 품질 감사 도구

**Files**

- Create: `scripts/content_quality_audit.py`
- Create: `tests/test_content_quality_audit.py`
- Modify: `scripts/adsense_preflight.py`

- [ ] indexable 페이지에 H1, 직접 답변, 최소 3개 H2, editorial meta, 관련 링크, canonical이 있는지 검사하는 테스트를 작성한다.
- [ ] YMYL 페이지에는 공식 출처 1개 이상과 면책문구를 추가 검사한다.
- [ ] 페이지 본문 길이는 통과 보장이 아니라 경고 지표로만 사용하고, 1,000자 미만을 `thin_content_warning`으로 보고한다.
- [ ] 동일 title, description, H1, 본문 문장 반복률을 경고한다.
- [ ] text와 JSON 출력 형식을 제공한다.
- [ ] 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --format text
```

**Expected:** 현재 보강이 필요한 URL이 FAIL 또는 WARNING으로 열거됨.

- [ ] 커밋한다.

```bash
git add scripts/content_quality_audit.py tests/test_content_quality_audit.py scripts/adsense_preflight.py
git commit -m "feat: add indexable content quality audit"
```

### Task C2 [P0]: 나이 계산 핵심 5페이지 보강

**Files**

- Modify: `templates/age.html`
- Modify: `templates/birth-year-age-table.html`
- Modify: `templates/annual-age-calculator.html`
- Modify: `templates/age-comparison-table.html`
- Modify: `templates/birthday-dday-calculator.html`
- Modify: `content/editorial_metadata.py`
- Modify: `tests/test_public_pages.py`

- [ ] 각 페이지의 독립 검색 의도와 필수 고유 섹션을 테스트 fixture로 정의한다.
- [ ] 직접 답변, 계산 공식, 실제 사례 3개, 예외, 공식 기준, 결과 다음 행동을 페이지별로 다르게 작성한다.
- [ ] `age.html`의 연령별 제도 정보는 공식 출처 확인일을 표시하고 변동 가능성이 큰 항목은 일반 안내로 축소한다.
- [ ] 출생연도표는 나이·띠·세대·학교·기념 나이 해석으로 확장한다.
- [ ] 연나이와 비교표가 같은 의도를 경쟁하지 않도록 연나이는 입력형, 비교표는 개념 비교형으로 역할을 고정한다.
- [ ] 테스트와 품질 감사를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_public_pages -v
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --paths /age /birth-year-age-table /annual-age-calculator /age-comparison-table /birthday-dday-calculator
```

**Expected:** 5개 URL PASS.

- [ ] 커밋한다.

```bash
git add templates/age.html templates/birth-year-age-table.html templates/annual-age-calculator.html templates/age-comparison-table.html templates/birthday-dday-calculator.html content/editorial_metadata.py tests/test_public_pages.py
git commit -m "content: deepen core age calculation pages"
```

### Task C3 [P0]: 교육 핵심 5페이지 보강

**Files**

- Modify: `templates/school-grade-calculator.html`
- Modify: `templates/school-entry-year-table.html`
- Modify: `templates/grade-age-table.html`
- Modify: `templates/grade-birth-year-table.html`
- Modify: `templates/college-entry-year-calculator.html`
- Modify: `content/official_sources.py`
- Modify: `tests/test_public_pages.py`

- [ ] 학년도, 1~2월 처리, 조기입학, 입학유예, 해외 학제 제외를 페이지별로 명시한다.
- [ ] 각 페이지의 역할을 학년 계산, 입학 시점, 학년별 나이, 학년별 출생연도, 대학 학번으로 분리한다.
- [ ] 교육청·정부 공식 안내 링크와 기준 확인일을 추가한다.
- [ ] 결과에 따라 졸업년도, 입학년도, 부모·자녀 페이지 링크가 달라지는 테스트를 작성한다.
- [ ] 테스트와 품질 감사를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_public_pages -v
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --hub education
```

**Expected:** 교육 핵심 5개 URL PASS.

- [ ] 커밋한다.

```bash
git add templates/school-grade-calculator.html templates/school-entry-year-table.html templates/grade-age-table.html templates/grade-birth-year-table.html templates/college-entry-year-calculator.html content/official_sources.py tests/test_public_pages.py
git commit -m "content: deepen education age pages"
```

### Task C4 [P0]: 가족·기념일 핵심 5페이지 보강

**Files**

- Modify: `templates/baby-months.html`
- Modify: `templates/baby-months-table.html`
- Modify: `templates/100-day-calculator.html`
- Modify: `templates/d-day.html`
- Modify: `templates/parent-child.html`
- Modify: `content/official_sources.py`
- Modify: `tests/test_public_pages.py`

- [ ] 월령 계산과 발달 판단을 분리하고 의료 진단이 아니라 날짜 계산임을 명시한다.
- [ ] 100일 계산의 시작일 포함 기준, D-day의 포함 기준, 윤년·월말 예외를 사례로 설명한다.
- [ ] 부모·자녀 결과에 부모의 환갑·칠순과 자녀의 학교 시점을 연결한다.
- [ ] 질병관리청·국민건강보험공단 등 공식 출처를 검수 데이터에 등록한다.
- [ ] 테스트와 품질 감사를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_public_pages -v
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --hub family
```

**Expected:** 5개 URL PASS.

- [ ] 커밋한다.

```bash
git add templates/baby-months.html templates/baby-months-table.html templates/100-day-calculator.html templates/d-day.html templates/parent-child.html content/official_sources.py tests/test_public_pages.py
git commit -m "content: deepen family and anniversary pages"
```

### Task C5 [P0]: 반려동물·가이드 핵심 5페이지 보강과 중복 정리

**Files**

- Modify: `templates/dog.html`
- Modify: `templates/cat.html`
- Modify: `templates/pet-age-table.html`
- Modify: `templates/pet-months-table.html`
- Modify: `templates/guide.html`
- Modify: `content/guide_pages.py`
- Modify: `content/page_registry.py`
- Modify: `tests/test_public_pages.py`

- [ ] 반려동물 계산 페이지에서 환산 나이와 건강 상태 판단을 분리한다.
- [ ] 체형·품종·생활환경에 따른 한계를 명확히 표시하고 수의학적 진단 표현을 제거한다.
- [ ] 가이드 20개의 검색 의도 중복표를 작성하고 `keep`, `merge`, `strengthen`, `noindex`를 확정한다.
- [ ] 유지 가이드는 동일한 5섹션 패턴을 깨고 사례·표·공식 기준 중 최소 2개를 추가한다.
- [ ] 통합 대상 URL은 즉시 삭제하지 않고 canonical 또는 noindex 후 향후 301 대상으로 기록한다.
- [ ] 품질 감사를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --hub pets
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_public_pages -v
```

**Expected:** 반려동물 핵심 URL PASS, 가이드 의도 중복 테스트 PASS.

- [ ] 커밋한다.

```bash
git add templates/dog.html templates/cat.html templates/pet-age-table.html templates/pet-months-table.html templates/guide.html content/guide_pages.py content/page_registry.py tests/test_public_pages.py
git commit -m "content: strengthen pet pages and consolidate guides"
```

---

## 트랙 D. 신규 고수요 기능

### Task D1 [P1, Batch 1]: 일반 날짜 계산 엔진과 나이 도구 3개

**기능**

1. 살아온 일수 계산기 `/age/days-lived`
2. 다음 생일까지 남은 시간 `/age/next-birthday`
3. 출생년도 역산 계산기 `/age/birth-year-from-age`

**Files**

- Create: `services/__init__.py`
- Create: `services/date_calculators.py`
- Create: `tests/test_date_calculators.py`
- Create: `templates/calculators/days-lived.html`
- Create: `templates/calculators/next-birthday.html`
- Create: `templates/calculators/birth-year-from-age.html`
- Modify: `app.py`
- Modify: `content/page_registry.py`
- Modify: `content/hub_pages.py`
- Modify: `tests/test_public_pages.py`

- [ ] `days_lived(birth_date, as_of)`가 출생일 당일 0일, 다음 날 1일, 윤년을 정확히 계산하는 실패 테스트를 작성한다.
- [ ] `next_birthday(month, day, as_of)`가 생일 당일, 이미 지난 생일, 2월 29일 정책을 처리하는 실패 테스트를 작성한다.
- [ ] `birth_year_range_for_age(age, as_of)`가 생일 전후 가능한 출생연도를 반환하는 실패 테스트를 작성한다.
- [ ] 결정적 계산 함수를 구현하고 단위 테스트를 통과시킨다.
- [ ] GET query 방식의 서버 렌더링 라우트와 세 템플릿을 추가한다.
- [ ] query가 없어도 독립 본문·예시·출처·관련 링크가 보이게 한다.
- [ ] `release_batch="batch-1"`과 `indexable=True`로 등록한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_date_calculators \
  tests.test_public_pages -v
```

**Expected:** PASS.

- [ ] 품질 감사를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --paths /age/days-lived /age/next-birthday /age/birth-year-from-age
```

**Expected:** 3개 URL PASS.

- [ ] 커밋한다.

```bash
git add services templates/calculators content/page_registry.py content/hub_pages.py app.py tests
git commit -m "feat: add high-value age date calculators"
```

### Task D2 [P1, Batch 1]: 가족 날짜 도구 4개

**기능**

1. 출산 예정일 `/family/due-date`
2. 임신 주수 `/family/pregnancy-weeks`
3. 아기 생후 일수 `/family/baby-days`
4. 돌 날짜 `/family/first-birthday`

**Files**

- Modify: `services/date_calculators.py`
- Modify: `tests/test_date_calculators.py`
- Create: `templates/calculators/due-date.html`
- Create: `templates/calculators/pregnancy-weeks.html`
- Create: `templates/calculators/baby-days.html`
- Create: `templates/calculators/first-birthday.html`
- Modify: `content/official_sources.py`
- Modify: `content/page_registry.py`
- Modify: `content/hub_pages.py`
- Modify: `app.py`
- Modify: `tests/test_public_pages.py`

- [ ] 마지막 생리 시작일 기준 280일 예정일 계산과 주수 계산 테스트를 작성한다.
- [ ] 예정일은 의료 확정값이 아니라 일반 추정치라는 결과 필드를 필수로 한다.
- [ ] 임신 주수는 미래 입력, 42주 초과, 존재하지 않는 날짜를 오류로 처리한다.
- [ ] 아기 생후 일수와 돌 날짜는 출생일 포함 여부를 결과에 명시한다.
- [ ] 보건복지부·질병관리청·의료기관 공식 기준을 출처 데이터에 등록한다.
- [ ] 네 페이지에 의료 면책, 응급상황 안내 금지, 전문 상담 우선 문구를 추가한다.
- [ ] `release_batch="batch-1"`로 등록하고 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_date_calculators \
  tests.test_public_pages -v
```

**Expected:** PASS.

- [ ] 품질 감사에서 YMYL 필수 조건을 검사한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --hub family
```

**Expected:** 신규 4개 URL PASS.

- [ ] 커밋한다.

```bash
git add services/date_calculators.py tests/test_date_calculators.py templates/calculators content/official_sources.py content/page_registry.py content/hub_pages.py app.py tests/test_public_pages.py
git commit -m "feat: add pregnancy and baby date tools"
```

### Task D3 [P1, Batch 2]: 교육·기념일 도구 3개

**기능**

1. 졸업년도 `/education/graduation-year`
2. 커플 기념일 `/anniversary/couple`
3. 환갑·칠순 날짜 `/anniversary/milestone-birthday`

**Files**

- Create: `services/education_calculators.py`
- Create: `tests/test_education_calculators.py`
- Modify: `services/date_calculators.py`
- Modify: `tests/test_date_calculators.py`
- Create: `templates/calculators/graduation-year.html`
- Create: `templates/calculators/couple-anniversary.html`
- Create: `templates/calculators/milestone-birthday.html`
- Modify: `app.py`
- Modify: `content/page_registry.py`
- Modify: `content/hub_pages.py`
- Modify: `tests/test_public_pages.py`

- [ ] 표준 한국 학제 기준 졸업년도와 입학유예 offset 테스트를 작성한다.
- [ ] 커플 기념일은 시작일 포함 여부를 UI에서 선택하고 100·200·365·1,000일을 반환한다.
- [ ] 환갑은 만 60세, 칠순·팔순은 전통 표현과 만나이 기준을 함께 반환하고 한 기준을 정답으로 단정하지 않는다.
- [ ] 세 페이지에 고유 사례·체크리스트·관련 링크를 추가한다.
- [ ] `release_batch="batch-2"`로 등록한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_education_calculators \
  tests.test_date_calculators \
  tests.test_public_pages -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add services/education_calculators.py services/date_calculators.py tests templates/calculators app.py content/page_registry.py content/hub_pages.py
git commit -m "feat: add graduation and milestone calculators"
```

### Task D4 [P1, Batch 3]: 연금·정년·건강 도구 4개

**기능**

1. 국민연금 수령 가능 나이 `/retirement/pension-age`
2. 정년퇴직 날짜 `/retirement/retirement-date`
3. 건강검진 대상년도 `/health/checkup-year`
4. 영유아 검진 시기 `/health/infant-checkup`

**Files**

- Create: `services/retirement_calculators.py`
- Create: `services/health_calculators.py`
- Create: `tests/test_retirement_calculators.py`
- Create: `tests/test_health_calculators.py`
- Create: `templates/calculators/pension-age.html`
- Create: `templates/calculators/retirement-date.html`
- Create: `templates/calculators/health-checkup-year.html`
- Create: `templates/calculators/infant-checkup.html`
- Modify: `content/official_sources.py`
- Modify: `content/editorial_metadata.py`
- Modify: `content/page_registry.py`
- Modify: `content/hub_pages.py`
- Modify: `app.py`
- Modify: `tests/test_public_pages.py`

- [ ] 국민연금 출생연도 구간별 지급개시연령을 공식 표와 일치시키는 경계값 테스트를 작성한다.
- [ ] 정년 계산은 법정 일반 기준과 회사·직군별 규정 차이를 분리하고, 사용자 지정 정년 나이를 입력받는다.
- [ ] 건강검진 대상년도는 출생연도 홀짝 안내와 가입 유형에 따른 차이를 결과에 표시한다.
- [ ] 영유아 검진은 공식 차수별 월령 구간을 데이터 상수로 관리하고 경계값을 테스트한다.
- [ ] 각 데이터 상수에 `source_url`, `verified_on`, `effective_from`을 포함한다.
- [ ] 공식 기준이 만료되거나 확인일이 180일을 넘으면 품질 감사가 경고하도록 한다.
- [ ] `release_batch="batch-3"`로 등록하되 공식 출처 검수 완료 전 `indexable=False`로 유지한다.
- [ ] 검수 후 `indexable=True`로 전환하는 별도 커밋을 만든다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_retirement_calculators \
  tests.test_health_calculators \
  tests.test_public_pages -v
```

**Expected:** 모든 경계값 PASS.

- [ ] 품질 감사를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --hub retirement
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --hub health
```

**Expected:** YMYL 필수 조건 PASS.

- [ ] 커밋한다.

```bash
git add services/retirement_calculators.py services/health_calculators.py tests templates/calculators content/official_sources.py content/editorial_metadata.py content/page_registry.py content/hub_pages.py app.py
git commit -m "feat: add sourced retirement and health tools"
```

### Task D5 [P1, Batch 3]: 나이별 인생 타임라인

**Files**

- Create: `services/life_timeline.py`
- Create: `tests/test_life_timeline.py`
- Create: `templates/calculators/life-timeline.html`
- Create: `static/js/life-timeline.js`
- Modify: `static/css/style.css`
- Modify: `app.py`
- Modify: `content/page_registry.py`
- Modify: `content/hub_pages.py`
- Modify: `tests/test_public_pages.py`

- [ ] 생년월일 입력으로 생일, 학교, 성년, 환갑 이벤트를 생성하는 단위 테스트를 작성한다.
- [ ] 공식 제도 이벤트는 출처가 있는 항목만 포함하고 추정 이벤트에는 `estimated=True`를 표시한다.
- [ ] 미래 이벤트와 과거 이벤트를 날짜순으로 반환한다.
- [ ] 서버 렌더링 결과를 기본으로 제공하고 JavaScript는 필터·공유 카드 UI만 담당한다.
- [ ] 사용자의 생년월일을 서버나 DB에 저장하지 않는 테스트와 개인정보 문구를 추가한다.
- [ ] `release_batch="batch-3"`로 등록하고 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_life_timeline \
  tests.test_public_pages -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add services/life_timeline.py tests/test_life_timeline.py templates/calculators/life-timeline.html static/js/life-timeline.js static/css/style.css app.py content/page_registry.py content/hub_pages.py tests/test_public_pages.py
git commit -m "feat: add personal life timeline"
```

### Task D6 [P1]: 배치 출시 게이트

**Files**

- Modify: `content/page_registry.py`
- Modify: `scripts/content_quality_audit.py`
- Create: `scripts/release_batch_check.py`
- Create: `tests/test_release_batch_check.py`
- Create: `docs/operations/release-batches.md`

- [ ] batch별 모든 URL이 200, canonical, indexable, hub 링크 1개, 문맥 링크 2개 이상을 만족하는 검사기를 작성한다.
- [ ] 실패 URL이 하나라도 있으면 종료 코드 1을 반환한다.
- [ ] sitemap에는 `released=True`인 batch만 포함하도록 레지스트리 필드를 추가한다.
- [ ] 각 batch를 배포한 날짜, GSC 제출일, 검사 URL, 2주·4주 결과를 기록하는 운영 문서를 만든다.
- [ ] 검사한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py batch-1
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py batch-2
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py batch-3
```

**Expected:** 준비된 batch는 PASS, 미완료 batch는 구체적 실패 사유와 종료 코드 1.

- [ ] 커밋한다.

```bash
git add content/page_registry.py scripts/content_quality_audit.py scripts/release_batch_check.py tests/test_release_batch_check.py docs/operations/release-batches.md
git commit -m "feat: gate indexed pages by release batch quality"
```

---

## 트랙 E. AI 최소 기능

### Task E1 [P1]: OpenAI 서비스 경계와 환경 설정

**Files**

- Modify: `requirements.txt`
- Create: `services/ai_explanations.py`
- Create: `tests/test_ai_explanations.py`
- Modify: `app.py`
- Modify: `.env.rss` documentation only through `DEPLOYMENT_GUIDE.md`

- [ ] `openai` SDK의 고정 버전을 requirements에 추가한다.
- [ ] `OPENAI_API_KEY`, `OPENAI_TEXT_MODEL`, `AI_FEATURES_ENABLED` 환경변수 정책을 문서화한다.
- [ ] API key가 없거나 기능 플래그가 꺼져 있으면 외부 호출 없이 결정적 기본 설명을 반환하는 테스트를 작성한다.
- [ ] API 호출은 주입 가능한 client를 사용해 테스트에서 네트워크를 호출하지 않게 한다.
- [ ] 반환 타입을 `title`, `summary`, `cautions`, `next_actions` 네 필드로 제한한다.
- [ ] timeout, rate limit, moderation 차단, JSON 파싱 실패를 사용자 안전 메시지로 변환한다.
- [ ] CSP와 개인정보 정책에 AI 처리 고지를 추가하되 사용자 입력 저장은 하지 않는다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_ai_explanations -v
```

**Expected:** 외부 네트워크 없이 PASS.

- [ ] 커밋한다.

```bash
git add requirements.txt services/ai_explanations.py tests/test_ai_explanations.py app.py DEPLOYMENT_GUIDE.md templates/privacy.html
git commit -m "feat: add safe OpenAI explanation service boundary"
```

### Task E2 [P1]: AI 결과 해설과 메시지 기능 3개

**기능**

1. 만나이 결과 쉬운 해설
2. 인생 타임라인 문장 요약
3. 생일·환갑·칠순 메시지 생성

**Files**

- Modify: `services/ai_explanations.py`
- Modify: `tests/test_ai_explanations.py`
- Modify: `templates/age.html`
- Modify: `templates/calculators/life-timeline.html`
- Create: `templates/partials/ai-explanation.html`
- Create: `static/js/ai-explanation.js`
- Modify: `app.py`
- Modify: `tests/test_public_pages.py`

- [ ] AI endpoint가 계산된 숫자를 입력으로 받고 생년월일 원문을 전달하지 않는 테스트를 작성한다.
- [ ] 결과 해설은 법률·의료·재정 판단을 생성하지 않도록 시스템 지침과 schema를 고정한다.
- [ ] 메시지 생성은 관계, 행사, 말투, 길이만 입력받고 민감정보를 요구하지 않는다.
- [ ] 모든 AI endpoint에 POST, CSRF 대응 방식, payload 길이 제한, 분당 요청 제한을 적용한다.
- [ ] AI 실패 시 기존 계산 결과와 정적 설명이 그대로 남는 progressive enhancement 구조로 구현한다.
- [ ] AI 결과 영역을 `noindex` 대상 동적 콘텐츠로 유지하고 별도 공개 URL을 만들지 않는다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_ai_explanations \
  tests.test_public_pages -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add services/ai_explanations.py tests/test_ai_explanations.py templates/age.html templates/calculators/life-timeline.html templates/partials/ai-explanation.html static/js/ai-explanation.js app.py tests/test_public_pages.py
git commit -m "feat: add low-risk AI life explanations"
```

### Task E3 [P1]: AI 운영 로그와 비용 보호

**Files**

- Modify: `models/blog_models.py`
- Modify: `db.py`
- Create: `tests/test_ai_usage.py`
- Modify: `services/ai_explanations.py`
- Create: `scripts/ai_usage_report.py`
- Modify: `DEPLOYMENT_GUIDE.md`

- [ ] `AiUsageEvent`에 feature, model, success, latency_ms, input_tokens, output_tokens, blocked_reason, created_at만 저장한다.
- [ ] 생년월일, 사용자 prompt 원문, 생성 메시지 원문은 저장하지 않는 테스트를 작성한다.
- [ ] 일일 요청 한도와 기능별 비활성 플래그를 환경변수로 제공한다.
- [ ] 비용·오류·차단 비율을 집계하는 보고 스크립트를 작성한다.
- [ ] DB 저장 실패가 사용자 기능을 중단시키지 않게 한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_ai_usage tests.test_ai_explanations -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add models/blog_models.py db.py tests/test_ai_usage.py services/ai_explanations.py scripts/ai_usage_report.py DEPLOYMENT_GUIDE.md
git commit -m "feat: add privacy-safe AI usage controls"
```

---

## 트랙 F. Search Console 운영과 4~6개월 확장

### Task F1 [P1]: GSC 주간 리뷰 도구와 KPI 기준선

**Files**

- Create: `scripts/gsc_weekly_review.py`
- Create: `tests/test_gsc_weekly_review.py`
- Create: `docs/operations/gsc-weekly-review.md`
- Modify: `content/page_registry.py`

- [ ] Search Console의 쿼리 CSV와 페이지 CSV를 입력받는 parser 테스트를 작성한다.
- [ ] URL을 레지스트리의 hub와 release batch에 매핑한다.
- [ ] 클릭, 노출, CTR, 평균 순위, 신규 쿼리 수를 hub·URL·batch별로 출력한다.
- [ ] `발견됨-미색인`, `크롤링됨-미색인`, canonical 중복은 별도 수동 CSV 입력으로 집계한다.
- [ ] 2주·4주·8주 판단 기준을 운영 문서에 고정한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_gsc_weekly_review -v
```

**Expected:** fixture CSV 집계 PASS.

- [ ] 커밋한다.

```bash
git add scripts/gsc_weekly_review.py tests/test_gsc_weekly_review.py docs/operations/gsc-weekly-review.md content/page_registry.py
git commit -m "feat: add Search Console weekly review workflow"
```

### Task F2 [P2]: 출생연도 프로필 10개 파일럿

**Files**

- Create: `content/birth_year_profiles.py`
- Create: `tests/test_birth_year_profiles.py`
- Create: `templates/birth-year-profile.html`
- Modify: `app.py`
- Modify: `content/page_registry.py`
- Modify: `content/hub_pages.py`
- Modify: `tests/test_public_pages.py`

- [ ] GSC에서 노출이 확인된 출생연도 10개를 운영 입력값으로 선정한다.
- [ ] 각 프로필에 나이, 띠, 세대, 학교 연도, 기념 나이, 검수된 시대 사건을 포함한다.
- [ ] 10개 외 연도는 통합 표로 연결하거나 `indexable=False` 상태의 일반 결과를 제공한다.
- [ ] 본문 고유성 검사에서 프로필 간 공통 문장 비율이 기준을 넘으면 실패하게 한다.
- [ ] 허가된 출처가 없는 유명인·문화 이미지는 포함하지 않는다.
- [ ] 10개 URL을 `release_batch="birth-year-pilot"`로 등록한다.
- [ ] 테스트와 batch 검사를 실행한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_birth_year_profiles tests.test_public_pages -v
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py birth-year-pilot
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add content/birth_year_profiles.py tests/test_birth_year_profiles.py templates/birth-year-profile.html app.py content/page_registry.py content/hub_pages.py tests/test_public_pages.py
git commit -m "feat: pilot ten rich birth-year profiles"
```

### Task F3 [P2]: 세대별 추억 탐험 MVP

**Files**

- Create: `content/generation_memories.py`
- Create: `tests/test_generation_memories.py`
- Create: `templates/generation-memory-explorer.html`
- Create: `static/js/generation-memory-explorer.js`
- Modify: `static/css/style.css`
- Modify: `app.py`
- Modify: `content/page_registry.py`
- Modify: `content/hub_pages.py`

- [ ] 공공 데이터·직접 작성 데이터만 허용하는 source schema를 작성한다.
- [ ] 출생연도에 따라 초등학교, 중학교, 스무 살 시기의 연도를 계산한다.
- [ ] 각 시대 카드에 출처, 범주, 연도 범위를 표시한다.
- [ ] 사용자가 선택한 추억 항목은 브라우저에서 공유 카드로 조합하고 서버에 저장하지 않는다.
- [ ] 저작권이 불명확한 사진·가사·방송 장면을 포함하지 않는 콘텐츠 검사를 작성한다.
- [ ] `release_batch="generation-mvp"`로 등록하고 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_generation_memories tests.test_public_pages -v
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py generation-mvp
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add content/generation_memories.py tests/test_generation_memories.py templates/generation-memory-explorer.html static/js/generation-memory-explorer.js static/css/style.css app.py content/page_registry.py content/hub_pages.py
git commit -m "feat: add sourced generation memory explorer"
```

### Task F4 [P2]: 비회원 내 라이프 캘린더

**Files**

- Create: `templates/my-life-calendar.html`
- Create: `static/js/my-life-calendar.js`
- Create: `tests/test_life_calendar.py`
- Modify: `services/life_timeline.py`
- Modify: `static/css/style.css`
- Modify: `app.py`
- Modify: `content/page_registry.py`
- Modify: `templates/privacy.html`

- [ ] localStorage schema에 version, family member label, date, event type만 저장한다.
- [ ] 이름·생년월일 저장 여부를 사용자가 명시적으로 선택하게 하고 기본값은 저장 안 함으로 둔다.
- [ ] 서버 요청 없이 저장·불러오기·전체 삭제가 동작하는 JavaScript 단위 또는 브라우저 테스트를 작성한다.
- [ ] JSON export/import에 schema version과 유효성 검사를 적용한다.
- [ ] 개인정보처리방침에 브라우저 로컬 저장과 삭제 방법을 추가한다.
- [ ] 개인 캘린더 URL과 데이터는 검색 색인 대상이 되지 않게 한다.
- [ ] 테스트한다.

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_life_calendar tests.test_public_pages -v
```

**Expected:** PASS.

- [ ] 커밋한다.

```bash
git add templates/my-life-calendar.html static/js/my-life-calendar.js tests/test_life_calendar.py services/life_timeline.py static/css/style.css app.py content/page_registry.py templates/privacy.html
git commit -m "feat: add privacy-first local life calendar"
```

### Task F5 [P2]: 광고·제휴 재도입 실험

**Files**

- Modify: `app.py`
- Modify: `templates/partials/adsense.html`
- Create: `templates/partials/contextual-affiliate.html`
- Modify: `static/css/style.css`
- Modify: `tests/test_public_pages.py`
- Create: `docs/operations/monetization-policy.md`

- [ ] 이 Task는 AdSense 승인 완료 후에만 시작한다.
- [ ] 광고 위치를 `after_intro`, `after_result`, `article_mid`, `article_end`로 제한하는 configuration을 작성한다.
- [ ] 계산 폼과 결과 사이, 첫 화면, 오류 메시지 주변에는 광고가 렌더링되지 않는 테스트를 작성한다.
- [ ] 제휴는 `family`, `anniversary`, `pets` 허브의 맥락 일치 페이지 하단에서만 허용한다.
- [ ] 모든 제휴 링크에 `rel="sponsored nofollow noopener"`와 고지 문구가 있는지 테스트한다.
- [ ] 실험별 CLS, 이탈률, 결과 완료율, 광고 수익을 기록한다.
- [ ] 커밋한다.

```bash
git add app.py templates/partials/adsense.html templates/partials/contextual-affiliate.html static/css/style.css tests/test_public_pages.py docs/operations/monetization-policy.md
git commit -m "feat: add controlled contextual monetization"
```

**완료 조건:** 수익화 요소가 계산 완료율과 콘텐츠 가독성을 훼손하지 않는다.

### Task F6 [P2]: 이미지 AI 베타 사전 심사

**Files**

- Create: `docs/product/image-ai-risk-review.md`
- Modify only after approval: `templates/privacy.html`
- No production route in this task

- [ ] 사진 나이 추정, 노화 시뮬레이션, 피부 나이 분석을 각각 개인정보·생체정보·의료 오인·미성년자 위험으로 평가한다.
- [ ] 원본 저장 금지, 즉시 삭제, 동의 문구, 미성년자 차단, 신고·삭제 절차를 정의한다.
- [ ] 피부 나이 분석은 의료 진단으로 오인될 가능성이 높으므로 기본 결론을 `출시 보류`로 기록한다.
- [ ] 승인된 기능만 별도 구현 계획으로 분리한다.
- [ ] 문서만 커밋한다.

```bash
git add docs/product/image-ai-risk-review.md
git commit -m "docs: assess image AI privacy and policy risks"
```

**완료 조건:** 이미지 업로드나 모델 호출을 구현하지 않고 출시 여부가 문서로 결정된다.

---

## 4. 릴리스 체크포인트

### Checkpoint 1: 승인 기반 릴리스

**포함 Task:** A1~A3, B1~B6, C1~C5

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests -v
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/adsense_preflight.py --format text
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py --format text
```

**통과 기준**

- 전체 테스트 PASS
- preflight PASS
- 핵심 20개 URL 품질 PASS
- 모바일 첫 화면 전역 제휴 없음
- 8개 허브와 하위 sitemap 정상
- 블로그·미니게임 noindex 유지

### Checkpoint 2: Batch 1 릴리스

**포함 Task:** D1~D2

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py batch-1
```

**통과 기준**

- 신규 7개 URL 모두 품질 게이트 PASS
- YMYL 2개 페이지 공식 출처·면책 PASS
- 기존 테스트 회귀 없음

### Checkpoint 3: Batch 2 릴리스

**포함 Task:** D3

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py batch-2
```

**통과 기준:** 신규 3개 URL PASS.

### Checkpoint 4: Batch 3 릴리스

**포함 Task:** D4~D5

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/release_batch_check.py batch-3
```

**통과 기준**

- 신규 5개 URL PASS
- 연금·정년·건강 데이터 경계값 PASS
- 공식 출처의 확인일 180일 이내

### Checkpoint 5: AI 최소 기능 릴리스

**포함 Task:** E1~E3

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_ai_explanations \
  tests.test_ai_usage -v
```

**통과 기준**

- API key 부재 시 정적 fallback
- 민감 입력 로그 없음
- moderation·timeout·rate limit 실패가 계산 기능을 중단하지 않음
- AI 동적 결과 별도 색인 URL 없음

## 5. AdSense 재심사 실행 조건

다음 조건이 모두 충족된 이후 운영자가 재심사를 제출한다.

- [ ] Checkpoint 1 완료
- [ ] 배포 후 14일 동안 5xx·canonical·sitemap 오류 없음
- [ ] Search Console에서 핵심 URL 색인 상태 확인
- [ ] 전역 제휴와 첫 화면 광고 없음
- [ ] 핵심 20개 URL에 작성·검수·출처 정보 표시
- [ ] 블로그 자동 공개 비활성 유지
- [ ] 미니게임 noindex와 sitemap 제외 유지
- [ ] 개인정보처리방침·이용약관·문의·운영 원칙 정상 접근
- [ ] 모바일 계산 완료 흐름 수동 검증
- [ ] `ads.txt`, robots.txt, AdSense account meta 정상

## 6. 예상 일정

| 주차 | Task | 산출물 |
|---:|---|---|
| 1 | A1~A3 | 승인 기준선, 전역 제휴 제거, 페이지 레지스트리 |
| 2 | B1~B3 | 8개 허브, 새 내비게이션, Breadcrumb |
| 3 | B4~B6 | 편집 메타, 내부링크, sitemap index |
| 4 | C1~C2 | 품질 감사, 나이 핵심 페이지 보강 |
| 5 | C3~C4 | 교육·가족·기념일 보강 |
| 6 | C5, Checkpoint 1 | 반려동물·가이드 정리, 승인 기반 배포 |
| 7 | D1 | 나이 신규 도구 3개 |
| 8 | D2, Checkpoint 2 | 가족 신규 도구 4개 |
| 9 | D3, Checkpoint 3 | 교육·기념일 신규 도구 3개 |
| 10 | D4 | 연금·정년·건강 도구 4개 |
| 11 | D5~D6, Checkpoint 4 | 인생 타임라인, 배치 게이트 |
| 12 | E1~E3, Checkpoint 5 | AI 최소 기능과 비용 보호 |
| 13~16 | F1~F2 | GSC 리뷰, 출생연도 파일럿 |
| 17~20 | F3 | 세대별 추억 탐험 |
| 21~24 | F4~F6 | 라이프 캘린더, 수익화 실험, 이미지 AI 심사 |

## 7. 최종 완료 기준

- 기존 핵심 20개 URL이 품질 게이트를 통과한다.
- 8개 라이프 허브가 모든 핵심 콘텐츠를 연결한다.
- sitemap index와 허브별 sitemap이 정상 동작한다.
- 신규 기능 15개가 3개 배치로 독립 검증된다.
- 연금·정년·건강·임신 페이지가 공식 출처와 경계값 테스트를 가진다.
- AI 기능은 계산 로직과 분리되고 민감정보를 저장하지 않는다.
- Search Console 리뷰와 콘텐츠 품질 감사가 반복 실행 가능한 스크립트로 남는다.
- AdSense 재심사 전 상업 요소가 콘텐츠보다 먼저 노출되지 않는다.
- 모든 변경은 Task 단위 테스트와 커밋으로 추적된다.
