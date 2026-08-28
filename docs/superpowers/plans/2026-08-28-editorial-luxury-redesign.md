# AgeCalc Editorial Luxury Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Redesign every public AgeCalc surface with the approved Editorial Luxury visual system while preserving calculator behavior, URLs, SEO metadata, and archived minigame routes.

**Architecture:** Keep Flask, Jinja, vanilla JavaScript, and the existing `static/css/style.css` compatibility layer. Add a final-cascade `editorial-luxury.css` stylesheet to public templates, introduce a self-contained homepage age calculator module that does not reuse the page-specific `AgeCalculatorUI`, and migrate representative page families before applying the shared stylesheet to the remaining public templates. Preserve game files and routes; lock their hidden/noindex status with tests.

**Tech Stack:** Python 3, Flask, Jinja2, vanilla CSS, vanilla JavaScript, `unittest`, Node.js assertions for browser-independent JavaScript tests.

**Spec:** `docs/superpowers/specs/2026-08-28-editorial-luxury-redesign-design.md`

## Global Constraints

- Keep Flask, Jinja, vanilla CSS, and the current JavaScript structure; do not migrate frameworks.
- Do not change calculator formulas or server data contracts.
- Do not delete minigame routes, templates, JavaScript, CSS, or image assets.
- Use `#F6F1E8`, `#FCF9F3`, `#241D18`, `#29231F`, `#746B63`, `#66705A`, `#A68B61`, and `#A34C3D` for the approved palette roles.
- Use Cormorant Garamond for English brand/display text, Pretendard for Korean UI/body text, and IBM Plex Mono for dates and calculated values.
- Keep body copy near 65 characters per line with a minimum `1.6` line-height.
- Animate only `transform` and `opacity`; honor `prefers-reduced-motion: reduce`.
- Maintain WCAG AA contrast, visible keyboard focus, 44×44px touch targets, semantic labels, and inline form errors.
- Keep existing title, description, canonical, Open Graph, structured data, privacy masking, ads, and affiliate disclosures intact.
- Preserve all unrelated user changes already present in the worktree.

## Verification note

The Core Web Vitals baseline command currently targets the live `https://agecalc.cloud` origin, not this feature branch. Browser-based viewport, keyboard, and screenshot checks were unavailable in this environment; those checks remain a required preview/deployment gate before production release.

---

## File Structure

- `static/css/editorial-luxury.css`: final-cascade design tokens, shared components, page-family styles, responsive rules, reduced-motion behavior, and game isolation.
- `static/js/home-age-calculator.js`: homepage-only solar-date validation and age/result rendering using unique `home-age-*` selectors.
- `templates/index.html`: editorial split hero, homepage calculator markup, quick links, and existing content/monetization includes.
- `templates/partials/header.html`: shared floating navigation semantics.
- `templates/partials/footer.html`: compact editorial footer.
- `templates/age.html`: representative calculator-page structure; existing IDs and script contracts stay intact.
- `templates/blog-list.html`, `templates/blog-detail.html`, `templates/guide.html`, `templates/guide-detail.html`: representative editorial content surfaces.
- Other public templates listed in Task 6: load the shared final-cascade stylesheet without functional markup rewrites.
- `tests/test_editorial_luxury_theme.py`: visual-contract, homepage calculator, responsive/accessibility, and minigame archival tests.
- `tests/test_public_pages.py`: retain broad public-page SEO and functionality assertions; add only cross-page assertions that belong with the existing suite.

---

### Task 1: Lock the theme and minigame archival contracts

**Files:**
- Create: `tests/test_editorial_luxury_theme.py`
- Modify: `tests/test_public_pages.py`

**Interfaces:**
- Consumes: Flask `app.test_client()` and existing `/`, `/age`, `/blog`, `/guide`, `/minigames/*`, and sitemap routes.
- Produces: regression contract requiring `editorial-luxury.css` on public pages, excluding it from archived games, and preserving `X-Robots-Tag: noindex, nofollow` for games.

- [ ] **Step 1: Write failing public-theme and game-archive tests**

```python
import re
import unittest

from app import app


class EditorialLuxuryThemeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_representative_public_pages_load_final_theme(self):
        for path in ("/", "/age", "/about", "/references"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                self.assertIn("css/editorial-luxury.css", response.get_data(as_text=True))

    def test_home_exposes_accessible_quick_age_calculator(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="home-age-form"', html)
        self.assertIn('id="home-birth-input"', html)
        self.assertIn('aria-describedby="home-birth-help home-birth-error"', html)
        self.assertIn('id="home-age-result"', html)

    def test_archived_games_stay_reachable_but_hidden(self):
        for path in ("/minigames", "/minigames/guess", "/minigames/snake"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                self.assertEqual("noindex, nofollow", response.headers["X-Robots-Tag"])
                self.assertNotIn("css/editorial-luxury.css", response.get_data(as_text=True))

    def test_public_navigation_has_no_minigame_discovery_link(self):
        for path in ("/", "/age", "/about"):
            html = self.client.get(path).get_data(as_text=True)
            self.assertIsNone(re.search(r'href=["\']\/minigames(?:\/|["\'])', html))
```

- [ ] **Step 2: Run the focused tests and verify they fail for missing theme/home markup**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme -v`

Expected: public-theme and homepage calculator assertions fail; existing minigame header/navigation assertions pass.

- [ ] **Step 3: Add sitemap and source-preservation assertions to the existing public suite**

```python
def test_archived_minigames_are_absent_from_every_sitemap(self):
    locations = _sitemap_leaf_locations(app.test_client())
    self.assertFalse(any("/minigames" in location for location in locations))

def test_archived_minigame_source_files_remain_present(self):
    for path in (
        Path("templates/minigames.html"),
        Path("templates/guess.html"),
        Path("static/js/guess-game.js"),
        Path("static/css/snake.css"),
    ):
        self.assertTrue(path.exists(), path)
```

- [ ] **Step 4: Run the two related suites**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme tests.test_public_pages.PublicPageTests.test_archived_minigames_are_absent_from_every_sitemap tests.test_public_pages.PublicPageTests.test_archived_minigame_source_files_remain_present -v`

Expected: the preservation and sitemap tests pass; theme-dependent tests remain red.

- [ ] **Step 5: Commit the contract tests**

```bash
git add tests/test_editorial_luxury_theme.py tests/test_public_pages.py
git commit -m "test: define editorial theme contracts"
```

---

### Task 2: Add the final-cascade design system and shared chrome

**Files:**
- Create: `static/css/editorial-luxury.css`
- Create: `static/fonts/PretendardVariable.subset.woff2`
- Modify: `templates/partials/header.html`
- Modify: `templates/partials/footer.html`
- Modify: `templates/index.html`
- Modify: `templates/age.html`
- Modify: `templates/about.html`
- Modify: `templates/references.html`
- Test: `tests/test_editorial_luxury_theme.py`

**Interfaces:**
- Consumes: existing class names such as `.container`, `.site-header`, `.mega-nav`, `.footer`, `.btn`, `.section-shell`, and body page classes.
- Produces: CSS custom properties under `:root`, `.editorial-frame`, `.editorial-panel-shell`, `.editorial-panel-core`, `.editorial-link-row`, and `.editorial-result-grid`.

- [ ] **Step 1: Extend the failing test with token and accessibility assertions**

```python
from pathlib import Path

def test_theme_defines_approved_tokens_and_reduced_motion(self):
    css = Path("static/css/editorial-luxury.css").read_text()
    for value in ("#F6F1E8", "#FCF9F3", "#241D18", "#66705A", "#A68B61", "#A34C3D"):
        self.assertIn(value.lower(), css.lower())
    self.assertIn("@media (prefers-reduced-motion: reduce)", css)
    self.assertIn(":focus-visible", css)
    self.assertTrue(Path("static/fonts/PretendardVariable.subset.woff2").read_bytes().startswith(b"wOF2"))
```

- [ ] **Step 2: Run the token test and verify file-not-found failure**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_theme_defines_approved_tokens_and_reduced_motion -v`

Expected: FAIL because `static/css/editorial-luxury.css` does not exist.

- [ ] **Step 3: Vendor the approved Korean body font from the official Pretendard release**

Run:

```bash
curl -fL https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/woff2-dynamic-subset/PretendardVariable.subset.woff2 -o static/fonts/PretendardVariable.subset.woff2
```

Verify:

```bash
file static/fonts/PretendardVariable.subset.woff2
```

Expected: the file is identified as Web Open Font Format (Version 2). The app serves it from `'self'`, so no CSP expansion is required.

- [ ] **Step 4: Create the token foundation and shared component rules**

```css
@import url("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@500;600&family=IBM+Plex+Mono:wght@500;600&display=swap");

@font-face {
  font-family: "Pretendard";
  src: url("../fonts/PretendardVariable.subset.woff2") format("woff2");
  font-style: normal;
  font-weight: 400 700;
  font-display: swap;
}

:root {
  --lux-canvas: #F6F1E8;
  --lux-surface: #FCF9F3;
  --lux-espresso: #241D18;
  --lux-text: #29231F;
  --lux-muted: #746B63;
  --lux-sage: #66705A;
  --lux-gold: #A68B61;
  --lux-danger: #A34C3D;
  --lux-display: "Cormorant Garamond", Georgia, serif;
  --lux-body: "Pretendard", "Apple SD Gothic Neo", "Malgun Gothic", sans-serif;
  --lux-number: "IBM Plex Mono", Consolas, monospace;
  --lux-focus: 0 0 0 3px rgba(102, 112, 90, .28);
}

body:not(.games-hub-page):not([class$="-game-page"]) {
  color: var(--lux-text);
  background: var(--lux-canvas);
  font-family: var(--lux-body);
}

:focus-visible { outline: 2px solid var(--lux-sage); outline-offset: 3px; }
.editorial-panel-shell { padding: 8px; border-radius: 18px; background: rgba(36,29,24,.08); }
.editorial-panel-core { border-radius: 12px; background: var(--lux-espresso); color: var(--lux-surface); }
.editorial-result-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); }
.editorial-result-grid output { font-family: var(--lux-number); font-variant-numeric: tabular-nums; }

@media (max-width: 760px) {
  .editorial-result-grid { grid-template-columns: 1fr; }
}

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { scroll-behavior: auto !important; animation: none !important; transition: none !important; }
}
```

Continue the file with final-cascade overrides for the existing header, buttons, footer, fields, tables, alerts, cookie banner, and responsive breakpoints. Scope every rule so archived game layouts retain `style.css` behavior.

- [ ] **Step 5: Load the theme after `style.css` on the four representative public templates**

```html
<link rel="stylesheet" href="{{ versioned_static('css/style.css') }}" />
<link rel="stylesheet" href="{{ versioned_static('css/editorial-luxury.css') }}" />
```

Apply the same ordering in `index.html`, `age.html`, `about.html`, and `references.html`. Do not add the second link to any minigame template.

- [ ] **Step 6: Refine shared header/footer markup without changing endpoint logic**

Add `editorial-frame` to the shared header, keep `data-nav-toggle`, `data-mobile-nav-overlay`, `data-mobile-nav-panel`, current-page conditions, breadcrumbs, policy links, contact email, donation disclosure, and all ARIA relationships unchanged. Add `editorial-link-row` only to link groups that are visually rendered as editorial rows.

- [ ] **Step 7: Run focused and existing navigation tests**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme tests.test_public_pages.PublicPageTests.test_home_page_removes_minigames_from_primary_navigation -v`

Expected: token, representative stylesheet, navigation, and minigame tests pass; homepage calculator test remains red.

- [ ] **Step 8: Commit the shared design system**

```bash
git add static/css/editorial-luxury.css static/fonts/PretendardVariable.subset.woff2 templates/partials/header.html templates/partials/footer.html templates/index.html templates/age.html templates/about.html templates/references.html tests/test_editorial_luxury_theme.py
git commit -m "feat: add editorial luxury design system"
```

---

### Task 3: Build the homepage editorial calculator hero

**Files:**
- Modify: `templates/index.html`
- Create: `static/js/home-age-calculator.js`
- Modify: `static/css/editorial-luxury.css`
- Test: `tests/test_editorial_luxury_theme.py`

**Interfaces:**
- Consumes: `Date` supplied by the browser and the server-rendered `today` shown as reference copy.
- Produces: `calculateSolarAge(birthIso: string, todayIso: string) -> {ok: boolean, age?: number, daysToBirthday?: number, error?: string}` and DOM IDs `home-age-form`, `home-birth-input`, `home-birth-error`, `home-age-result`, `home-grade-result`, `home-birthday-result`.

- [ ] **Step 1: Write a failing Node contract test launched from Python**

```python
import subprocess

def test_home_calculator_module_handles_birthday_boundaries(self):
    program = r"""
const assert = require('assert');
global.document = { addEventListener() {} };
const { calculateSolarAge } = require('./static/js/home-age-calculator.js');
assert.deepStrictEqual(calculateSolarAge('1992-10-02', '2026-10-01').age, 33);
assert.deepStrictEqual(calculateSolarAge('1992-10-02', '2026-10-02').age, 34);
assert.strictEqual(calculateSolarAge('2027-01-01', '2026-08-28').ok, false);
assert.strictEqual(calculateSolarAge('2024-02-30', '2026-08-28').ok, false);
"""
    result = subprocess.run(["node", "-e", program], capture_output=True, text=True)
    self.assertEqual(0, result.returncode, result.stderr)
```

- [ ] **Step 2: Run the calculator test and verify missing-module failure**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_home_calculator_module_handles_birthday_boundaries -v`

Expected: FAIL with `Cannot find module './static/js/home-age-calculator.js'`.

- [ ] **Step 3: Implement the pure calculation interface first**

```javascript
function parseIsoDate(value) {
  const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || "");
  if (!match) return null;
  const date = new Date(Date.UTC(Number(match[1]), Number(match[2]) - 1, Number(match[3])));
  return date.getUTCFullYear() === Number(match[1]) &&
    date.getUTCMonth() === Number(match[2]) - 1 &&
    date.getUTCDate() === Number(match[3]) ? date : null;
}

function calculateSolarAge(birthIso, todayIso) {
  const birth = parseIsoDate(birthIso);
  const today = parseIsoDate(todayIso);
  if (!birth || !today || birth > today) return { ok: false, error: "올바른 생년월일을 입력하세요." };
  const birthdayPassed = today.getUTCMonth() > birth.getUTCMonth() ||
    (today.getUTCMonth() === birth.getUTCMonth() && today.getUTCDate() >= birth.getUTCDate());
  return { ok: true, age: today.getUTCFullYear() - birth.getUTCFullYear() - (birthdayPassed ? 0 : 1) };
}

if (typeof module !== "undefined") module.exports = { calculateSolarAge };
```

Then bind the form on `DOMContentLoaded`, read the immutable `data-today` ISO value from the form, update the error using `textContent`, toggle `[hidden]`, and never write the birth date into a URL or storage.

- [ ] **Step 4: Replace the current homepage hero dashboard with the approved split hero**

Use semantic markup equivalent to:

```html
<section class="age-hub-hero editorial-hero" aria-labelledby="home-title">
  <div class="editorial-hero-copy">
    <p class="eyebrow">Age calculator & life dates</p>
    <h1 id="home-title">오늘 기준 나이를 바로 계산하세요</h1>
    <p class="page-intro">생년월일부터 중요한 생활 시점까지 차분하게 확인하세요.</p>
  </div>
  <div class="editorial-panel-shell">
    <form id="home-age-form" class="editorial-panel-core" data-today="{{ today.isoformat() }}" novalidate>
      <label for="home-birth-input">생년월일</label>
      <input id="home-birth-input" type="date" required aria-describedby="home-birth-help home-birth-error">
      <p id="home-birth-help">입력한 날짜는 저장하지 않습니다.</p>
      <p id="home-birth-error" role="alert"></p>
      <button class="btn btn-primary" type="submit">계산하기</button>
      <div class="editorial-result-grid" id="home-age-result" aria-live="polite" hidden>
        <div><span>만나이</span><output id="home-age-value"></output></div>
        <div><span>학년</span><a href="{{ url_for('school_grade_calculator') }}">학년 계산</a></div>
        <div><span>생일 D-day</span><a href="{{ url_for('birthday_dday_calculator') }}">D-day 계산</a></div>
      </div>
    </form>
  </div>
</section>
<script src="{{ versioned_static('js/home-age-calculator.js') }}" defer></script>
```

Keep existing quick-reference, life-hub, affiliate, cookie, footer, analytics, and SEO blocks. Do not claim grade or birthday values the homepage module does not calculate.

- [ ] **Step 5: Add desktop overlap and mobile single-column rules**

Implement a two-column hero above 980px. Use pseudo-elements behind `.editorial-panel-shell` for the paper-stack effect; disable their transforms and remove overlap at 980px and below. Keep form controls at least 44px high and results in DOM order after the submit button.

- [ ] **Step 6: Run homepage calculator and public-page tests**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme tests.test_public_pages.PublicPageTests.test_home_page_removes_minigames_from_primary_navigation -v`

Expected: PASS.

- [ ] **Step 7: Commit the homepage redesign**

```bash
git add templates/index.html static/js/home-age-calculator.js static/css/editorial-luxury.css tests/test_editorial_luxury_theme.py
git commit -m "feat: redesign the homepage calculator hero"
```

---

### Task 4: Restyle the calculator family without changing behavior

**Files:**
- Modify: `templates/age.html`
- Modify: `templates/annual-age-calculator.html`
- Modify: `templates/school-grade-calculator.html`
- Modify: `templates/birthday-dday-calculator.html`
- Modify: `templates/baby-months.html`
- Modify: `templates/dog.html`
- Modify: `templates/cat.html`
- Modify: `static/css/editorial-luxury.css`
- Test: `tests/test_editorial_luxury_theme.py`
- Test: `tests/test_public_pages.py`
- Test: `tests/test_pet_age_ui.py`
- Test: `tests/test_birth_date_privacy.py`

**Interfaces:**
- Consumes: existing form IDs, names, `data-*` privacy attributes, script URLs, result container IDs, and JavaScript-rendered result classes.
- Produces: common `.editorial-calculator-page`, `.editorial-calculator-shell`, and `.editorial-supporting-content` wrappers without changing selectors consumed by JavaScript.

- [ ] **Step 1: Add a failing representative calculator markup test**

```python
def test_calculator_pages_use_shared_editorial_structure(self):
    for path in ("/age", "/annual-age-calculator", "/school-grade-calculator", "/birthday-dday-calculator", "/baby-months", "/dog", "/cat"):
        with self.subTest(path=path):
            html = self.client.get(path).get_data(as_text=True)
            self.assertIn("editorial-calculator-page", html)
            self.assertIn("editorial-calculator-shell", html)
            self.assertIn("css/editorial-luxury.css", html)
```

- [ ] **Step 2: Run the new test and verify it fails**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_calculator_pages_use_shared_editorial_structure -v`

Expected: FAIL because shared wrapper classes are absent.

- [ ] **Step 3: Apply the shared structure while preserving functional hooks**

For each template, add the theme stylesheet after `style.css`, add `editorial-calculator-page` to the body, and wrap the existing form/result pair with `editorial-calculator-shell`. Do not rename or remove `birth-input`, `birth-error`, `.age-form`, `result-container`, calendar radio names, privacy `data-clarity-mask`, script query versions, form methods, or action URLs.

- [ ] **Step 4: Add final-cascade calculator states**

Style `.result`, `.result.success`, `.result.error`, `.result.loading`, `.error-msg`, `.input-help`, `.calendar-toggle`, and generated `.age-result-*` classes. Error color must use `--lux-danger`; loading must use a layout-shaped skeleton rather than a rotating spinner; calculated numbers must use `--lux-number`.

- [ ] **Step 5: Run calculator, privacy, and pet UI tests**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme tests.test_birth_date_privacy tests.test_pet_age_ui tests.test_public_pages.PublicPageTests.test_age_result_prioritizes_summary_and_safe_related_links -v`

Expected: PASS.

- [ ] **Step 6: Commit the calculator-family redesign**

```bash
git add templates/age.html templates/annual-age-calculator.html templates/school-grade-calculator.html templates/birthday-dday-calculator.html templates/baby-months.html templates/dog.html templates/cat.html static/css/editorial-luxury.css tests/test_editorial_luxury_theme.py
git commit -m "feat: unify editorial calculator layouts"
```

---

### Task 5: Redesign blog and guide surfaces as editorial content

**Files:**
- Modify: `templates/blog-list.html`
- Modify: `templates/blog-category.html`
- Modify: `templates/blog-detail.html`
- Modify: `templates/guide.html`
- Modify: `templates/guide-detail.html`
- Modify: `templates/partials/editorial-meta.html`
- Modify: `templates/partials/reading-progress.html`
- Modify: `static/css/editorial-luxury.css`
- Test: `tests/test_editorial_luxury_theme.py`
- Test: `tests/test_blog_content_contract.py`
- Test: `tests/test_editorial_metadata.py`
- Test: `tests/test_reading_progress.py`

**Interfaces:**
- Consumes: existing post/category/guide objects, JSON-LD blocks, article metadata, reading-progress hooks, ads, affiliate disclosures, and related-path partials.
- Produces: `.editorial-index`, `.editorial-story-list`, `.editorial-article`, and `.editorial-prose` visual hooks.

- [ ] **Step 1: Write a failing editorial content contract**

```python
def test_content_templates_load_theme_and_keep_readable_prose_hook(self):
    for template_name in ("blog-list.html", "blog-detail.html", "guide.html", "guide-detail.html"):
        source = Path("templates", template_name).read_text()
        self.assertIn("editorial-luxury.css", source)
        self.assertRegex(source, r"editorial-(?:index|article|prose)")
```

- [ ] **Step 2: Run the contract and verify it fails**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_content_templates_load_theme_and_keep_readable_prose_hook -v`

Expected: FAIL for missing stylesheet and hooks.

- [ ] **Step 3: Apply editorial list and article markup hooks**

Add the final theme stylesheet. Preserve all loops, post links, dates, images, alt text, meta robots conditions, JSON-LD, ads, reading progress, and related content. Use alternating media/text rows for lists where an image exists; text-only items stay in the same semantic `<article>` sequence rather than receiving placeholders.

- [ ] **Step 4: Add editorial content styles**

Limit prose to `65ch`, set body line-height to `1.75`, balance headings, use `--lux-gold` only for rules and small metadata, and ensure inline links retain underlines. Keep ad/affiliate blocks visually separated with explicit labels. On mobile, return alternating rows to source-order single-column layout.

- [ ] **Step 5: Run content, metadata, and reading-progress tests**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme tests.test_blog_content_contract tests.test_editorial_metadata tests.test_reading_progress -v`

Expected: PASS.

- [ ] **Step 6: Commit the editorial content redesign**

```bash
git add templates/blog-list.html templates/blog-category.html templates/blog-detail.html templates/guide.html templates/guide-detail.html templates/partials/editorial-meta.html templates/partials/reading-progress.html static/css/editorial-luxury.css tests/test_editorial_luxury_theme.py
git commit -m "feat: add editorial blog and guide layouts"
```

---

### Task 6: Roll the theme across remaining public pages and isolate games

**Files:**
- Modify: `templates/100-day-calculator.html`, `templates/age-comparison-table.html`, `templates/age-gap-calculator.html`, `templates/baby-months-table.html`, `templates/birth-year-age-table.html`, `templates/birth-year-zodiac-table.html`, `templates/college-entry-year-calculator.html`, `templates/contact.html`, `templates/d-day.html`, `templates/faq.html`, `templates/grade-age-table.html`, `templates/grade-birth-year-table.html`, `templates/hub-detail.html`, `templates/korean-age-guide.html`, `templates/life-timeline.html`, `templates/parent-child.html`, `templates/pet-age-table.html`, `templates/pet-months-table.html`, `templates/privacy.html`, `templates/school-entry-year-table.html`, `templates/terms.html`
- Modify: `static/css/editorial-luxury.css`
- Modify: `tests/test_editorial_luxury_theme.py`

**Interfaces:**
- Consumes: every public template that currently loads `style.css`.
- Produces: a complete public-theme allowlist and explicit archived-game exclusion.

- [ ] **Step 1: Add a failing template allowlist test**

```python
PUBLIC_THEME_TEMPLATES = (
    "100-day-calculator.html", "age-comparison-table.html", "age-gap-calculator.html",
    "baby-months-table.html", "birth-year-age-table.html", "birth-year-zodiac-table.html",
    "college-entry-year-calculator.html", "contact.html", "d-day.html", "faq.html",
    "grade-age-table.html", "grade-birth-year-table.html", "hub-detail.html",
    "korean-age-guide.html", "life-timeline.html", "parent-child.html",
    "pet-age-table.html", "pet-months-table.html", "privacy.html",
    "school-entry-year-table.html", "terms.html",
)

def test_remaining_public_templates_load_theme_after_legacy_css(self):
    for name in PUBLIC_THEME_TEMPLATES:
        source = Path("templates", name).read_text()
        self.assertLess(source.index("css/style.css"), source.index("css/editorial-luxury.css"), name)
```

- [ ] **Step 2: Run the allowlist test and verify it fails**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_remaining_public_templates_load_theme_after_legacy_css -v`

Expected: FAIL on the first template without the theme link.

- [ ] **Step 3: Add the second stylesheet mechanically to the allowlisted templates**

Insert exactly this line immediately after the existing `style.css` link in every listed template:

```html
<link rel="stylesheet" href="{{ versioned_static('css/editorial-luxury.css') }}" />
```

Do not edit any game template. Do not alter metadata, scripts, forms, tables, IDs, or Jinja variables during this mechanical pass.

- [ ] **Step 4: Add family-level CSS for tables, policies, FAQ, contact, and hub layouts**

Use existing body classes and semantic elements. Tables receive sticky headers only inside their existing scroll container; policies use `65ch`; FAQ retains native `<details>` behavior; hub pages use an asymmetric two-column intro and single-column mobile flow. Add an explicit `.games-hub-page` and known `*-page .mini-game` isolation block only if public-theme selectors leak through shared partials.

- [ ] **Step 5: Run theme and all public-page tests**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme tests.test_public_pages -v`

Expected: PASS.

- [ ] **Step 6: Commit the public rollout**

```bash
git add templates static/css/editorial-luxury.css tests/test_editorial_luxury_theme.py
git commit -m "feat: roll editorial theme across public pages"
```

Before committing, verify `git diff --cached --name-only` contains no game templates or unrelated `_data`, `_workspace`, `.gitignore`, or roadmap files.

---

### Task 7: Verify accessibility, SEO, performance, and full regression

**Files:**
- Modify: `tests/test_editorial_luxury_theme.py`
- Modify: `scripts/core_web_vitals_baseline.py` only if the existing checker cannot see the newly added stylesheet; otherwise do not change it.
- Modify: `scripts/seo_performance_baseline.py` only if the existing checker requires a public asset allowlist update; otherwise do not change it.
- Modify: `static/css/editorial-luxury.css` and affected templates only for defects found by verification.

**Interfaces:**
- Consumes: finished public UI, Flask test client, existing SEO/Core Web Vitals scripts, and the complete unittest suite.
- Produces: evidence that functionality, discoverability, archived games, accessibility contracts, and asset loading meet the spec.

- [ ] **Step 1: Add static accessibility and privacy assertions**

```python
def test_home_quick_calculator_has_no_persistence_or_query_transport(self):
    script = Path("static/js/home-age-calculator.js").read_text()
    self.assertNotIn("localStorage", script)
    self.assertNotIn("sessionStorage", script)
    self.assertNotIn("URLSearchParams", script)
    self.assertNotIn("fetch(", script)

def test_theme_has_touch_target_and_mobile_overflow_guards(self):
    css = Path("static/css/editorial-luxury.css").read_text()
    self.assertRegex(css, r"min-height:\s*44px")
    self.assertIn("overflow-wrap", css)
    self.assertNotRegex(css, r"transition:\s*(?:all\s+)?(?:linear|ease-in-out)")
```

- [ ] **Step 2: Run the new assertions and fix only concrete failures**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme -v`

Expected: PASS after adding any missing explicit touch-target or wrapping rules.

- [ ] **Step 3: Run syntax and whitespace checks**

Run: `node --check static/js/home-age-calculator.js`

Expected: no output and exit code 0.

Run: `git diff --check`

Expected: no output and exit code 0.

- [ ] **Step 4: Run the complete automated test suite**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests -v`

Expected: all tests pass with no errors or failures.

- [ ] **Step 5: Run the existing SEO and Core Web Vitals baselines**

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/seo_performance_baseline.py`

Expected: exit code 0 with no missing canonical, robots, metadata, or public-asset findings.

Run: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/core_web_vitals_baseline.py`

Expected: exit code 0 with no new blocking asset, image dimension, layout-shift, or continuous-scroll-listener findings.

- [ ] **Step 6: Perform manual responsive and interaction review**

Start the local app with `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python app.py`. Inspect `/`, `/age`, `/blog`, one blog detail, `/guide`, one guide detail, `/birth-year-age-table`, `/privacy`, `/minigames`, and `/minigames/guess` at 1440px, 768px, and 390px widths. Verify keyboard order, visible focus, form errors, result announcement, menu open/close, no horizontal overflow, readable ads/disclosures, and unchanged game boards. Record any failure as a reproducible path/viewport/interaction before fixing it.

- [ ] **Step 7: Review the final diff scope**

Run: `git status --short`

Expected: only planned theme files plus pre-existing unrelated user changes; no generated image, temporary screenshot, game deletion, or dependency file.

Run: `git diff --stat b9385a3..HEAD`

Expected: changes align with Tasks 1–7 and contain no framework migration.

- [ ] **Step 8: Commit verification fixes**

```bash
git add tests/test_editorial_luxury_theme.py static/css/editorial-luxury.css static/js/home-age-calculator.js templates scripts/core_web_vitals_baseline.py scripts/seo_performance_baseline.py
git commit -m "test: verify editorial redesign regression safety"
```

Stage the two scripts only if they were actually modified. Confirm the staged file list before committing so unrelated user files remain untouched.
