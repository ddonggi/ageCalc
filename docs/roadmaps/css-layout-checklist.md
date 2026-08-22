# AgeCalc CSS & Layout Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** AgeCalc의 공통 레이아웃을 화면 크기별로 일관되고 접근성 있게 개선한다.

**Architecture:** 공통 레이아웃 변경은 `static/css/style.css`의 기존 디자인 토큰과 반응형 구간을 확장해 적용한다. 데스크톱과 모바일 동작을 명시적으로 분리하고, 공통 헤더처럼 모든 페이지에 영향을 주는 변경은 구조·가로 넘침·키보드 탐색 회귀 테스트를 먼저 작성한다.

**Tech Stack:** HTML5, Jinja2, vanilla CSS/JavaScript, Python unittest

**Spec:** 이 문서의 작업별 완료 기준

## Global Constraints

- 기존 warm paper 디자인 토큰과 IBM Plex 타이포그래피를 유지한다.
- 데스크톱 기준은 `min-width: 901px`, 모바일·태블릿 기준은 `max-width: 900px`로 통일한다.
- 360px 화면에서 가로 스크롤이 생기지 않아야 한다.
- 키보드 포커스와 모바일 메뉴 열기·닫기 동작을 유지한다.
- `position: fixed` 요소가 본문, 쿠키 배너, 드롭다운 메뉴를 가리지 않아야 한다.
- CSS 변경은 콘텐츠 순서나 검색엔진이 읽는 HTML 구조를 바꾸지 않는다.
- 모든 변경은 `tests/test_public_pages.py`와 전체 unittest를 통과해야 한다.

---

## Task 1: 데스크톱 전체 너비 고정 헤더

**Files:**
- Modify: `static/css/style.css`
- Modify: `templates/partials/header.html` only if a dedicated inner wrapper is required
- Modify: `tests/test_public_pages.py`

**Interfaces:**
- Consumes: `.site-header`, `.container`, `.mega-nav`, `.mega-menu-panel`
- Produces: 데스크톱에서 뷰포트 전체 너비를 차지하며 스크롤 중 고정되는 공통 헤더

- [ ] **Step 1: 데스크톱 fixed 헤더의 회귀 테스트 작성**

```python
def test_desktop_header_is_fixed_full_width_without_changing_mobile_header():
    css = Path("static/css/style.css").read_text(encoding="utf-8")
    assert "@media (min-width: 901px)" in css
    assert "position: fixed" in css
    assert "width: 100%" in css or "inset-inline: 0" in css
    assert "--desktop-header-height" in css
```

- [ ] **Step 2: 테스트가 기존 CSS에서 실패하는지 확인**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_public_pages.PublicPageTests.test_desktop_header_is_fixed_full_width_without_changing_mobile_header -v
```

Expected: 데스크톱 fixed 헤더 규칙과 본문 보정 토큰이 없어 FAIL.

- [ ] **Step 3: 데스크톱 헤더를 전체 너비 fixed로 구현**

적용할 CSS 계약:

```css
:root {
    --desktop-header-height: 104px;
}

@media (min-width: 901px) {
    .site-header {
        position: fixed;
        inset: 0 0 auto;
        width: 100%;
        min-height: var(--desktop-header-height);
        z-index: 1000;
    }

    body {
        padding-top: var(--desktop-header-height);
    }
}
```

기존 `.site-header`의 최대 너비·바깥 여백이 전체 너비 적용을 방해하면 헤더 자체는 full bleed로 두고 내부 정렬용 래퍼를 추가한다. 내부 래퍼의 최대 너비는 기존 `--page-width`를 사용한다.

- [ ] **Step 4: 메뉴와 본문 겹침 방지**

```css
@media (min-width: 901px) {
    .mega-menu-panel {
        z-index: 1010;
    }

    .cookie-banner {
        z-index: 1100;
    }
}
```

헤더 높이가 페이지별 첫 콘텐츠를 덮지 않는지 홈, `/age`, `/dog`, `/life-timeline`, `/blog`에서 확인한다.

- [ ] **Step 5: 반응형 화면 수동 확인**

- 1440px: 헤더가 좌우 전체 너비를 차지한다.
- 1024px: 로고·탐색·액션이 한 줄에서 겹치지 않는다.
- 900px: 기존 모바일 헤더와 메뉴 패널이 유지된다.
- 360px: 가로 스크롤이 없고 메뉴 버튼을 키보드·터치로 사용할 수 있다.
- 200% 확대: 메뉴 텍스트가 잘리거나 본문을 영구적으로 가리지 않는다.

- [ ] **Step 6: 전체 검증**

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests -v
git diff --check
```

Expected: 전체 테스트 PASS, whitespace 오류 없음.

---

## Backlog

- [ ] 공통 헤더 높이와 내부 여백을 데스크톱·태블릿·모바일 토큰으로 분리한다.
- [ ] 긴 페이지에서 현재 허브를 나타내는 활성 메뉴의 대비를 높인다.
- [ ] 키보드 포커스가 fixed 헤더 뒤로 숨지 않도록 `scroll-padding-top`을 적용한다.
- [ ] 360px·768px·1024px·1440px 회귀 화면을 기록하는 시각 테스트 환경을 마련한다.
- [ ] 공통 폼의 입력·오류·도움말 간격을 하나의 CSS 컴포넌트 규칙으로 정리한다.
- [ ] 결과 카드의 숫자 크기와 긴 한국어 줄바꿈을 모바일 기준으로 통일한다.
- [ ] `prefers-reduced-motion`에서 장식 애니메이션과 전환을 축소한다.
- [ ] 프린트 화면에서 fixed 헤더와 광고·쿠키 UI를 숨기는 인쇄 스타일을 추가한다.

## Definition of Done

- [ ] 변경된 레이아웃의 목적과 적용 화면 구간이 문서화되어 있다.
- [ ] 데스크톱·태블릿·모바일 경계값을 확인했다.
- [ ] 키보드 탐색과 200% 확대가 가능하다.
- [ ] 페이지 시작 콘텐츠, 드롭다운, 쿠키 배너가 서로 겹치지 않는다.
- [ ] 가로 스크롤과 누적 레이아웃 이동이 증가하지 않는다.
- [ ] 관련 테스트와 전체 테스트가 통과한다.
