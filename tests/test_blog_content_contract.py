from __future__ import annotations

import copy
import hashlib
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace

from PIL import Image


class BlogContentContractTests(unittest.TestCase):
    def setUp(self):
        from content.blog_articles import structured_blog_article_for_slug

        self.valid_article = structured_blog_article_for_slug("2026-man-age-guide")
        self.assertIsNotNone(self.valid_article)

    def test_registry_contains_the_eight_priority_articles(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS, PRIORITY_ARTICLE_SLUGS

        self.assertEqual(
            (
                "2026-man-age-guide",
                "man-age-vs-korean-age",
                "2000-birth-year-age",
                "2026-school-entry-birth-year",
                "age-65-benefits-2026",
                "dog-age-calculation-guide",
                "national-pension-receiving-age",
                "2026-national-health-checkup-eligibility",
            ),
            PRIORITY_ARTICLE_SLUGS,
        )
        self.assertTrue(set(PRIORITY_ARTICLE_SLUGS).issubset(BLOG_ARTICLE_BLUEPRINTS))
        self.assertGreaterEqual(len(BLOG_ARTICLE_BLUEPRINTS), 12)

    def test_every_article_satisfies_the_shared_contract(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS
        from content.blog.schema import validate_article_registry

        validate_article_registry(BLOG_ARTICLE_BLUEPRINTS, today=date(2026, 7, 22))

    def test_contract_requires_editorial_metadata(self):
        from content.blog.schema import ContentContractError, validate_article_registry

        article = copy.deepcopy(self.valid_article)
        del article["reviewed_at"]

        with self.assertRaisesRegex(ContentContractError, "reviewed_at"):
            validate_article_registry({article["slug"]: article}, today=date(2026, 7, 22))

    def test_contract_rejects_duplicate_article_slugs(self):
        from content.blog.schema import ContentContractError, validate_article_registry

        first = copy.deepcopy(self.valid_article)
        second = copy.deepcopy(self.valid_article)
        second["title"] = "중복 slug 글"

        with self.assertRaisesRegex(ContentContractError, "registry key"):
            validate_article_registry(
                {"first-key": first, "second-key": second},
                today=date(2026, 7, 22),
            )

    def test_registry_merge_rejects_collisions_before_dictionary_overwrite(self):
        from content.blog.schema import ContentContractError, merge_article_registries

        article = copy.deepcopy(self.valid_article)
        slug = article["slug"]

        with self.assertRaisesRegex(ContentContractError, "duplicate article slug"):
            merge_article_registries({slug: article}, {slug: copy.deepcopy(article)})

    def test_contract_rejects_invalid_date_order(self):
        from content.blog.schema import ContentContractError, validate_article_registry

        article = copy.deepcopy(self.valid_article)
        article["effective_date"] = "2026-08-01"
        article["expires_at"] = "2026-07-01"

        with self.assertRaisesRegex(ContentContractError, "expires_at"):
            validate_article_registry({article["slug"]: article}, today=date(2026, 7, 22))

    def test_contract_requires_https_named_sources(self):
        from content.blog.schema import ContentContractError, validate_article_registry

        article = copy.deepcopy(self.valid_article)
        article["source_urls"] = [
            {
                "organization": "국가기관",
                "title": "기준 문서",
                "url": "http://example.com/source",
                "checked_at": "2026-07-21",
            }
        ]

        with self.assertRaisesRegex(ContentContractError, "HTTPS"):
            validate_article_registry({article["slug"]: article}, today=date(2026, 7, 22))

    def test_contract_rejects_unverified_source_hosts_and_string_booleans(self):
        from content.blog.schema import ContentContractError, validate_article_registry

        unverified = copy.deepcopy(self.valid_article)
        unverified["source_urls"][0]["url"] = "https://example.com/looks-official"
        with self.assertRaisesRegex(ContentContractError, "official institution"):
            validate_article_registry({unverified["slug"]: unverified}, today=date(2026, 7, 22))

        string_boolean = copy.deepcopy(self.valid_article)
        string_boolean["is_indexable"] = "false"
        with self.assertRaisesRegex(ContentContractError, "must be a boolean"):
            validate_article_registry({string_boolean["slug"]: string_boolean}, today=date(2026, 7, 22))

    def test_structured_body_changes_require_a_new_approved_snapshot(self):
        from content.blog.rendering import render_article_content_html
        from scripts.adsense_blog_review import audit_post

        approved = render_article_content_html(self.valid_article)
        changed = copy.deepcopy(self.valid_article)
        changed["content_sections"][0]["paragraphs"].append("승인 뒤 추가된 변경 문장입니다.")
        post = SimpleNamespace(
            id=1,
            slug=changed["slug"],
            title=changed["title"],
            content_html=approved,
            cover_image_url=changed["thumbnail"],
            status="published",
            sources=[],
        )

        result = audit_post(
            post,
            require_cover_image=True,
            article_registry={changed["slug"]: changed},
            today=date(2026, 7, 22),
        )

        self.assertFalse(result.keep)
        self.assertIn("content_snapshot_mismatch", result.issue_codes)

    def test_structured_public_metadata_changes_require_a_new_approved_snapshot(self):
        from content.blog.rendering import render_article_content_html
        from scripts.adsense_blog_review import audit_post

        changed = copy.deepcopy(self.valid_article)
        changed["title"] = "승인 뒤 바뀐 제목"
        post = SimpleNamespace(
            id=1,
            slug=changed["slug"],
            title=self.valid_article["title"],
            excerpt=changed["summary"],
            content_html=render_article_content_html(changed),
            cover_image_url=changed["thumbnail"],
            status="published",
            sources=[],
        )

        result = audit_post(
            post,
            require_cover_image=True,
            article_registry={changed["slug"]: changed},
            today=date(2026, 7, 22),
        )

        self.assertFalse(result.keep)
        self.assertIn("content_snapshot_mismatch", result.issue_codes)

    def test_contract_rejects_broken_related_article_links(self):
        from content.blog.schema import ContentContractError, validate_article_registry

        article = copy.deepcopy(self.valid_article)
        article["related_articles"] = [
            {"title": "없는 글", "path": "/blog/not-registered", "summary": "끊어진 링크"}
        ]

        with self.assertRaisesRegex(ContentContractError, "related article"):
            validate_article_registry({article["slug"]: article}, today=date(2026, 7, 22))

    def test_contract_rejects_unknown_calculator_and_cta_paths(self):
        from content.blog.schema import ContentContractError, validate_article_registry

        broken_tool = copy.deepcopy(self.valid_article)
        broken_tool["related_tools"][0]["path"] = "/does-not-exist"
        broken_tool["related_calculators"] = broken_tool["related_tools"]
        with self.assertRaisesRegex(ContentContractError, "internal path"):
            validate_article_registry({broken_tool["slug"]: broken_tool}, today=date(2026, 7, 22))

        broken_cta = copy.deepcopy(self.valid_article)
        broken_cta["primary_cta"]["path"] = "/does-not-exist"
        with self.assertRaisesRegex(ContentContractError, "internal path"):
            validate_article_registry({broken_cta["slug"]: broken_cta}, today=date(2026, 7, 22))

    def test_contract_marks_policy_and_health_content_with_a_future_expiry(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS

        today = date(2026, 7, 22)
        regulated_categories = {"policy-benefits", "health"}
        regulated = [
            article
            for article in BLOG_ARTICLE_BLUEPRINTS.values()
            if article["category"] in regulated_categories
        ]

        self.assertGreaterEqual(len(regulated), 3)
        for article in regulated:
            with self.subTest(slug=article["slug"]):
                self.assertGreater(date.fromisoformat(article["expires_at"]), today)
                self.assertEqual("AgeCalc 편집책임자", article["review_owner"])

    def test_all_twelve_articles_record_the_current_full_editorial_review(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS

        self.assertEqual(12, len(BLOG_ARTICLE_BLUEPRINTS))
        generic_homepages = {
            "https://www.bokjiro.go.kr/",
            "https://www.gov.kr/",
            "https://www.law.go.kr/법령/민법",
            "https://www.law.go.kr/법령/초·중등교육법",
            "https://www.moe.go.kr/",
            "https://www.nhis.or.kr/",
        }
        for slug, article in BLOG_ARTICLE_BLUEPRINTS.items():
            with self.subTest(slug=slug):
                self.assertEqual("2026-07-22", article["reviewed_at"])
                self.assertTrue(article["source_urls"])
                for source in article["source_urls"]:
                    self.assertEqual("2026-07-22", source["checked_at"])
                    self.assertNotIn(source["url"], generic_homepages)

    def test_contract_uses_stable_canonical_and_local_thumbnail(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS

        thumbnails = set()
        for slug, article in BLOG_ARTICLE_BLUEPRINTS.items():
            with self.subTest(slug=slug):
                self.assertEqual(
                    f"https://agecalc.cloud/blog/{slug}",
                    article["canonical_url"],
                )
                self.assertEqual(f"/static/images/blog/{slug}.jpg", article["thumbnail"])
                self.assertTrue(article["thumbnail_alt"].strip())
                thumbnails.add(article["thumbnail"])
        self.assertEqual(len(BLOG_ARTICLE_BLUEPRINTS), len(thumbnails))

    def test_every_article_has_a_unique_optimized_social_cover(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS

        project_root = Path(__file__).resolve().parents[1]
        digests = set()
        for slug in BLOG_ARTICLE_BLUEPRINTS:
            with self.subTest(slug=slug):
                cover = project_root / "static" / "images" / "blog" / f"{slug}.jpg"
                self.assertTrue(cover.is_file())
                self.assertLess(cover.stat().st_size, 500_000)
                with Image.open(cover) as image:
                    self.assertEqual((1200, 630), image.size)
                    self.assertEqual("RGB", image.mode)
                    self.assertEqual("JPEG", image.format)
                digests.add(hashlib.sha256(cover.read_bytes()).hexdigest())
        self.assertEqual(len(BLOG_ARTICLE_BLUEPRINTS), len(digests))

    def test_seed_payloads_are_audit_ready_drafts(self):
        from content.blog_articles import PRIORITY_ARTICLE_SLUGS
        from scripts.adsense_blog_review import audit_post
        from scripts.seed_public_blog_posts import build_seed_post_payload, seed_sources_for_slug

        for slug in PRIORITY_ARTICLE_SLUGS:
            with self.subTest(slug=slug):
                payload = build_seed_post_payload(slug)
                sources = [SimpleNamespace(**source) for source in seed_sources_for_slug(slug)]
                post = SimpleNamespace(id=None, sources=sources, **payload)
                result = audit_post(post, require_cover_image=True)

                self.assertEqual("draft", payload["status"])
                self.assertIsNone(payload["published_at"])
                self.assertTrue(payload["cover_image_url"].startswith("/static/"))
                self.assertTrue(result.keep, result.issues)

    def test_structured_sources_make_real_seed_rows_publishable_without_rss_links(self):
        from scripts.adsense_blog_review import audit_post
        from scripts.seed_public_blog_posts import build_seed_post_payload

        payload = build_seed_post_payload("national-pension-receiving-age")
        post = SimpleNamespace(id=None, sources=[], **payload)

        result = audit_post(post, require_cover_image=True)

        self.assertTrue(result.keep, result.issues)
        self.assertNotIn("missing_sources", result.issue_codes)

    def test_seed_main_includes_all_structured_articles_without_publishing(self):
        from unittest import mock

        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS
        from scripts import seed_public_blog_posts

        with mock.patch.object(seed_public_blog_posts, "upsert_seed_post") as upsert_seed_post:
            seeded = seed_public_blog_posts.main()

        self.assertEqual(list(BLOG_ARTICLE_BLUEPRINTS), seeded)
        self.assertEqual(len(BLOG_ARTICLE_BLUEPRINTS), upsert_seed_post.call_count)


if __name__ == "__main__":
    unittest.main()
