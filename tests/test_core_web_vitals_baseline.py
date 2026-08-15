import csv
import tempfile
import unittest
from pathlib import Path

from scripts.core_web_vitals_baseline import (
    DataQualityError,
    build_baseline,
    extract_pagespeed_run,
    render_markdown,
    summarize_runs,
)


def _pagespeed_payload(*, lcp=2400, cls=0.08, tbt=180, fcp=1300, ttfb=420):
    def audit(value, unit="millisecond"):
        return {"numericValue": value, "numericUnit": unit}

    return {
        "id": "https://agecalc.cloud/age",
        "analysisUTCTimestamp": "2026-08-16T01:00:00.000Z",
        "lighthouseResult": {
            "finalUrl": "https://agecalc.cloud/age",
            "lighthouseVersion": "12.8.2",
            "categories": {"performance": {"score": 0.91}},
            "audits": {
                "largest-contentful-paint": audit(lcp),
                "cumulative-layout-shift": audit(cls, "unitless"),
                "total-blocking-time": audit(tbt),
                "first-contentful-paint": audit(fcp),
                "server-response-time": audit(ttfb),
                "total-byte-weight": audit(412000, "byte"),
                "network-requests": {
                    "details": {
                        "items": [
                            {"url": "https://pagead2.googlesyndication.com/a.js", "transferSize": 90000},
                            {"url": "https://fonts.gstatic.com/font.woff2", "transferSize": 30000},
                            {"url": "https://agecalc.cloud/static/images/og.png", "transferSize": 40000},
                            {"url": "https://agecalc.cloud/static/js/age.js", "transferSize": 12000},
                        ]
                    }
                },
                "third-party-summary": {
                    "details": {
                        "items": [
                            {"entity": "Google/Doubleclick Ads", "transferSize": 90000, "mainThreadTime": 75}
                        ]
                    }
                },
                "largest-contentful-paint-element": {
                    "details": {"items": [{"node": {"snippet": "<h1>만나이 계산기</h1>"}}]}
                },
            },
        },
    }


class CoreWebVitalsBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        self.export_dir = self.root / "agecalc.cloud-core-web-vitals-Valid-2026-08-16"
        self._write_gsc_export()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_extracts_metrics_and_observed_resource_groups(self):
        result = extract_pagespeed_run(_pagespeed_payload())

        self.assertEqual(91, result["performance_score"])
        self.assertEqual(2400, result["lcp_ms"])
        self.assertEqual(0.08, result["cls"])
        self.assertEqual(180, result["tbt_ms"])
        self.assertEqual(420, result["ttfb_ms"])
        self.assertEqual(90000, result["resource_bytes"]["ads"])
        self.assertEqual(30000, result["resource_bytes"]["fonts"])
        self.assertEqual(40000, result["resource_bytes"]["images"])
        self.assertEqual(12000, result["resource_bytes"]["first_party_scripts"])
        self.assertEqual("<h1>만나이 계산기</h1>", result["lcp_element"])

    def test_summarizes_three_runs_with_medians(self):
        runs = [
            extract_pagespeed_run(_pagespeed_payload(lcp=2800, cls=0.12)),
            extract_pagespeed_run(_pagespeed_payload(lcp=2200, cls=0.04)),
            extract_pagespeed_run(_pagespeed_payload(lcp=2400, cls=0.08)),
        ]

        summary = summarize_runs(runs, required_runs=3)

        self.assertEqual("complete", summary["status"])
        self.assertEqual(2400, summary["median"]["lcp_ms"])
        self.assertEqual(0.08, summary["median"]["cls"])

    def test_marks_fewer_than_three_runs_incomplete(self):
        runs = [extract_pagespeed_run(_pagespeed_payload())] * 2

        summary = summarize_runs(runs, required_runs=3)

        self.assertEqual("incomplete", summary["status"])
        self.assertEqual(2, summary["successful_runs"])

    def _write_gsc_export(self):
        self.export_dir.mkdir(parents=True, exist_ok=True)
        (self.export_dir / "메타데이터.csv").write_text(
            "속성,값\n기기,모바일\n", encoding="utf-8-sig"
        )
        (self.export_dir / "차트.csv").write_text(
            "날짜,빠른 URL\n2026-08-13,38\n2026-08-14,36\n",
            encoding="utf-8-sig",
        )
        (self.export_dir / "테이블.csv").write_text(
            "URL 예시,그룹 채우기\nhttps://agecalc.cloud/age,36\n",
            encoding="utf-8-sig",
        )

    def test_rejects_non_mobile_exports_and_external_urls(self):
        metadata = self.export_dir / "메타데이터.csv"
        metadata.write_text("속성,값\n기기,데스크톱\n", encoding="utf-8-sig")
        with self.assertRaisesRegex(DataQualityError, "mobile"):
            build_baseline(self.root, {})

        self._write_gsc_export()
        table = self.export_dir / "테이블.csv"
        table.write_text(
            table.read_text(encoding="utf-8-sig").replace("agecalc.cloud", "example.com"),
            encoding="utf-8-sig",
        )
        with self.assertRaisesRegex(DataQualityError, "agecalc.cloud"):
            build_baseline(self.root, {})

    def test_builds_deterministic_report_without_inventing_missing_p75(self):
        pagespeed = {
            "https://agecalc.cloud/age": [extract_pagespeed_run(_pagespeed_payload())] * 3
        }

        baseline = build_baseline(self.root, pagespeed, target_urls=("https://agecalc.cloud/age",))
        markdown = render_markdown(baseline)

        self.assertEqual("valid", baseline["field_data"]["status"])
        self.assertEqual(36, baseline["field_data"]["affected_url_count"])
        self.assertEqual("not_available", baseline["field_data"]["p75_value"])
        self.assertEqual("complete", baseline["status"])
        self.assertEqual(1, baseline["analysis"]["lab_lcp_good_count"])
        self.assertEqual(1, baseline["analysis"]["lab_cls_good_count"])
        self.assertEqual("input_calculators", baseline["analysis"]["url_groups"][0]["name"])
        self.assertIn("INP는 Search Console 현장 데이터로만 판정", markdown)
        self.assertIn("URL군별 중앙값", markdown)
        self.assertIn("| ads | 90,000B |", markdown)
        self.assertIn("Google/Doubleclick Ads", markdown)
        self.assertNotIn("PAGESPEED_API_KEY", markdown)


if __name__ == "__main__":
    unittest.main()
