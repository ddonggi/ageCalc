import csv
import json
import tempfile
import unittest
from pathlib import Path

from scripts.seo_performance_baseline import (
    DataQualityError,
    build_baseline,
    render_markdown,
)


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class SeoPerformanceBaselineTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp_dir.name)
        self.gsc_dir = self.data_dir / "google_agecalc.cloud-Performance-on-Search-2026-08-12"
        self._write_valid_fixture()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write_valid_fixture(self):
        _write_csv(
            self.gsc_dir / "차트.csv",
            ["날짜", "클릭수", "노출", "CTR", "게재 순위"],
            [
                {"날짜": "2026-08-08", "클릭수": 1, "노출": 100, "CTR": "1%", "게재 순위": 5},
                {"날짜": "2026-08-09", "클릭수": 2, "노출": 100, "CTR": "2%", "게재 순위": 7},
            ],
        )
        _write_csv(
            self.gsc_dir / "페이지.csv",
            ["인기 페이지", "클릭수", "노출", "CTR", "게재 순위"],
            [
                {"인기 페이지": "https://agecalc.cloud/age", "클릭수": 2, "노출": 150, "CTR": "1.33%", "게재 순위": 6},
                {"인기 페이지": "https://agecalc.cloud/dog", "클릭수": 2, "노출": 100, "CTR": "2%", "게재 순위": 8},
            ],
        )
        _write_csv(
            self.gsc_dir / "검색어 수.csv",
            ["인기 검색어", "클릭수", "노출", "CTR", "게재 순위"],
            [
                {"인기 검색어": "agecalc", "클릭수": 1, "노출": 2, "CTR": "50%", "게재 순위": 1},
                {"인기 검색어": "만나이 계산기", "클릭수": 1, "노출": 50, "CTR": "2%", "게재 순위": 5},
            ],
        )
        for filename, dimension, rows in (
            ("기기.csv", "기기", [("모바일", 2, 150, "1.33%", 5), ("데스크톱", 1, 50, "2%", 9)]),
            ("국가.csv", "국가", [("한국", 3, 200, "1.5%", 6)]),
        ):
            _write_csv(
                self.gsc_dir / filename,
                [dimension, "클릭수", "노출", "CTR", "게재 순위"],
                [
                    {dimension: key, "클릭수": clicks, "노출": impressions, "CTR": ctr, "게재 순위": position}
                    for key, clicks, impressions, ctr, position in rows
                ],
            )
        with (self.data_dir / "naver_export_chart.csv").open("w", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle).writerows(
                [["", "08.10", "08.11"], ["노출", 100, 200], ["클릭", 10, 20]]
            )
        _write_csv(
            self.data_dir / "naver_top30_2026-08-12.csv",
            ["순위", "검색 키워드", "클릭", "노출", "CTR(%)"],
            [
                {"순위": 1, "검색 키워드": "학년 계산기", "클릭": 5, "노출": 10, "CTR(%)": 50},
                {"순위": 2, "검색 키워드": "연나이 계산기", "클릭": 1, "노출": 20, "CTR(%)": 5},
            ],
        )
        _write_csv(
            self.data_dir / "naver_web_documents_top30_2026-08-12.csv",
            ["순위", "URL", "클릭", "노출", "CTR(%)"],
            [
                {"순위": 1, "URL": "https://agecalc.cloud/age?year=2000", "클릭": 5, "노출": 100, "CTR(%)": 5},
                {"순위": 2, "URL": "https://agecalc.cloud/age", "클릭": 4, "노출": 100, "CTR(%)": 4},
            ],
        )

    def test_builds_separate_property_page_and_query_grains(self):
        data = build_baseline(self.data_dir)

        self.assertEqual(3, data["google"]["property_total"]["clicks"])
        self.assertEqual(200, data["google"]["property_total"]["impressions"])
        self.assertEqual(250, data["google"]["page_table"]["total"]["impressions"])
        self.assertEqual("expected_aggregation_difference", data["google"]["page_table"]["comparison_to_property"])
        self.assertEqual("partial_top_rows", data["google"]["query_table"]["coverage"])

    def test_device_and_country_totals_must_match_property_total(self):
        data = build_baseline(self.data_dir)
        self.assertTrue(data["quality"]["google_device_matches_property"])
        self.assertTrue(data["quality"]["google_country_matches_property"])

        with (self.gsc_dir / "기기.csv").open(encoding="utf-8-sig", newline="") as handle:
            rows = list(csv.DictReader(handle))
        rows[0]["클릭수"] = "3"
        rows[0]["CTR"] = "2%"
        _write_csv(self.gsc_dir / "기기.csv", list(rows[0]), rows)
        with self.assertRaisesRegex(DataQualityError, "기기 합계"):
            build_baseline(self.data_dir)

    def test_naver_daily_wide_format_and_path_grouping(self):
        data = build_baseline(self.data_dir)

        self.assertEqual(30, data["naver"]["property_total"]["clicks"])
        self.assertEqual(300, data["naver"]["property_total"]["impressions"])
        self.assertEqual(9, data["naver"]["web_documents"]["path_groups"][0]["clicks"])
        self.assertEqual(2, data["naver"]["web_documents"]["path_groups"][0]["url_count"])
        self.assertIn("?year=2000", data["naver"]["web_documents"]["rows"][0]["url"])

    def test_google_www_page_is_preserved_as_normalization_signal(self):
        pages = self.gsc_dir / "페이지.csv"
        pages.write_text(
            pages.read_text(encoding="utf-8-sig").replace(
                "https://agecalc.cloud/dog", "https://www.agecalc.cloud/dog"
            ),
            encoding="utf-8-sig",
        )

        data = build_baseline(self.data_dir)

        self.assertEqual(1, data["quality"]["google_noncanonical_www_page_rows"])
        self.assertEqual(
            "medium_for_url_normalization",
            data["quality"]["google_noncanonical_www_page_severity"],
        )

    def test_brand_segments_do_not_treat_unreported_queries_as_nonbrand(self):
        data = build_baseline(self.data_dir)
        segments = data["google"]["query_table"]["segments"]

        self.assertEqual(2, segments["known_brand"]["impressions"])
        self.assertEqual(50, segments["known_nonbrand"]["impressions"])
        self.assertEqual("not_quantifiable_from_export", segments["unclassified_or_unreported"]["status"])

    def test_rejects_duplicate_dates_invalid_ctr_negative_values_and_external_urls(self):
        chart = self.gsc_dir / "차트.csv"
        original = chart.read_text(encoding="utf-8-sig")
        chart.write_text(original + "2026-08-09,0,1,0%,1\n", encoding="utf-8-sig")
        with self.assertRaisesRegex(DataQualityError, "중복"):
            build_baseline(self.data_dir)

        self._write_valid_fixture()
        pages = self.gsc_dir / "페이지.csv"
        text = pages.read_text(encoding="utf-8-sig").replace("2,150,1.33%", "2,150,9%")
        pages.write_text(text, encoding="utf-8-sig")
        with self.assertRaisesRegex(DataQualityError, "CTR"):
            build_baseline(self.data_dir)

        self._write_valid_fixture()
        pages.write_text(pages.read_text(encoding="utf-8-sig").replace(",150,", ",-1,"), encoding="utf-8-sig")
        with self.assertRaisesRegex(DataQualityError, "음수"):
            build_baseline(self.data_dir)

        self._write_valid_fixture()
        web = self.data_dir / "naver_web_documents_top30_2026-08-12.csv"
        web.write_text(web.read_text(encoding="utf-8-sig").replace("https://agecalc.cloud", "https://example.com", 1), encoding="utf-8-sig")
        with self.assertRaisesRegex(DataQualityError, "agecalc.cloud"):
            build_baseline(self.data_dir)

    def test_rejects_missing_required_column(self):
        _write_csv(self.gsc_dir / "차트.csv", ["날짜", "클릭수"], [{"날짜": "2026-08-09", "클릭수": 1}])
        with self.assertRaisesRegex(DataQualityError, "필수 열"):
            build_baseline(self.data_dir)

    def test_markdown_and_json_are_deterministic(self):
        first = build_baseline(self.data_dir)
        second = build_baseline(self.data_dir)

        self.assertEqual(json.dumps(first, ensure_ascii=False, sort_keys=True), json.dumps(second, ensure_ascii=False, sort_keys=True))
        self.assertEqual(render_markdown(first), render_markdown(second))
        self.assertIn("2026-08-12~2026-08-25", render_markdown(first))


if __name__ == "__main__":
    unittest.main()
