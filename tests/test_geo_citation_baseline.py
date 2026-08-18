import copy
import csv
import hashlib
import json
import unittest
from pathlib import Path

from scripts.validate_geo_citation_baseline import (
    build_observation_rows,
    summarize_observations,
    validate_observations,
)


ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "_workspace" / "p2-7-geo-citation" / "prompt-catalog.json"
TEMPLATE_PATH = ROOT / "_workspace" / "p2-7-geo-citation" / "observation-template.csv"


class GeoCitationBaselineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))

    def test_builds_one_observation_for_every_prompt_and_platform(self):
        rows = build_observation_rows(self.catalog)

        self.assertEqual(36, len(rows))
        self.assertEqual(
            36,
            len({(row["query_id"], row["platform"]) for row in rows}),
        )
        self.assertTrue(all(row["observation_status"] == "pending" for row in rows))

    def test_repository_template_matches_the_catalog(self):
        with TEMPLATE_PATH.open(encoding="utf-8", newline="") as file:
            actual_rows = list(csv.DictReader(file))

        self.assertEqual(build_observation_rows(self.catalog), actual_rows)
        self.assertEqual((), validate_observations(self.catalog, actual_rows))

    def test_complete_validation_rejects_pending_and_missing_combinations(self):
        rows = build_observation_rows(self.catalog)
        rows.pop()

        errors = validate_observations(self.catalog, rows, require_complete=True)

        self.assertTrue(any("missing combinations" in error for error in errors))
        self.assertTrue(any("pending observations" in error for error in errors))

    def test_rejects_duplicate_and_unknown_platform_rows(self):
        rows = build_observation_rows(self.catalog)
        rows.append(copy.deepcopy(rows[0]))
        rows[1]["platform"] = "unknown_ai"

        errors = validate_observations(self.catalog, rows)

        self.assertTrue(any("duplicate combination" in error for error in errors))
        self.assertTrue(any("unknown platform" in error for error in errors))

    def test_citation_requires_agecalc_url_and_evidence_checksum(self):
        rows = self._observed_rows()
        rows[0]["agecalc_url_cited"] = "true"
        rows[0]["agecalc_cited_urls"] = "https://example.com/age"
        rows[0]["evidence_sha256"] = "bad-checksum"

        errors = validate_observations(self.catalog, rows, require_complete=True)

        self.assertTrue(any("agecalc.cloud URL" in error for error in errors))
        self.assertTrue(any("SHA-256" in error for error in errors))

    def test_brand_sentiment_and_citation_context_must_be_consistent(self):
        rows = self._observed_rows()
        rows[0]["brand_mentioned"] = "false"
        rows[0]["sentiment"] = "positive"
        rows[1]["agecalc_url_cited"] = "false"
        rows[1]["citation_context"] = "supporting_source"

        errors = validate_observations(self.catalog, rows, require_complete=True)

        self.assertTrue(any("sentiment" in error for error in errors))
        self.assertTrue(any("citation_context" in error for error in errors))

    def test_complete_run_requires_fixed_conditions_and_one_measurement_date(self):
        rows = self._observed_rows()
        rows[0]["country"] = "US"
        rows[1]["measurement_date"] = "2026-08-17"
        rows[2]["session_state"] = "personalized_session"

        errors = validate_observations(self.catalog, rows, require_complete=True)

        self.assertTrue(any("country differs from catalog" in error for error in errors))
        self.assertTrue(any("session_state differs from catalog" in error for error in errors))
        self.assertTrue(any("one measurement_date" in error for error in errors))

    def test_citation_positions_domains_and_click_state_must_agree(self):
        rows = self._observed_rows()
        rows[0].update(
            {
                "agecalc_url_cited": "true",
                "agecalc_cited_urls": "https://agecalc.cloud/age",
                "citation_positions": "0;two",
                "citation_context": "direct_answer",
                "all_cited_domains": "example.com",
                "citation_link_available": "false",
            }
        )
        rows[1]["citation_link_available"] = "true"

        errors = validate_observations(self.catalog, rows, require_complete=True)

        self.assertTrue(any("citation_positions" in error for error in errors))
        self.assertTrue(any("all_cited_domains" in error for error in errors))
        self.assertTrue(any("link cannot exist without citation" in error for error in errors))

    def test_summary_excludes_unavailable_surfaces_and_reports_literal_rates(self):
        rows = self._observed_rows()
        rows[0].update(
            {
                "brand_mentioned": "true",
                "agecalc_url_cited": "true",
                "agecalc_cited_urls": "https://agecalc.cloud/age",
                "citation_positions": "2",
                "citation_context": "supporting_source",
                "sentiment": "positive",
                "all_cited_domains": "example.com;agecalc.cloud",
                "citation_link_available": "true",
            }
        )
        rows[1]["observation_status"] = "surface_not_present"
        rows[1]["brand_mentioned"] = "not_applicable"
        rows[1]["agecalc_url_cited"] = "not_applicable"
        rows[1]["citation_context"] = "not_applicable"
        rows[1]["sentiment"] = "not_applicable"
        rows[1]["citation_link_available"] = "not_applicable"

        summary = summarize_observations(rows)

        self.assertEqual(35, summary["valid_observations"])
        self.assertEqual(1, summary["surface_not_present"])
        self.assertAlmostEqual(1 / 35, summary["citation_rate"])
        self.assertAlmostEqual(1 / 35, summary["brand_mention_rate"])
        self.assertAlmostEqual(1 / 2, summary["citation_share"])
        self.assertEqual({"positive": 1, "neutral": 0, "negative": 0}, summary["sentiment"])
        self.assertEqual("not_available", summary["downstream_clicks"])

    def _observed_rows(self):
        rows = build_observation_rows(self.catalog)
        checksum = hashlib.sha256(b"evidence").hexdigest()
        for index, row in enumerate(rows):
            row.update(
                {
                    "measurement_date": "2026-08-18",
                    "platform_model": "recorded-default",
                    "observation_status": "observed",
                    "brand_mentioned": "false",
                    "agecalc_url_cited": "false",
                    "agecalc_cited_urls": "",
                    "citation_positions": "",
                    "citation_context": "not_applicable",
                    "sentiment": "not_applicable",
                    "all_cited_domains": "",
                    "citation_link_available": "false",
                    "downstream_clicks": "not_available",
                    "evidence_file": f"{index + 1:02d}.png",
                    "evidence_sha256": checksum,
                }
            )
        return rows


if __name__ == "__main__":
    unittest.main()
