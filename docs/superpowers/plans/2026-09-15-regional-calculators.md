# Regional Calculators Implementation Plan

> **Current status (2026-09-17):** All tasks below were completed and the work was later merged and deployed in `bb5db60`. The no-deployment/no-merge constraints record the original implementation session; they are not the current release state.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox syntax for tracking.

**Goal:** Ship five calculator features as seven locale-scoped pages without deployment.
**Architecture:** Pure Python engines consume bounded holiday data; localized Flask SSR forms integrate with the existing registry, metadata and navigation.
**Tech Stack:** Flask 2.3, Python datetime, korean-lunar-calendar 0.3.1, existing CSS/Jinja.
**Spec:** docs/superpowers/specs/2026-09-15-regional-calculators-design.md

## Global Constraints

No deployment, push or merge. Seven URLs only; supported locales ko, ja, pt-BR and en as mapped in the spec. No personal data in GET URLs, logs or persistence. No unsupported holiday-year estimates. Use apply_patch for authored files. Do not alter unrelated worktree files.

### Task 1: Calculation engines

Files: create `models/regional_calculators.py`, `tests/test_regional_calculators.py`; consume `data/regional_holidays.json` supplied by controller.

Interfaces: `calculate(kind: str, values: dict[str,str], locale: str) -> dict`; result has `rows: list[tuple[str,str]]`, optional `table: list[list[str]]`, `note: str` (translation key); raise ValueError with a stable error key. Kinds lunar_birthday, business_days, school_year, birth_date_range, japanese_era. Dates are ISO strings. Labels are translation keys, never hard-coded prose.

- [x] Write tests before engine: `assert calculate('birth_date_range', {'reference':'2026-09-15','age':'30'}, 'en')['rows'] == [('earliest','1995-09-16'),('latest','1996-09-15')]`.
- [x] Assert school DOB 2020-04-01 enters primary in 2026; 2020-04-02 in 2027. Test gap and university lengths, graduation March vs entry April.
- [x] Assert Reiwa 1-05-01 = 2019-05-01, invalid Reiwa 1-04-30 fails; Gregorian 1989-01-07 Showa64 and 1989-01-08 Heisei1. Reject dates before Gregorian adoption 1873-01-01.
- [x] Assert Korea lunar 2026-01-01 = 2026-02-17; leap month absent is an unavailable table row, never silently regular month. Validate month/day without parsing lunar as Gregorian.
- [x] Assert national holiday exclusion and weekend/custom exclusion not double counted; date-range final-day option and zero/negative addition; out-of-range input/result must fail.
- [x] Run `/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_regional_calculators -v`, record RED, implement, record GREEN.

### Task 2: Locale-scoped SSR integration

Files: modify `content/page_registry.py`, `content/i18n.py`, add `content/regional_copy.py`, `templates/partials/regional-calculator.html`, `static/css/regional-calculator.css`, `tests/test_regional_pages.py`; update affected independent sitemap fixture.

- [x] Write route tests: `self.assertEqual(200, self.client.get('/ja/school-year-calculator').status_code)` and `self.assertEqual(404, self.client.get('/en/school-year-calculator').status_code)`; run and record RED.
- [x] Register five definitions with exact locale allowlists, extend sitemap expansion to omit unsupported base documents, preserve existing 6-language clusters.
- [x] Add GET/POST SSR renderer calling `calculate`; labels are translated, values escaped, results excluded from indexing/caching; language fallback stays explicit.
- [x] Implement seven complete localized copies with examples, scope, source links and FAQ; reuse existing fonts/colors/form layouts.
- [x] Test valid and invalid POSTs, seven canonical URLs, reciprocal actual alternates, unique sitemap entries and absence of phantom root pages.

### Task 3: Verification and handoff

- [x] Run complete unittest discovery and Node calculation tests, update only affected expected URL fixtures.
- [x] Review implementation spec compliance and code quality; fix correctness issues and repeat relevant tests.
- [x] Record holiday provenance, support bounds, Korean copy audit and browser verification availability.
- [x] Leave changes in pre-release for user review; do not deploy or merge.
