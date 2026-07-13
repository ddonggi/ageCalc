import unittest
import os
import subprocess
import sys
from pathlib import Path

import scripts.adsense_preflight as preflight_module
from app import PUBLIC_SITEMAP_ENDPOINTS
from scripts.adsense_preflight import PreflightReport, format_report, run_local_preflight, validate_sitemap_paths


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AdsensePreflightTests(unittest.TestCase):
    def test_local_preflight_passes_current_public_structure(self):
        report = run_local_preflight()

        self.assertTrue(report.ok, format_report(report))
        self.assertEqual(46, report.sitemap_urls)
        self.assertEqual(46, report.checked_pages)
        self.assertEqual(31, len(PUBLIC_SITEMAP_ENDPOINTS))
        self.assertEqual(0, report.content_quality_warnings)

    def test_local_preflight_still_passes_after_curated_blog_support(self):
        report = run_local_preflight()

        self.assertTrue(report.ok)
        self.assertEqual(0, report.content_quality_failures)

    def test_preflight_reports_forbidden_sitemap_paths(self):
        report = PreflightReport()

        validate_sitemap_paths(["/", "/blog", "/minigames", "/blog/drafts"], report)

        self.assertFalse(report.ok)
        self.assertIn("/minigames", format_report(report))
        self.assertIn("/blog/drafts", format_report(report))

    def test_review_mode_validator_rejects_affiliate_material(self):
        validator = getattr(preflight_module, "validate_review_mode_html", None)
        self.assertIsNotNone(validator)
        report = PreflightReport()
        html = """
        <a href="https://link.coupang.com/example" rel="sponsored nofollow">
          쿠팡 파트너스 활동으로 수수료를 제공받습니다.
        </a>
        """

        validator("/age", html, report)

        self.assertFalse(report.ok)
        self.assertIn("affiliate_material_present", format_report(report))

    def test_review_mode_preflight_checks_only_sitemap_quality_pages(self):
        report = run_local_preflight()

        self.assertEqual(46, report.sitemap_urls)
        self.assertEqual(0, report.content_quality_failures)
        self.assertEqual(0, report.content_quality_warnings)

    def test_review_mode_validator_rejects_monetized_excluded_page(self):
        validator = getattr(preflight_module, "validate_review_excluded_page", None)
        self.assertIsNotNone(validator)
        report = PreflightReport()
        response = type("Response", (), {"status_code": 200, "headers": {}})()
        html = """
        <html><head>
          <meta name="google-adsense-account" content="ca-pub-test">
          <script src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-test"></script>
        </head><body><h1>허브</h1></body></html>
        """

        validator("/health/", response, html, "ca-pub-test", report)

        output = format_report(report)
        self.assertIn("excluded_page_indexable", output)
        self.assertIn("excluded_page_adsense_present", output)

    def test_format_report_summarizes_clean_result(self):
        report = PreflightReport(checked_pages=3)

        self.assertIn("PASS", format_report(report))
        self.assertIn("checked_pages=3", format_report(report))

    def test_preflight_script_runs_as_file(self):
        env = os.environ.copy()
        env.pop("DATABASE_URL", None)
        result = subprocess.run(
            [sys.executable, "scripts/adsense_preflight.py"],
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
