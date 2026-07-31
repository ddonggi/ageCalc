# Hub Content Enrichment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add useful, original guidance to the eight life hubs and the education-family blog category so they clear the internal thin-content check without changing calculator behavior.

**Architecture:** Keep copy in content data, not templates. Add a `usage_guide` field to each hub record and a category-page editorial-content mapping for the education-family category; templates render the shared sections only when their corresponding data exists.

**Tech Stack:** Flask, Jinja2, Python unittest, existing content-quality audit.

---

### Task 1: Establish the failing content-quality regression

**Files:**
- Test: `tests/test_content_quality_audit.py`

- [ ] **Step 1: Write the failing audit regression test**

```python
def test_public_hubs_and_education_family_category_have_no_thin_content_warning(self):
    paths = ("/age/", "/family/", "/education/", "/anniversary/", "/retirement/", "/health/", "/pets/", "/generations/", "/blog/category/education-family")
    report = audit_local_pages(paths=paths)
    warnings = [issue.code for result in report.results for issue in result.warnings]
    self.assertNotIn("thin_content_warning", warnings)
```

- [ ] **Step 2: Run the targeted test and verify RED**

Run: `env ADSENSE_REVIEW_MODE=false BLOG_PUBLIC_INDEXING_ENABLED=true COUPANG_PARTNERS_ENABLED=false /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_content_quality_audit.ContentQualityAuditTests.test_public_hubs_and_education_family_category_have_no_thin_content_warning`

Expected: failure listing one or more `thin_content_warning` entries.

- [ ] **Step 3: Leave the test failing while Tasks 2 and 3 add content**

```python
Do not weaken the 1,000-character audit threshold or add target-page exemptions.
```

### Task 2: Specify and render hub usage guides

**Files:**
- Modify: `content/hub_pages.py`
- Modify: `templates/hub-detail.html`
- Test: `tests/test_public_pages.py`

- [ ] **Step 1: Write failing rendering tests**

```python
def test_life_hub_pages_render_unique_usage_guides(self):
    client = app.test_client()
    for key in ("age", "family", "education", "anniversary", "retirement", "health", "pets", "generations"):
        html = client.get(f"/{key}/").get_data(as_text=True)
        self.assertIn('class="life-hub-usage-guide"', html)
        self.assertIn("이렇게 시작하세요", html)
```

- [ ] **Step 2: Run the targeted test and verify RED**

Run: `env ADSENSE_REVIEW_MODE=true BLOG_PUBLIC_INDEXING_ENABLED=false COUPANG_PARTNERS_ENABLED=false /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_public_pages.PublicPageTests.test_life_hub_pages_render_unique_usage_guides`

Expected: failure because the usage-guide markup is absent.

- [ ] **Step 3: Add the minimal content-data interface and template section**

```python
# Each hub record contains:
"usage_guide": {
    "title": "이렇게 시작하세요",
    "intro": "...",
    "steps": (("첫 번째", "..."), ("두 번째", "..."), ("마지막", "...")),
    "note": "...",
},
```

Render the title, intro, three steps, and note in `hub-detail.html` after the primary tool grid. Populate unique, non-diagnostic copy for all eight hubs.

- [ ] **Step 4: Run the targeted test and verify GREEN**

Run the command from Step 2.

Expected: `OK`.

### Task 3: Add education-family category editorial guidance

**Files:**
- Modify: `content/blog/schema.py`
- Modify: `app.py`
- Modify: `templates/blog-category.html`
- Test: `tests/test_blog_discovery.py`

- [ ] **Step 1: Write a failing category rendering test**

```python
def test_education_family_category_renders_editorial_usage_guide(self):
    # Patch eligible posts so the category is indexable, then assert the guide title,
    # its three step headings, and its FAQ section are in the response.
```

- [ ] **Step 2: Run the targeted test and verify RED**

Run: `env ADSENSE_REVIEW_MODE=true BLOG_PUBLIC_INDEXING_ENABLED=false COUPANG_PARTNERS_ENABLED=false /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_blog_discovery.BlogDiscoveryTests.test_education_family_category_renders_editorial_usage_guide`

Expected: failure because no category editorial guide is passed to the template.

- [ ] **Step 3: Add minimal category content mapping and conditional rendering**

```python
CATEGORY_PAGE_EDITORIAL_CONTENT = {
    "education-family": {
        "title": "학교·육아 정보를 확인하는 순서",
        "intro": "...",
        "steps": (("출생일과 기준일을 먼저 확인", "..."), ...),
        "faqs": (("질문", "답변"), ...),
    },
}
```

Pass the matching record from `blog_category` and render it conditionally before the post grid. Do not change the category indexability rule, canonical URL, pagination, or ad behavior.

- [ ] **Step 4: Run the targeted test and verify GREEN**

Run the command from Step 2.

Expected: `OK`.

### Task 4: Verify quality threshold and regression suite

**Files:**
- Modify: `tests/test_content_quality_audit.py`

- [ ] **Step 1: Run the targeted regression test after Tasks 2 and 3**

Run the command from Step 2.

Expected: `OK`; repeated-sentence warnings are outside this task and remain non-blocking.

- [ ] **Step 2: Run the full suite and production-oriented checks**

```bash
env ADSENSE_REVIEW_MODE=true BLOG_PUBLIC_INDEXING_ENABLED=false COUPANG_PARTNERS_ENABLED=false /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests
git diff --check
```

Expected: all tests pass and no whitespace errors.

- [ ] **Step 3: Commit the completed work**

```bash
git add content/hub_pages.py content/blog/schema.py app.py templates/hub-detail.html templates/blog-category.html tests/test_public_pages.py tests/test_blog_discovery.py tests/test_content_quality_audit.py docs/superpowers/plans/2026-07-31-hub-content-enrichment.md
git commit -m "feat: enrich hub and category guidance"
```
