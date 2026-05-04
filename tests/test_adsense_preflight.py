import unittest
import os
import subprocess
import sys
from pathlib import Path

from app import PUBLIC_SITEMAP_ENDPOINTS
from scripts.adsense_preflight import PreflightReport, format_report, run_local_preflight, validate_sitemap_paths


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class AdsensePreflightTests(unittest.TestCase):
    def test_local_preflight_passes_current_public_structure(self):
        report = run_local_preflight()

        self.assertTrue(report.ok, format_report(report))
        self.assertGreaterEqual(report.checked_pages, len(PUBLIC_SITEMAP_ENDPOINTS) - 1)

    def test_preflight_reports_forbidden_sitemap_paths(self):
        report = PreflightReport()

        validate_sitemap_paths(["/", "/blog", "/minigames", "/blog/drafts"], report)

        self.assertFalse(report.ok)
        self.assertIn("/minigames", format_report(report))
        self.assertIn("/blog/drafts", format_report(report))

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
