### Task 6 Report: Roll Theme Across Remaining Public Pages And Isolate Games

**Status:** complete

**Files changed:**
- `templates/100-day-calculator.html`
- `templates/age-comparison-table.html`
- `templates/age-gap-calculator.html`
- `templates/baby-months-table.html`
- `templates/birth-year-age-table.html`
- `templates/birth-year-zodiac-table.html`
- `templates/college-entry-year-calculator.html`
- `templates/contact.html`
- `templates/d-day.html`
- `templates/faq.html`
- `templates/grade-age-table.html`
- `templates/grade-birth-year-table.html`
- `templates/hub-detail.html`
- `templates/korean-age-guide.html`
- `templates/life-timeline.html`
- `templates/parent-child.html`
- `templates/pet-age-table.html`
- `templates/pet-months-table.html`
- `templates/privacy.html`
- `templates/school-entry-year-table.html`
- `templates/terms.html`
- `static/css/editorial-luxury.css`
- `tests/test_editorial_luxury_theme.py`

**RED:**
- Command: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_remaining_public_templates_load_theme_after_legacy_css -v`
- Result: failed as expected, 1 error.
- Failure: `ValueError: substring not found` when `templates/100-day-calculator.html` lacked `css/editorial-luxury.css`.
- Command: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_theme_defines_public_page_family_layout_rules -v`
- Result: failed as expected, 1 failure.
- Failure: missing sticky-header/public-family CSS selectors in `static/css/editorial-luxury.css`.

**GREEN:**
- Command: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_remaining_public_templates_load_theme_after_legacy_css tests.test_editorial_luxury_theme.EditorialLuxuryThemeTests.test_theme_defines_public_page_family_layout_rules -v`
- Result: passed, 2 tests.

**Focused Suite:**
- Command: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_editorial_luxury_theme tests.test_public_pages -v`
- Result: passed, 246 tests.

**Full Suite:**
- Command: `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests -v`
- Result: passed, 436 tests.
- Note: bare `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest -v` ran 0 tests in this repo, so the full suite was verified with the explicit `-s tests` start directory.

**Whitespace Check:**
- Command: `git diff --check`
- Result: passed with no output.

**Implementation Notes:**
- Added the final `editorial-luxury.css` stylesheet immediately after legacy `style.css` in the 21 allowlisted public templates only.
- Left archived game templates unchanged; no game template loads the final stylesheet, so no extra isolation block was needed in this pass.
- Added final-cascade family styling for public data tables, raw policy prose sections, FAQ blocks and native `details`, contact cards, and life-hub hero/index layouts.
- Kept sticky headers scoped to existing scroll containers (`.data-table-wrap` and `.table-scroll`) only.
- Preserved metadata, scripts, forms, tables, IDs, and Jinja variables during the mechanical template pass.
- Kept motion transform/opacity-only and maintained 44px targets for interactive controls.

**Self-Review:**
- Narrowed the initial policy-prose selector after self-review to avoid constraining non-policy sections on other themed pages.
- Verified `git diff --cached --name-only` contains only Task 6 templates, `static/css/editorial-luxury.css`, `tests/test_editorial_luxury_theme.py`, and this report file.
- Verified no game templates, `_data`, `_workspace`, `.gitignore`, or roadmap files were staged.

**Concerns:**
- No blocking concerns. Visual QA in a browser was not run; verification here is test and diff based.
