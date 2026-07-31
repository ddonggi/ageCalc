from __future__ import annotations

import copy
import unittest
from datetime import date, datetime
from types import SimpleNamespace
from unittest import mock

import app as app_module


app = app_module.app


class FakeQuery:
    def __init__(self, posts):
        self.posts = posts

    def filter(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        return self.posts

    def first(self):
        return self.posts[0] if self.posts else None


class FakeSession:
    def __init__(self, posts):
        self.posts = posts

    def query(self, model):
        return FakeQuery(self.posts)

    def close(self):
        pass


def make_post(slug: str, post_id: int = 1):
    article = app_module.BLOG_ARTICLE_BLUEPRINTS[slug]
    from content.blog.rendering import render_article_content_html

    return SimpleNamespace(
        id=post_id,
        slug=slug,
        title=article["title"],
        excerpt=article["summary"],
        content_html=render_article_content_html(article),
        cover_image_url=article["thumbnail"],
        status="published",
        published_at=datetime(2026, 7, 1, 1, 0),
        created_at=datetime(2026, 6, 30, 1, 0),
        updated_at=datetime(2026, 7, 20, 1, 0),
        sources=[],
    )


class BlogDiscoveryTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)

    def test_public_slug_filter_excludes_expired_and_nonindexable_articles(self):
        active = copy.deepcopy(app_module.BLOG_ARTICLE_BLUEPRINTS["2026-man-age-guide"])
        expired = copy.deepcopy(app_module.BLOG_ARTICLE_BLUEPRINTS["man-age-vs-korean-age"])
        hidden = copy.deepcopy(app_module.BLOG_ARTICLE_BLUEPRINTS["2000-birth-year-age"])
        expired["expires_at"] = "2026-07-21"
        hidden["is_indexable"] = False

        with mock.patch.object(
            app_module,
            "BLOG_ARTICLE_BLUEPRINTS",
            {active["slug"]: active, expired["slug"]: expired, hidden["slug"]: hidden},
        ):
            slugs = app_module._eligible_public_blog_slugs(today=date(2026, 7, 21))

        self.assertEqual(("2026-man-age-guide",), slugs)

    def test_unknown_category_returns_404(self):
        response = app.test_client().get("/blog/category/not-a-category")

        self.assertEqual(404, response.status_code)

    def test_category_with_fewer_than_three_posts_is_noindex(self):
        posts = [make_post("2026-man-age-guide", 1), make_post("man-age-vs-korean-age", 2)]
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(posts)), mock.patch.object(
            app_module, "_published_blog_count", return_value=3
        ):
            response = app.test_client().get("/blog/category/age?page=1")

        html = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn('<meta name="robots" content="noindex,follow"', html)
        self.assertIn('<link rel="canonical" href="https://agecalc.cloud/blog/category/age"', html)
        self.assertNotIn("pagead/js/adsbygoogle.js", html)
        self.assertNotIn("google-adsense-account", html)

    def test_category_with_three_posts_can_be_indexed(self):
        posts = [
            make_post("2026-man-age-guide" if index % 2 else "man-age-vs-korean-age", index)
            for index in range(1, 10)
        ]
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(posts)), mock.patch.object(
            app_module, "_published_blog_count", return_value=9
        ):
            response = app.test_client().get("/blog/category/age?page=2")

        html = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertNotIn('content="noindex,follow"', html)
        self.assertIn(
            '<link rel="canonical" href="https://agecalc.cloud/blog/category/age?page=2"',
            html,
        )

    def test_education_family_category_renders_editorial_usage_guide(self):
        posts = [
            make_post("early-birth-school-grade-guide", 1),
            make_post("baby-months-calculation-guide", 2),
            make_post("parent-child-age-gap-guide", 3),
        ]

        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(posts)), mock.patch.object(
            app_module, "_published_blog_count", return_value=3
        ):
            response = app.test_client().get("/blog/category/education-family")

        html = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("blog-category-usage-guide", html)
        self.assertIn("학교·육아 정보를 확인하는 순서", html)
        self.assertIn("출생일과 기준일을 먼저 확인", html)
        self.assertIn("학교와 기관의 실제 기준도 확인", html)
        self.assertIn("자주 묻는 질문", html)

    def test_blog_detail_renders_twitter_article_schema_and_category_breadcrumb(self):
        post = make_post("national-pension-receiving-age")
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession([post])), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            response = app.test_client().get("/blog/national-pension-receiving-age")

        html = response.get_data(as_text=True).replace(" ", "")
        self.assertEqual(200, response.status_code)
        self.assertIn('name="twitter:card"content="summary_large_image"', html)
        self.assertIn('"@type":"BlogPosting"', html)
        self.assertIn('"datePublished":"2026-07-01T10:00:00+09:00"', html)
        self.assertIn('href="/blog/category/policy-benefits"', html)
        self.assertEqual(1, html.count('"@type":"BreadcrumbList"'))
        self.assertIn("기준일", html)
        self.assertIn("재검수기한", html)

    def test_public_detail_rejects_stale_db_snapshot(self):
        post = make_post("national-pension-receiving-age")
        post.title = "STALE DB TITLE"
        post.excerpt = "STALE DB EXCERPT"
        post.cover_image_url = "/static/generated/stale.png"
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession([post])), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            response = app.test_client().get("/blog/national-pension-receiving-age")

        self.assertEqual(404, response.status_code)


if __name__ == "__main__":
    unittest.main()
