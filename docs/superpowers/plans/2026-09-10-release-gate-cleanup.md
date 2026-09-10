# Release Gate Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Make the current production contract and its tests consistent, preserve the consolidated school-page SEO policy, and deploy the multilingual date add/subtract calculator safely.

**Architecture:** Keep `/school-entry-year-table` and `/grade-age-table` as permanent legacy redirects to their consolidated owners. Remove obsolete test expectations for retired documents, retain explicit redirect and canonical-owner coverage, repair genuine content-quality gaps, then merge the verified feature commit into `main` and restart the existing systemd service.

**Tech Stack:** Flask, Jinja, vanilla JavaScript, Python `unittest`, Node.js, Playwright, systemd

**Spec:** Current `content/page_registry.py` ownership policy and the user-approved production deployment request.

## Global Constraints

- Do not restore duplicate school pages or create competing indexable URLs.
- Do not add user `_data` or unrelated `_workspace` artifacts to Git.
- Run Korean copy through `im-not-ai-codex:humanize-korean` before publication.
- Do not deploy unless the full Python suite, focused JavaScript tests, and release preflight pass.
- Preserve the current service definition and database configuration.

---

### Task 1: Reconcile retired school-page tests

**Files:**
- Modify: `tests/test_public_pages.py`

**Interfaces:**
- Consumes: Flask routes `school_entry_year_table()` and `grade_age_table()`.
- Produces: tests that require 301 redirects and validate the consolidated owner pages.

- [x] Remove retired URLs from generic tests that require a rendered 200 document.
- [x] Replace page-specific legacy assertions with redirect target and query-preservation assertions.
- [x] Update navigation and sitemap expectations to include only indexable owners.
- [x] Run `tests.test_public_pages.PublicPageTests` and record remaining failure identities.

### Task 2: Reconcile current UI and query contracts

**Files:**
- Modify: `tests/test_public_pages.py`

**Interfaces:**
- Consumes: content-hashed asset URLs, the desktop navigation panel, the simplified home page, and partial pet-table queries.
- Produces: regression tests for the current implementation rather than superseded markup.

- [x] Update static asset assertions to accept the content hash.
- [x] Assert the current desktop panel selectors and positioning rules.
- [x] Update home-page and pet-query expectations to the current forms.
- [x] Run each corrected test group before proceeding.

### Task 3: Restore education hub content quality

**Files:**
- Modify: `content/hub_pages.py`
- Create: `_workspace/2026-09-10-003/01_input.txt`
- Create: `_workspace/2026-09-10-003/final.md`

**Interfaces:**
- Consumes: the consolidated three-tool education hub.
- Produces: substantive Korean hub copy that clears the existing thin-content audit without linking retired pages.

- [x] Draft only the missing explanatory copy and preserve all school-rule claims.
- [x] Run the humanize-korean fast metrics workflow.
- [x] Apply the approved copy to the education hub.
- [x] Run the education hub and content-quality tests.

### Task 4: Verify the complete release candidate

**Files:**
- Test: `tests/`
- Test: `tests/global-calculations.test.js`
- Test: `scripts/adsense_preflight.py`

**Interfaces:**
- Consumes: the entire working-tree release candidate.
- Produces: a green release gate.

- [x] Run `python -m unittest discover -s tests` and require zero failures and errors.
- [x] Run the global calculation Node test.
- [x] Run the six-locale date-shift Playwright test and 40-flow i18n browser suite.
- [x] Run AdSense preflight and `git diff --check`.

### Task 5: Integrate and deploy

**Files:**
- Commit only the date calculator, test reconciliation, hub copy, and release documentation files.

**Interfaces:**
- Consumes: verified `develop/pre-release` commit.
- Produces: matching `main`, remote branches, restarted `agecalc.service`, and verified production URLs.

- [ ] Review the exact staged file list and commit.
- [ ] Fetch remote state and fast-forward or merge `develop/pre-release` into `main` without discarding unrelated files.
- [ ] Push the updated branches according to the existing remote topology.
- [ ] Restart `agecalc.service` and verify active status, health, six localized pages, canonical/hreflang, and sitemap entries.
