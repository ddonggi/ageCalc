import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest import mock

import app as app_module
import scripts.content_quality_audit as audit_module

from scripts.content_quality_audit import (
    ContentQualityReport,
    audit_html,
    audit_local_pages,
    format_json,
    format_text,
)


RICH_HTML = """
<!doctype html>
<html lang="ko">
<head>
  <title>고유한 나이 계산 안내</title>
  <meta name="description" content="생년월일을 기준으로 나이를 계산하고 예외와 다음 행동을 자세히 설명합니다.">
  <link rel="canonical" href="https://agecalc.cloud/example">
</head>
<body>
  <h1>고유한 나이 계산 안내</h1>
  <p class="direct-answer">생일이 지났으면 기준연도에서 출생연도를 뺀 값이 현재 만나이입니다.</p>
  <h2>계산 공식</h2><p>기준연도와 출생연도, 생일 전후를 순서대로 비교합니다.</p>
  <h2>실제 사례</h2><p>서로 다른 날짜 사례를 통해 결과가 달라지는 이유를 확인합니다.</p>
  <h2>예외와 다음 행동</h2><p>윤년과 공식 제출 상황에서는 기관 기준일도 함께 확인합니다.</p>
  <aside class="related-paths"><a href="/age">관련 도구</a></aside>
  <aside class="editorial-meta">
    <li data-official-source="true"><a href="https://example.go.kr">공식 출처</a></li>
    <p class="editorial-disclaimer">공식 판단이나 진단을 대신하지 않습니다.</p>
  </aside>
</body>
</html>
"""


class ContentQualityAuditTests(unittest.TestCase):
    def test_audit_html_requires_core_editorial_elements(self):
        html = """
        <html><head><title>짧은 페이지</title></head>
        <body><h1>짧은 페이지</h1><h2>한 개 섹션</h2><p>설명</p></body></html>
        """

        result = audit_html("/thin", html, ymyl=False)
        codes = {issue.code for issue in result.issues}

        self.assertIn("canonical_missing", codes)
        self.assertIn("description_missing", codes)
        self.assertIn("direct_answer_missing", codes)
        self.assertIn("insufficient_h2", codes)
        self.assertIn("editorial_meta_missing", codes)
        self.assertIn("related_paths_missing", codes)
        self.assertIn("thin_content_warning", codes)
        self.assertFalse(result.passed)

    def test_audit_html_requires_official_source_and_disclaimer_for_ymyl(self):
        html = RICH_HTML.replace('data-official-source="true"', 'data-official-source="false"').replace(
            '<p class="editorial-disclaimer">공식 판단이나 진단을 대신하지 않습니다.</p>',
            "",
        )

        result = audit_html("/ymyl", html, ymyl=True)
        codes = {issue.code for issue in result.issues}

        self.assertIn("official_source_missing", codes)
        self.assertIn("ymyl_disclaimer_missing", codes)
        self.assertFalse(result.passed)

    def test_thin_content_is_warning_only(self):
        result = audit_html("/rich-structure", RICH_HTML, ymyl=True)

        self.assertTrue(result.passed)
        self.assertIn(
            "thin_content_warning",
            {issue.code for issue in result.warnings},
        )

    def test_indexable_blog_article_requires_article_schema(self):
        without_schema = audit_html("/blog/example", RICH_HTML, ymyl=False)
        with_schema = audit_html(
            "/blog/example",
            RICH_HTML.replace(
                "</head>",
                '<script type="application/ld+json">{"@type":"BlogPosting"}</script></head>',
            ),
            ymyl=False,
        )

        self.assertIn("article_schema_missing", {issue.code for issue in without_schema.errors})
        self.assertNotIn("article_schema_missing", {issue.code for issue in with_schema.errors})

    def test_trust_pages_are_exempt_from_thin_content_warning(self):
        result = audit_html("/about", RICH_HTML, ymyl=False)

        self.assertNotIn(
            "thin_content_warning",
            {issue.code for issue in result.warnings},
        )

    def test_report_detects_duplicate_metadata_and_repeated_sentences(self):
        report = ContentQualityReport()
        report.add(audit_html("/one", RICH_HTML, ymyl=True))
        report.add(audit_html("/two", RICH_HTML, ymyl=True))
        report.detect_duplicates()

        warning_codes = {
            issue.code
            for result in report.results
            for issue in result.warnings
        }
        self.assertIn("duplicate_title_warning", warning_codes)
        self.assertIn("duplicate_description_warning", warning_codes)
        self.assertIn("duplicate_h1_warning", warning_codes)
        self.assertIn("repeated_sentence_warning", warning_codes)

    def test_text_and_json_formats_include_summary_and_issues(self):
        report = ContentQualityReport()
        report.add(audit_html("/thin", "<h1>얇은 페이지</h1>", ymyl=False))

        text = format_text(report)
        payload = json.loads(format_json(report))

        self.assertIn("[content-quality]", text)
        self.assertIn("direct_answer_missing", text)
        self.assertEqual(1, payload["checked_pages"])
        self.assertFalse(payload["ok"])

    def test_local_audit_can_filter_paths_and_hubs(self):
        path_report = audit_local_pages(paths=("/age",))
        hub_report = audit_local_pages(hub="age")

        self.assertEqual(["/age"], [result.path for result in path_report.results])
        self.assertGreaterEqual(len(hub_report.results), 5)
        self.assertTrue(all(result.hub == "age" for result in hub_report.results))

    def test_all_indexable_local_pages_pass_content_quality_errors(self):
        report = audit_local_pages()
        failing = {
            result.path: [issue.code for issue in result.errors]
            for result in report.results
            if result.errors
        }

        self.assertEqual({}, failing)

    def test_review_mode_audit_covers_only_46_approval_pages(self):
        report = audit_local_pages()

        self.assertEqual(46, len(report.results))
        self.assertEqual(0, report.error_count)
        self.assertEqual(0, report.warning_count)
        self.assertFalse(any(result.path.endswith("/") and result.path != "/" for result in report.results))

    def test_public_mode_audit_includes_dynamic_ymyl_blog_articles(self):
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

        article = app_module.BLOG_ARTICLE_BLUEPRINTS["national-pension-receiving-age"]
        def make_post(slug, post_id):
            from content.blog.rendering import render_article_content_html

            structured = app_module.BLOG_ARTICLE_BLUEPRINTS[slug]
            return SimpleNamespace(
                id=post_id,
                slug=slug,
                title=structured["title"],
                excerpt=structured["summary"],
                content_html=render_article_content_html(structured),
                cover_image_url=structured["thumbnail"],
                status="published",
                published_at=datetime(2026, 7, 1, 1, 0),
                created_at=datetime(2026, 7, 1, 1, 0),
                updated_at=datetime(2026, 7, 20, 1, 0),
                sources=[],
            )

        posts = [
            make_post("national-pension-receiving-age", 1),
            make_post("early-birth-school-grade-guide", 2),
            make_post("baby-months-calculation-guide", 3),
            make_post("parent-child-age-gap-guide", 4),
            make_post("2026-school-entry-birth-year", 5),
        ]

        with mock.patch.object(audit_module, "_auditable_pages", return_value=()), mock.patch.object(
            app_module, "ADSENSE_REVIEW_MODE", False
        ), mock.patch.object(app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True), mock.patch.object(
            app_module, "SessionLocal", return_value=FakeSession(posts)
        ), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            report = audit_local_pages()

        paths = [result.path for result in report.results]
        self.assertIn("/blog/national-pension-receiving-age", paths)
        self.assertIn("/blog/category/education-family", paths)
        self.assertEqual(0, report.error_count)


if __name__ == "__main__":
    unittest.main()
