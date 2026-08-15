import copy
import csv
import json
import unittest
from pathlib import Path

from scripts.validate_owned_data_catalog import validate_catalog


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "_workspace" / "p2-3-owned-data" / "metric-catalog.json"
CITATION_TEMPLATE_PATH = (
    ROOT / "_workspace" / "p2-3-owned-data" / "citation-table-template.csv"
)


class OwnedDataCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    def test_repository_catalog_is_valid(self):
        self.assertEqual(validate_catalog(self.catalog), ())

    def test_only_approved_anonymous_sources_are_available(self):
        self.assertEqual(
            set(self.catalog["approved_sources"]),
            {"ga4", "page_feedback_db"},
        )
        self.assertEqual(
            set(self.catalog["excluded_sources"]),
            {"server_logs", "clarity", "blog_rss_db"},
        )

    def test_forbidden_personal_or_calculation_values_are_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["events"][0]["allowed_dimensions"].append("birth_date")

        errors = validate_catalog(catalog)

        self.assertTrue(any("birth_date" in error for error in errors))

    def test_unapproved_event_source_is_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["events"][0]["source"] = "server_logs"

        errors = validate_catalog(catalog)

        self.assertTrue(any("server_logs" in error for error in errors))

    def test_publication_and_retention_floors_are_enforced(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["publication_gate"]["minimum_denominator"] = 99
        catalog["retention_months"]["monthly_aggregates"] = 15

        errors = validate_catalog(catalog)

        self.assertTrue(any("minimum_denominator" in error for error in errors))
        self.assertTrue(any("monthly_aggregates" in error for error in errors))

    def test_public_metrics_require_traceable_formulas(self):
        catalog = copy.deepcopy(self.catalog)
        catalog["public_metrics"][0]["denominator_event"] = "unknown_event"
        catalog["public_metrics"][0]["formula"] = ""

        errors = validate_catalog(catalog)

        self.assertTrue(any("unknown_event" in error for error in errors))
        self.assertTrue(any("formula" in error for error in errors))

    def test_citation_template_has_provenance_columns_and_no_data_rows(self):
        with CITATION_TEMPLATE_PATH.open(encoding="utf-8", newline="") as file:
            rows = list(csv.reader(file))

        self.assertEqual(
            rows,
            [[
                "metric_name",
                "value",
                "unit",
                "period_start",
                "period_end",
                "sample_size",
                "source",
                "formula",
                "coverage_and_bias",
                "last_updated",
            ]],
        )


if __name__ == "__main__":
    unittest.main()
