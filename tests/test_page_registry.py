import csv
import re
import unittest
from pathlib import Path

from app import app
from content.page_registry import (
    CONTENT_ACTIONS,
    GUIDE_PAGE_REGISTRY,
    HUB_PAGE_REGISTRY,
    PUBLIC_PAGE_REGISTRY,
    REQUIRED_PAGE_FIELDS,
    STATIC_PAGE_REGISTRY,
    validate_page_registry,
)


class PageRegistryTests(unittest.TestCase):
    def test_registry_covers_current_static_and_guide_pages(self):
        self.assertEqual(31, len(STATIC_PAGE_REGISTRY))
        self.assertEqual(8, len(HUB_PAGE_REGISTRY))
        self.assertEqual(20, len(GUIDE_PAGE_REGISTRY))
        self.assertEqual(59, len(PUBLIC_PAGE_REGISTRY))

        self.assertEqual(
            {"index", "age", "blog_list"},
            {
                page["endpoint"]
                for page in STATIC_PAGE_REGISTRY
                if page["endpoint"] in {"index", "age", "blog_list"}
            },
        )
        self.assertEqual(
            20,
            sum(page["endpoint"] == "guide_detail" for page in GUIDE_PAGE_REGISTRY),
        )

    def test_every_registry_entry_has_required_policy_fields(self):
        for page in PUBLIC_PAGE_REGISTRY:
            with self.subTest(key=page["key"]):
                self.assertTrue(REQUIRED_PAGE_FIELDS.issubset(page))
                self.assertIn(page["content_action"], CONTENT_ACTIONS)
                self.assertTrue(page["search_intent"].strip())
                self.assertTrue(page["path"].startswith("/"))
                self.assertIsInstance(page["related_endpoints"], tuple)

    def test_registry_keys_paths_and_search_intents_are_unique(self):
        for field in ("key", "path", "search_intent"):
            values = [page[field] for page in PUBLIC_PAGE_REGISTRY]
            with self.subTest(field=field):
                self.assertEqual(len(values), len(set(values)))

        self.assertEqual((), validate_page_registry())

    def test_registry_driven_sitemap_preserves_the_fifty_url_baseline(self):
        response = app.test_client().get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        urls = re.findall(r"<loc>(.*?)</loc>", response.get_data(as_text=True))
        self.assertEqual(58, len(urls))
        self.assertEqual(58, len(set(urls)))
        self.assertNotIn("https://agecalc.cloud/blog", urls)
        self.assertIn("https://agecalc.cloud/age", urls)
        self.assertIn("https://agecalc.cloud/age/", urls)
        self.assertIn(
            "https://agecalc.cloud/guides/age-calculation-2026",
            urls,
        )

    def test_page_audit_csv_covers_the_fifty_baseline_urls(self):
        audit_path = Path("docs/content/page-audit-2026-06.csv")

        with audit_path.open(encoding="utf-8", newline="") as audit_file:
            rows = list(csv.DictReader(audit_file))

        self.assertEqual(50, len(rows))
        self.assertEqual(50, len({row["path"] for row in rows}))
        self.assertEqual(
            {
                "path",
                "endpoint",
                "hub",
                "content_action",
                "current_status",
                "unique_value",
                "official_source_required",
            },
            set(rows[0]),
        )
        self.assertNotIn("/blog", {row["path"] for row in rows})


if __name__ == "__main__":
    unittest.main()
