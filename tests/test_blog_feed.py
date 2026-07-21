from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET
from datetime import datetime
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

    def count(self):
        return len(self.posts)


class FakeSession:
    def __init__(self, posts):
        self.posts = posts

    def query(self, model):
        return FakeQuery(self.posts)

    def close(self):
        pass


def post_for(slug: str, post_id: int):
    article = app_module.BLOG_ARTICLE_BLUEPRINTS.get(slug)
    if article:
        from content.blog.rendering import render_article_content_html

    return SimpleNamespace(
        id=post_id,
        slug=slug,
        title=article["title"] if article else "레거시 글",
        excerpt=article["summary"] if article else "레거시 요약",
        content_html=(
            render_article_content_html(article)
            if article
            else f'<h2>{slug}</h2><p><a href="/age">AgeCalc 계산기</a> 전체 본문</p>'
        ),
        cover_image_url=article["thumbnail"] if article else None,
        status="published",
        published_at=datetime(2026, 7, post_id, 1, 0),
        created_at=datetime(2026, 6, post_id, 1, 0),
        updated_at=datetime(2026, 7, post_id, 2, 0),
        sources=[],
    )


class BlogFeedTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)

    def test_rss_is_404_during_adsense_review(self):
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", True):
            response = app.test_client().get("/rss.xml")

        self.assertEqual(404, response.status_code)

    def test_rss_cdata_escaping_preserves_literal_terminator(self):
        escaped = app_module._escape_rss_cdata("앞]]>뒤")

        self.assertEqual("앞]]]]><![CDATA[>뒤", escaped)

    def test_rss_contains_only_registered_current_published_posts(self):
        current = post_for("national-pension-receiving-age", 1)
        legacy = post_for("legacy-general-post", 2)
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession([current, legacy])), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            response = app.test_client().get("/rss.xml")

        self.assertEqual(200, response.status_code)
        self.assertEqual("application/rss+xml", response.mimetype)
        root = ET.fromstring(response.data)
        items = root.findall("./channel/item")
        self.assertEqual(1, len(items))
        self.assertEqual(
            "https://agecalc.cloud/blog/national-pension-receiving-age",
            items[0].findtext("link"),
        )
        self.assertIn("정상 노령연금 개시연령은 출생연도에 따라 만 61~65세입니다", response.get_data(as_text=True))
        self.assertNotIn("전체 본문", response.get_data(as_text=True))
        self.assertNotIn("legacy-general-post", response.get_data(as_text=True))
        namespaces = {"dc": "http://purl.org/dc/elements/1.1/"}
        self.assertEqual("AgeCalc 편집팀", items[0].findtext("dc:creator", namespaces=namespaces))
        self.assertEqual("2026-07-01T02:00:00+00:00", items[0].findtext("dc:date", namespaces=namespaces))
        self.assertNotIn('href="/blog/age-65-benefits-2026"', response.get_data(as_text=True))

    def test_public_detail_does_not_link_to_related_drafts(self):
        current = post_for("national-pension-receiving-age", 1)
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession([current])), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            response = app.test_client().get("/blog/national-pension-receiving-age")

        self.assertEqual(200, response.status_code)
        self.assertNotIn('href="/blog/age-65-benefits-2026"', response.get_data(as_text=True))

    def test_rss_checks_total_eligibility_before_limiting_to_twenty_items(self):
        posts = [post_for("national-pension-receiving-age", (index % 20) + 1) for index in range(25)]
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "BLOG_INDEX_MIN_POSTS", 21), mock.patch.object(
            app_module, "SessionLocal", return_value=FakeSession(posts)
        ), mock.patch.object(
            app_module, "_published_blog_count", return_value=25
        ):
            response = app.test_client().get("/rss.xml")

        self.assertEqual(200, response.status_code)
        self.assertEqual(20, len(ET.fromstring(response.data).findall("./channel/item")))

    def test_guides_sitemap_uses_same_filter_and_adds_qualified_categories(self):
        posts = [
            post_for("early-birth-school-grade-guide", 1),
            post_for("baby-months-calculation-guide", 2),
            post_for("parent-child-age-gap-guide", 3),
            post_for("2026-school-entry-birth-year", 4),
            post_for("legacy-general-post", 5),
        ]
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(posts)), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            response = app.test_client().get("/sitemaps/guides.xml")

        xml = response.get_data(as_text=True)
        self.assertEqual(200, response.status_code)
        self.assertIn("https://agecalc.cloud/blog/category/education-family", xml)
        self.assertIn("https://agecalc.cloud/blog/2026-school-entry-birth-year", xml)
        self.assertNotIn("legacy-general-post", xml)

    def test_blog_pages_advertise_rss_only_when_public_indexing_is_active(self):
        post = post_for("2026-man-age-guide", 1)
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession([post])), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ), mock.patch.object(app_module, "_published_blog_count", return_value=3):
            response = app.test_client().get("/blog")

        self.assertIn(
            '<link rel="alternate" type="application/rss+xml" title="AgeCalc 블로그 RSS" href="/rss.xml"',
            response.get_data(as_text=True),
        )


if __name__ == "__main__":
    unittest.main()
