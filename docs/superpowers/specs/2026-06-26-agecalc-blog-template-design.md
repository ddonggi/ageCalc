# AgeCalc Blog Template Design

Date: 2026-06-26
Status: approved draft
Scope: public blog article structure for AdSense-safe, calculator-connected editorial posts

## Goal

Define a production-ready blog article format for AgeCalc that:

- supports AdSense approval better than the current free-form blog article layout
- reinforces the site's calculator-first information architecture
- provides independent editorial value beyond calculator result pages
- can be implemented within the current Flask/Jinja codebase with minimal structural risk

This design covers:

- the first flagship article, `2026-man-age-guide`
- the reusable public blog template structure
- the component contract needed in Flask templates and route context

This design does not cover:

- the full implementation task breakdown
- migration of legacy blog posts
- automated article generation workflow changes

## Current State

Current public blog detail pages use [templates/blog-detail.html](/srv/apps/agecalc/.worktrees/life-platform-checkpoint-1/templates/blog-detail.html) and primarily render:

- a simple article header
- `post.content_html`
- source links
- a fixed "같이 보면 좋은 계산기" block

This is functional, but weak for approval-oriented editorial content because:

- there is no required `direct-answer` block
- the article body is mostly unconstrained free-form HTML
- examples, comparison tables, FAQs, and related article links are not structurally enforced
- internal linking depth is weaker than the calculator and guide templates

The existing guide template in [templates/guide-detail.html](/srv/apps/agecalc/.worktrees/life-platform-checkpoint-1/templates/guide-detail.html) already contains patterns that align better with the quality model established elsewhere on the site:

- `section-shell direct-answer`
- example cards via `data-example-card`
- comparison tables
- FAQ block
- footer-driven editorial metadata and related paths

## Design Decision

Recommended approach:

Adopt a hybrid blog article format that keeps the existing blog route and article model, but restructures the public template to behave more like an editorial landing page than a raw article container.

Why this approach:

- It reuses already-verified quality patterns from calculators and guides.
- It avoids inventing a second visual language for long-form content.
- It creates consistent review standards for future public blog posts.
- It allows gradual rollout starting with a small number of high-value articles.

Rejected alternatives:

1. Keep the current free-form blog template and only improve writing quality.
Reason: too much quality variance, weak structural guarantees, higher review risk.

2. Publish blog posts as additional static guide pages instead of blog posts.
Reason: this would blur the distinction between evergreen guides and editorial explanation pieces, and would create avoidable duplication with the guide system.

## Information Architecture

Each public blog article should act as a calculator-connected editorial node.

Required content flow:

1. answer the question immediately
2. explain the core rule
3. cover common exceptions
4. show 2 to 3 practical examples
5. direct users into the correct calculator flow
6. support the answer with sources
7. keep users moving through the same topic cluster

Minimum internal link contract per article:

- 2 calculator links
- 1 guide or references link
- 2 same-cluster blog/article links

## Flagship Article Specification

Target article:

- slug: `2026-man-age-guide`
- title: `2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리`
- h1: `2026년 만나이 계산 기준 총정리`

### Required Section Order

1. Hero

- eyebrow: `해설 글`
- h1
- one-line summary
- authored/reviewed/updated information
- primary CTA: `/age`
- secondary CTA: `/age-comparison-table`

2. Direct Answer

- h2: `2026년 만나이 계산은 이렇게 보면 됩니다`
- 3 to 5 sentences
- must include:
  - the core rule
  - the birthday-before/after distinction
  - the limitation of birth-year-only interpretation
  - calculator handoff

3. Who This Is For

- 3 audience bullets:
  - users comparing official age vs daily usage
  - users who only know a birth year
  - users confused by birthday timing

4. Core Rule Explanation

- h2: `만나이는 무엇을 기준으로 계산하나`
- h2: `2026년에 결과가 달라지는 핵심은 생일 전후`

5. Common Exceptions

- h2: `이 경우는 바로 단정하면 틀리기 쉽습니다`
- must include:
  - birth year only
  - leap day birth
  - lunar birthday memory vs official handling
  - mixing official age and conversational age

6. Example Cards

- 3 cards:
  - pre-birthday case
  - post-birthday case
  - birth-year-only case

7. Comparison Table

- h2: `만나이·연나이·출생연도 해석 비교`
- columns:
  - 확인 상황
  - 가장 안전한 기준
  - 같이 봐야 할 계산기

8. Tool Flow

- h2: `AgeCalc에서 바로 확인하는 순서`
- sequence:
  - `/age`
  - `/age-comparison-table`
  - `/birth-year-age-table`
  - `/references`

9. FAQ

- 3 entries minimum

10. Sources

- official or primary references
- AgeCalc references page

11. Next Reading

- links to:
  - `/blog/birth-year-age-interpretation`
  - `/blog/early-birth-school-grade-guide`

### Content Length Target

- minimum: 2,200 visible characters
- preferred range: 2,200 to 3,200 visible characters

## Template Component Specification

The public blog template should be rebuilt as a component-driven layout rather than a single `post.content_html` shell.

### 1. `blog_article_header`

Purpose:

- deliver search intent, trust metadata, and primary CTA above the fold

Required fields:

- `post.title`
- `post.excerpt`
- `post.published_at` or `post.created_at`
- `post.updated_at`
- `hero_summary`
- `primary_cta`
- `secondary_cta`

### 2. `blog_direct_answer`

Purpose:

- guarantee immediate answer visibility and satisfy content quality expectations

Required fields:

- `direct_answer_title`
- `direct_answer_paragraphs[]`

Markup requirement:

- must use `section-shell direct-answer`

### 3. `blog_audience_box`

Purpose:

- clarify who benefits from the article and reduce generic-intro fluff

Required fields:

- `audience_items[]`

### 4. `blog_example_cards`

Purpose:

- provide practical interpretation value, not just theory

Required fields:

- `example_cards[]`
  - `label`
  - `title`
  - `description`

Markup requirement:

- cards should use `data-example-card`

### 5. `blog_comparison_table`

Purpose:

- compare baseline rules and exceptions in a scan-friendly structure

Required fields:

- `comparison_rows[]`
  - `label`
  - `standard`
  - `exception`

### 6. `blog_related_tools`

Purpose:

- replace the current hard-coded calculator list with topic-specific links

Required fields:

- `related_tools[]`
  - `label`
  - `path`
  - `summary`

### 7. `blog_faq`

Purpose:

- support lower-funnel search intent and allow structured FAQ rendering

Required fields:

- `faq_items[]`
  - `question`
  - `answer`

### 8. `blog_sources`

Purpose:

- preserve source transparency and make why-each-source-matters more explicit

Required fields:

- existing `post.sources`
- optional `source_notes[]` or per-source explanation

### 9. `blog_related_articles`

Purpose:

- prevent orphan editorial pages and build cluster navigation

Required fields:

- `related_articles[]`
  - `title`
  - `slug`
  - `summary`

### 10. `blog_feedback`

Purpose:

- collect page usefulness signals for editorial iteration

Implementation note:

- reuse [templates/partials/page-feedback.html](/srv/apps/agecalc/.worktrees/life-platform-checkpoint-1/templates/partials/page-feedback.html)

## Data Contract

Current public blog detail rendering is too dependent on unconstrained `post.content_html`.

Recommended hybrid contract:

- keep `post.content_html` for the long-form body
- add structured fields for repeated editorial blocks

Preferred article context fields:

- `hero_summary`
- `direct_answer_title`
- `direct_answer_paragraphs`
- `audience_items`
- `example_cards`
- `comparison_rows`
- `faq_items`
- `related_tools`
- `related_articles`
- `source_notes`

This should be treated as a rendering contract at the route/template layer, even if the persistence layer evolves in stages.

## Rendering Strategy

Recommended implementation path:

1. extend the blog detail render context in [app.py](/srv/apps/agecalc/.worktrees/life-platform-checkpoint-1/app.py:1763)
2. refactor [templates/blog-detail.html](/srv/apps/agecalc/.worktrees/life-platform-checkpoint-1/templates/blog-detail.html) to match the guide/calculator quality patterns
3. keep draft/review behavior intact
4. make public blog article sections data-driven, not hard-coded

Important constraint:

- public blog pages should not diverge from the site's established editorial trust blocks
- they should continue inheriting footer-level `related-paths` and `editorial-meta`

## Quality Gates

Before a blog post is made public, it should pass all of the following:

- direct answer present above the fold
- at least 3 H2 sections
- at least 2 practical examples
- at least 2 calculator/internal links
- sources present
- independent explanatory value beyond calculator output
- no obvious duplication with guides or calculators
- no thin summary-only body

For the flagship article specifically:

- direct answer must mention birthday timing
- examples must cover pre-birthday, post-birthday, and birth-year-only interpretation
- related tools must include `/age`, `/age-comparison-table`, `/birth-year-age-table`, `/references`

## Risks

1. Half-structured adoption

If the template is improved but the route context remains mostly free-form, article quality will drift quickly.

Mitigation:

- enforce a structured render context for all public blog articles

2. Guide/blog duplication

If blog posts repeat guide copy too closely, the site will add URLs without adding value.

Mitigation:

- position blog content as interpretation + examples
- position guides as evergreen rule/reference content

3. Premature public rollout

Publishing one or two improved posts while the rest remain weak or hidden creates an inconsistent quality signal.

Mitigation:

- release a small but complete cluster of high-quality public posts together

## Recommendation

Proceed with:

- one implementation batch for the reusable public blog template
- one flagship article implementation batch for `2026-man-age-guide`

Do not reopen the public blog index broadly until the first cluster of 8 to 12 posts meets the same structure and quality standard.
