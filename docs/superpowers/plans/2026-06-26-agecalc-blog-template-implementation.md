# AgeCalc Blog Template Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the public blog article experience around a structured, AdSense-safer editorial template and publish the first flagship post at `/blog/2026-man-age-guide`.

**Architecture:** Keep the existing `GeneratedPost` database model and `/blog/<slug>` route, but add a slug-based structured article registry that supplies deterministic render data for approved public posts. Refactor the public blog detail template to consume structured sections first and fall back to legacy `post.content_html` for older entries, preserving draft/review workflows.

**Tech Stack:** Flask, Jinja2 templates, SQLAlchemy models, unittest, existing AgeCalc CSS system

---

## File Structure

Planned files and responsibilities:

- Create: `content/blog_articles.py`
  - Structured article registry for curated public blog posts
  - Helper functions to resolve article sections by slug
  - Content definition for `2026-man-age-guide`

- Create: `scripts/seed_public_blog_posts.py`
  - Idempotent seeding/upsert script for curated public blog entries in `generated_posts`

- Modify: `app.py`
  - Extend `blog_detail`, `blog_list`, and helper context assembly for structured article rendering
  - Keep draft/review behavior intact

- Modify: `templates/blog-detail.html`
  - Replace the current mostly free-form article shell with section-driven rendering
  - Support FAQ, direct answer, example cards, comparison table, related tools, related articles, and page feedback

- Modify: `templates/blog-list.html`
  - Improve card rendering for curated structured posts without breaking legacy list behavior

- Modify: `static/css/style.css`
  - Add styles for new structured blog sections using existing section/card vocabulary

- Modify: `tests/test_public_pages.py`
  - Add rendering and regression tests for structured blog detail pages and list behavior

- Modify: `tests/test_adsense_preflight.py`
  - Verify the preflight still passes with blog hidden by default and stays compliant when curated public posts are present

- Modify: `docs/BLOG_WORKFLOW.md`
  - Document the curated public blog post path separately from draft/review automation

## Task 1: Add Structured Blog Article Registry

**Files:**
- Create: `content/blog_articles.py`
- Modify: `tests/test_public_pages.py`
- Test: `tests/test_public_pages.py`

- [ ] **Step 1: Write the failing tests for structured article resolution**

Add tests near the existing blog detail tests in `tests/test_public_pages.py`:

```python
    def test_structured_blog_article_registry_defines_flagship_man_age_post(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS, structured_blog_article_for_slug

        article = structured_blog_article_for_slug("2026-man-age-guide")

        self.assertIn("2026-man-age-guide", BLOG_ARTICLE_BLUEPRINTS)
        self.assertEqual("2026년 만나이 계산 기준 총정리", article["h1"])
        self.assertEqual("/age", article["primary_cta"]["path"])
        self.assertGreaterEqual(len(article["direct_answer_paragraphs"]), 3)
        self.assertGreaterEqual(len(article["example_cards"]), 3)
        self.assertGreaterEqual(len(article["faq_items"]), 3)
```

```python
    def test_structured_blog_article_registry_exposes_related_tools_and_articles(self):
        from content.blog_articles import structured_blog_article_for_slug

        article = structured_blog_article_for_slug("2026-man-age-guide")

        tool_paths = [tool["path"] for tool in article["related_tools"]]
        article_paths = [item["path"] for item in article["related_articles"]]

        self.assertIn("/age", tool_paths)
        self.assertIn("/age-comparison-table", tool_paths)
        self.assertIn("/birth-year-age-table", tool_paths)
        self.assertIn("/references", tool_paths)
        self.assertIn("/blog/birth-year-age-interpretation", article_paths)
        self.assertIn("/blog/early-birth-school-grade-guide", article_paths)
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_structured_blog_article_registry_defines_flagship_man_age_post \
  tests.test_public_pages.PublicPageTests.test_structured_blog_article_registry_exposes_related_tools_and_articles -v
```

Expected: `ImportError` or `ModuleNotFoundError` for `content.blog_articles`.

- [ ] **Step 3: Write the minimal structured article registry**

Create `content/blog_articles.py` with a single responsibility: define curated structured article data and a lookup helper.

Start with this shape:

```python
from __future__ import annotations

from copy import deepcopy


BLOG_ARTICLE_BLUEPRINTS = {
    "2026-man-age-guide": {
        "slug": "2026-man-age-guide",
        "title": "2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
        "h1": "2026년 만나이 계산 기준 총정리",
        "hero_summary": "2026년 기준 만나이 계산법과 생일 전후 예외를 한 번에 정리합니다.",
        "eyebrow": "해설 글",
        "primary_cta": {"label": "만나이 계산기 바로가기", "path": "/age"},
        "secondary_cta": {"label": "나이 비교표 보기", "path": "/age-comparison-table"},
        "direct_answer_title": "2026년 만나이 계산은 이렇게 보면 됩니다",
        "direct_answer_paragraphs": [
            "2026년 현재 만나이는 기준일 현재 생일이 지났는지에 따라 계산합니다.",
            "기본 공식은 기준연도에서 출생연도를 뺀 뒤, 아직 생일 전이면 한 살을 빼는 방식입니다.",
            "출생연도만 알면 정확한 단일 나이가 아니라 만나이 범위로 해석해야 하는 경우가 많습니다.",
            "정확한 값은 만나이 계산기에서, 다른 나이 체계 비교는 비교표에서 함께 확인하는 것이 가장 안전합니다.",
        ],
        "audience_items": [
            "공식 기준으로 현재 만나이를 확인하려는 사람",
            "출생연도만 알고 나이를 해석해야 하는 사람",
            "만나이와 연나이 차이를 한 번에 정리하려는 사람",
        ],
        "example_cards": [
            {"label": "사례 1", "title": "생일 전", "description": "1992년 10월 2일생은 2026년 생일 전까지 이전 만나이를 유지합니다."},
            {"label": "사례 2", "title": "생일 후", "description": "같은 출생일도 2026년 생일이 지나면 만나이가 한 살 올라갑니다."},
            {"label": "사례 3", "title": "출생연도만 아는 경우", "description": "1992년생처럼 생일을 모르면 현재 만나이는 범위로만 해석해야 합니다."},
        ],
        "comparison_rows": [
            {"label": "생년월일을 정확히 아는 경우", "standard": "만나이 계산기", "exception": "생일 전후 차이를 함께 확인"},
            {"label": "출생연도만 아는 경우", "standard": "출생년도별 나이표", "exception": "정확한 단일 만나이로 단정하지 않기"},
            {"label": "연나이와 비교가 필요한 경우", "standard": "만나이·연나이 비교표", "exception": "공적 기준과 생활 표현 구분"},
        ],
        "faq_items": [
            {"question": "2026년에도 공적 기준은 만나이인가요?", "answer": "네. 공적 기준은 원칙적으로 만나이로 확인하는 것이 안전합니다."},
            {"question": "출생연도만 알면 왜 정확한 만나이를 못 정하나요?", "answer": "생일이 지났는지 여부를 모르기 때문에 현재 시점에서 한 살 차이가 날 수 있습니다."},
            {"question": "생일 전에는 왜 한 살을 빼나요?", "answer": "만나이는 출생일이 돌아와야 한 살이 증가하는 방식이기 때문입니다."},
        ],
        "related_tools": [
            {"label": "만나이 계산기", "path": "/age", "summary": "생년월일 기준 현재 만나이 계산"},
            {"label": "만나이·연나이 비교표", "path": "/age-comparison-table", "summary": "나이 체계 차이 비교"},
            {"label": "출생년도별 나이표", "path": "/birth-year-age-table", "summary": "생일을 모를 때 범위 확인"},
            {"label": "계산 기준과 참고 자료", "path": "/references", "summary": "공식 기준과 참고 출처 확인"},
        ],
        "related_articles": [
            {"title": "출생연도만 알 때 나이를 해석하는 방법", "path": "/blog/birth-year-age-interpretation", "summary": "출생연도 기반 해석 순서"},
            {"title": "빠른년생은 지금 어떻게 봐야 하나", "path": "/blog/early-birth-school-grade-guide", "summary": "학년과 나이 기준 구분"},
        ],
    }
}


def structured_blog_article_for_slug(slug: str) -> dict[str, object] | None:
    blueprint = BLOG_ARTICLE_BLUEPRINTS.get(slug)
    if blueprint is None:
        return None
    return deepcopy(blueprint)
```

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_structured_blog_article_registry_defines_flagship_man_age_post \
  tests.test_public_pages.PublicPageTests.test_structured_blog_article_registry_exposes_related_tools_and_articles -v
```

Expected: both tests `ok`.

- [ ] **Step 5: Commit**

```bash
git add content/blog_articles.py tests/test_public_pages.py
git commit -m "feat: add structured public blog article registry"
```

## Task 2: Seed and Resolve the Flagship Public Blog Post

**Files:**
- Create: `scripts/seed_public_blog_posts.py`
- Modify: `app.py`
- Modify: `tests/test_public_pages.py`
- Test: `tests/test_public_pages.py`

- [ ] **Step 1: Write the failing tests for public blog detail resolution**

Add tests in `tests/test_public_pages.py`:

```python
    def test_blog_detail_uses_structured_article_sections_when_slug_is_curated(self):
        post = SimpleNamespace(
            id=1,
            title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
            slug="2026-man-age-guide",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>레거시 본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/2026-man-age-guide"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                structured_article=structured_blog_article_for_slug("2026-man-age-guide"),
            )

        self.assertIn('class="section-shell direct-answer"', html)
        self.assertIn("2026년 만나이 계산은 이렇게 보면 됩니다", html)
        self.assertIn("data-example-card", html)
        self.assertIn("만나이·연나이·출생연도 해석 비교", html)
```

```python
    def test_seed_public_blog_posts_upserts_flagship_article(self):
        from scripts.seed_public_blog_posts import build_seed_post_payload

        payload = build_seed_post_payload("2026-man-age-guide")

        self.assertEqual("2026-man-age-guide", payload["slug"])
        self.assertEqual("published", payload["status"])
        self.assertIn("2026년 만나이 계산 기준 총정리", payload["title"])
        self.assertIn("<h2>만나이는 무엇을 기준으로 계산하나</h2>", payload["content_html"])
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_blog_detail_uses_structured_article_sections_when_slug_is_curated \
  tests.test_public_pages.PublicPageTests.test_seed_public_blog_posts_upserts_flagship_article -v
```

Expected: failure because `structured_article` is ignored and `seed_public_blog_posts.py` does not exist.

- [ ] **Step 3: Add the seed script and route helper**

Create `scripts/seed_public_blog_posts.py` with a narrow contract:

```python
from __future__ import annotations

from datetime import datetime

from db import SessionLocal
from models.blog_models import GeneratedPost
from content.blog_articles import structured_blog_article_for_slug


def build_seed_post_payload(slug: str) -> dict[str, object]:
    article = structured_blog_article_for_slug(slug)
    if article is None:
        raise KeyError(slug)

    content_html = "".join(
        [
            "<section>",
            "<h2>만나이는 무엇을 기준으로 계산하나</h2>",
            "<p>만나이는 출생일이 지났는지 여부를 기준으로 계산합니다.</p>",
            "</section>",
            "<section>",
            "<h2>2026년에 결과가 달라지는 핵심은 생일 전후</h2>",
            "<p>생일 전과 후의 결과 차이를 먼저 확인해야 합니다.</p>",
            "</section>",
            "<section>",
            "<h2>이 경우는 바로 단정하면 틀리기 쉽습니다</h2>",
            "<p>출생연도만 아는 경우와 윤년 출생은 범위 또는 예외로 해석해야 합니다.</p>",
            "</section>",
        ]
    )

    return {
        "slug": article["slug"],
        "title": article["title"],
        "excerpt": article["hero_summary"],
        "content_html": content_html,
        "cover_image_url": None,
        "status": "published",
        "published_at": datetime.utcnow(),
    }
```

Add an idempotent upsert function in the same file:

```python
def upsert_seed_post(slug: str) -> GeneratedPost:
    payload = build_seed_post_payload(slug)
    session = SessionLocal()
    post = session.query(GeneratedPost).filter(GeneratedPost.slug == slug).first()
    if post is None:
        post = GeneratedPost(**payload)
        session.add(post)
    else:
        for field, value in payload.items():
            setattr(post, field, value)
    session.commit()
    session.refresh(post)
    session.close()
    return post
```

In `app.py`, add a small helper above `blog_detail`:

```python
from content.blog_articles import structured_blog_article_for_slug
```

```python
def _structured_blog_context(post) -> dict[str, object] | None:
    return structured_blog_article_for_slug(post.slug)
```

Then update `blog_detail` render context:

```python
        render_template(
            'blog-detail.html',
            post=post,
            draft_mode=False,
            review_mode=False,
            blog_indexable=blog_indexable,
            structured_article=_structured_blog_context(post),
        )
```

Keep draft and review routes passing `structured_article=_structured_blog_context(post)` too.

- [ ] **Step 4: Run the targeted tests to verify they pass**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_blog_detail_uses_structured_article_sections_when_slug_is_curated \
  tests.test_public_pages.PublicPageTests.test_seed_public_blog_posts_upserts_flagship_article -v
```

Expected: both tests `ok`.

- [ ] **Step 5: Commit**

```bash
git add scripts/seed_public_blog_posts.py app.py tests/test_public_pages.py
git commit -m "feat: seed and resolve flagship public blog post"
```

## Task 3: Refactor Public Blog Detail Template to Structured Sections

**Files:**
- Modify: `templates/blog-detail.html`
- Modify: `static/css/style.css`
- Modify: `tests/test_public_pages.py`
- Test: `tests/test_public_pages.py`

- [ ] **Step 1: Write the failing template tests**

Add tests in `tests/test_public_pages.py`:

```python
    def test_blog_detail_renders_structured_related_tools_and_related_articles(self):
        post = SimpleNamespace(
            title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
            slug="2026-man-age-guide",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/2026-man-age-guide"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                structured_article=structured_blog_article_for_slug("2026-man-age-guide"),
            )

        self.assertIn("AgeCalc에서 바로 확인하는 순서", html)
        self.assertIn("다음에 읽을 글", html)
        self.assertIn('href="/blog/birth-year-age-interpretation"', html)
        self.assertIn('href="/blog/early-birth-school-grade-guide"', html)
        self.assertIn('data-page-feedback="/blog/2026-man-age-guide"', html)
```

```python
    def test_blog_detail_uses_faqpage_schema_for_structured_articles(self):
        post = SimpleNamespace(
            title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
            slug="2026-man-age-guide",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/2026-man-age-guide"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                structured_article=structured_blog_article_for_slug("2026-man-age-guide"),
            )

        self.assertIn('"@type":"FAQPage"', html.replace(" ", ""))
        self.assertIn("2026년에도 공적 기준은 만나이인가요?", html)
```

- [ ] **Step 2: Run the targeted tests to verify they fail**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_blog_detail_renders_structured_related_tools_and_related_articles \
  tests.test_public_pages.PublicPageTests.test_blog_detail_uses_faqpage_schema_for_structured_articles -v
```

Expected: failures because the current template does not render these sections.

- [ ] **Step 3: Refactor `templates/blog-detail.html`**

Keep the draft/review controls, but branch public rendering around `structured_article`.

Use this render pattern:

```jinja2
{% set article = structured_article %}
...
{% if article %}
<section class="section-shell direct-answer" aria-label="{{ article.direct_answer_title }}">
    <div class="section-heading">
        <p class="eyebrow">바로 답변</p>
        <h2>{{ article.direct_answer_title }}</h2>
    </div>
    {% for paragraph in article.direct_answer_paragraphs %}
    <p>{{ paragraph }}</p>
    {% endfor %}
</section>

<section class="section-shell">
    <div class="section-heading">
        <p class="eyebrow">이런 분께</p>
        <h2>이 글이 필요한 사람</h2>
    </div>
    <ul>
        {% for item in article.audience_items %}
        <li>{{ item }}</li>
        {% endfor %}
    </ul>
</section>

<section class="section-shell">
    <div class="section-heading">
        <p class="eyebrow">사례</p>
        <h2>사례로 보면 더 빠릅니다</h2>
    </div>
    <div class="section-card-grid">
        {% for example in article.example_cards %}
        <article class="section-card" data-example-card>
            <p class="eyebrow">{{ example.label }}</p>
            <h3>{{ example.title }}</h3>
            <p>{{ example.description }}</p>
        </article>
        {% endfor %}
    </div>
</section>
{% endif %}
```

Add a comparison table, related tools section, related articles section, FAQ section, and page feedback partial.

Also add FAQ schema in `<head>` only when `structured_article` exists:

```jinja2
{% if structured_article and structured_article.faq_items %}
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"FAQPage","mainEntity":[...]}
</script>
{% endif %}
```

Keep fallback rendering:

```jinja2
{% if not structured_article %}
<div class="blog-content">{{ post.content_html | safe }}</div>
{% endif %}
```

- [ ] **Step 4: Add minimal styles for the new sections**

In `static/css/style.css`, add focused selectors only:

```css
.blog-article .section-shell {
  margin-top: 28px;
}

.blog-article .section-card-grid {
  margin-top: 16px;
}

.blog-related-articles .section-card,
.blog-related-tools .section-card {
  min-height: 100%;
}
```

Avoid introducing a separate visual language; reuse section/card primitives already used on calculators and guides.

- [ ] **Step 5: Run the targeted tests to verify they pass**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_blog_detail_renders_structured_related_tools_and_related_articles \
  tests.test_public_pages.PublicPageTests.test_blog_detail_uses_faqpage_schema_for_structured_articles -v
```

Expected: both tests `ok`.

- [ ] **Step 6: Commit**

```bash
git add templates/blog-detail.html static/css/style.css tests/test_public_pages.py
git commit -m "feat: refactor public blog detail into structured sections"
```

## Task 4: Improve Blog List and Document the Curated Public Workflow

**Files:**
- Modify: `templates/blog-list.html`
- Modify: `docs/BLOG_WORKFLOW.md`
- Modify: `tests/test_public_pages.py`
- Test: `tests/test_public_pages.py`

- [ ] **Step 1: Write the failing tests for blog list presentation**

Add tests in `tests/test_public_pages.py`:

```python
    def test_blog_list_surfaces_curated_editorial_positioning_copy(self):
        posts = [
            SimpleNamespace(
                slug="2026-man-age-guide",
                title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
                excerpt="2026년 기준 만나이 계산법과 생일 전후 예외를 한 번에 정리합니다.",
                cover_image_url=None,
                published_at=None,
            )
        ]

        with app.test_request_context("/blog"):
            html = render_template(
                "blog-list.html",
                posts=posts,
                total=1,
                page=1,
                total_pages=1,
                blog_indexable=True,
            )

        self.assertIn("계산기 결과를 해석하는 설명형 글", html)
        self.assertIn('href="/blog/2026-man-age-guide"', html)
```

- [ ] **Step 2: Run the targeted test to verify it fails**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_blog_list_surfaces_curated_editorial_positioning_copy -v
```

Expected: fail because the current list intro is still generic.

- [ ] **Step 3: Update the list copy and workflow documentation**

In `templates/blog-list.html`, tighten the hero intro so it explicitly matches the curated public strategy:

```jinja2
<p class="page-intro">
    계산기 결과를 해석하는 설명형 글만 선별해 공개합니다.
    현재 게시된 글은 {{ total }}개입니다.
</p>
```

In `docs/BLOG_WORKFLOW.md`, add a short section:

```md
## Curated Public Posts

Curated public blog posts are not published directly from raw generated drafts.
They must:

- map to a structured article blueprint
- pass the public quality checklist
- include direct answer, examples, FAQ, and source sections
- be seeded or updated through `scripts/seed_public_blog_posts.py`
```

- [ ] **Step 4: Run the targeted test to verify it passes**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_public_pages.PublicPageTests.test_blog_list_surfaces_curated_editorial_positioning_copy -v
```

Expected: `ok`.

- [ ] **Step 5: Commit**

```bash
git add templates/blog-list.html docs/BLOG_WORKFLOW.md tests/test_public_pages.py
git commit -m "docs: define curated public blog workflow"
```

## Task 5: Full Verification and Public Seed Run

**Files:**
- Modify: `tests/test_adsense_preflight.py`
- Test: `tests/test_adsense_preflight.py`
- Test: `tests/test_public_pages.py`

- [ ] **Step 1: Add a regression test for preflight after curated blog support**

In `tests/test_adsense_preflight.py`, add:

```python
    def test_local_preflight_still_passes_after_curated_blog_support(self):
        report = run_local_preflight()

        self.assertTrue(report.ok)
        self.assertEqual(0, report.content_quality_failures)
```

- [ ] **Step 2: Run the targeted preflight test to verify it passes**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest \
  tests.test_adsense_preflight.AdsensePreflightTests.test_local_preflight_still_passes_after_curated_blog_support -v
```

Expected: `ok`.

- [ ] **Step 3: Seed the flagship public post locally**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/seed_public_blog_posts.py
```

Expected: the script upserts `2026-man-age-guide` without duplicate row creation.

- [ ] **Step 4: Run the full verification suite**

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests
```

Expected: `OK`.

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/content_quality_audit.py
```

Expected: `PASS checked_pages=54 errors=0`.

Run:

```bash
/srv/apps/agecalc/.micromamba/envs/agecalc/bin/python scripts/adsense_preflight.py
```

Expected: `PASS checked_pages=54 sitemap_urls=54 quality_failures=0`.

Run:

```bash
git diff --check
```

Expected: no output.

- [ ] **Step 5: Commit**

```bash
git add tests/test_adsense_preflight.py
git commit -m "test: verify curated public blog support stays adsense-safe"
```

## Spec Coverage Check

Spec requirement to task mapping:

- reusable structured public blog template: Tasks 1, 2, 3
- first flagship article structure: Tasks 1, 2, 3
- Flask/Jinja component contract: Tasks 1, 2, 3
- curated publication workflow: Task 4
- AdSense-safe verification: Task 5

No intentional gaps remain.
