# Mobile Footer QR Size Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 모바일 푸터의 후원 QR 외곽 너비를 104px로 제한해 전체 폭으로 확대되지 않게 한다.

**Architecture:** 기존 `@media (max-width: 980px)` 블록 안에서 `.support-qr`만 제한한다. 데스크톱 기본 그리드와 템플릿 및 SVG는 유지한다.

**Tech Stack:** CSS, Flask/Jinja 페이지 테스트, Git diff 검증

## Global Constraints

- `980px` 이하에서만 QR 외곽 너비를 `104px`로 제한한다.
- 모바일 QR은 왼쪽 정렬한다.
- 데스크톱의 기존 `96px` 그리드 열은 변경하지 않는다.
- 템플릿과 SVG 원본은 변경하지 않는다.
- 문서 가로스크롤을 만들지 않는다.

---

### Task 1: 모바일 QR 크기 제한

**Files:**
- Modify: `static/css/style.css:3742-3746`
- Test: `tests/test_public_pages.py`

**Interfaces:**
- Consumes: 기존 `.support-row`, `.support-qr`, `.support-qr img` 스타일
- Produces: `980px` 이하에서 너비 104px, 왼쪽 정렬인 QR 컨테이너

- [ ] **Step 1: 기준 상태 확인**

Run:

```bash
sed -n '3328,3352p' static/css/style.css
sed -n '3734,3752p' static/css/style.css
```

Expected: 기본 `.support-row`는 `96px 1fr`이고, 모바일 블록은 `.support-row`를 1열로 바꾸지만 `.support-qr` 너비 제한은 없다.

- [ ] **Step 2: 최소 CSS 변경 적용**

`@media (max-width: 980px)` 안에 다음 규칙을 추가한다.

```css
.support-qr {
    width: 104px;
    justify-self: start;
}
```

- [ ] **Step 3: 산술 레이아웃 검증**

외곽 너비 104px에서 좌우 padding 20px와 border 2px를 제외한 실제 QR 이미지가 82px인지 확인한다. 360px 모바일의 최소 콘텐츠 폭보다 작으므로 문서 가로 넘침이 생기지 않음을 확인한다.

- [ ] **Step 4: 기존 페이지 테스트 실행**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_reading_progress tests.test_public_pages.PublicPageTests.test_home_page_renders
```

Expected: 모든 선택 테스트가 통과한다.

- [ ] **Step 5: 변경 범위 및 구문 검증**

Run:

```bash
git diff --check
git diff -- static/css/style.css
```

Expected: 공백 오류가 없고, 모바일 미디어쿼리의 `.support-qr` 규칙만 추가된다.

- [ ] **Step 6: 구현 커밋**

```bash
git add static/css/style.css
git commit -m "fix: constrain mobile footer QR size"
```
