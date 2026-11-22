import json
import re
from copy import deepcopy
import unittest
from datetime import date
from html.parser import HTMLParser
from unittest.mock import patch
from urllib.parse import urlsplit

from app import app
from content.i18n import PAGE_BY_KEY, catalog, validate_translations
from content.locale_config import ALL_LOCALES
from content.page_registry import PRIVACY_NO_THIRD_PARTY_PATHS
from content.related_tools import RELATED_TOOLS, baseline_destinations, validate_related_copy


class RelatedNav(HTMLParser):
    """Read the actual links and disclosure state from the rendered component."""

    def __init__(self, response):
        super().__init__()
        self.nav = None
        self.cards = {}
        self.in_nav = False
        self.feed(response.get_data(as_text=True))

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "nav" and "data-related-tools" in attrs:
            if self.nav is not None:
                raise ValueError("Duplicate recommendation navigation")
            self.in_nav = True
            self.nav = attrs
        if tag == "a" and self.in_nav:
            key = attrs["data-tool"]
            if key in self.cards:
                raise ValueError("Duplicate recommendation destination")
            self.cards[key] = attrs

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_nav = False


class RelatedToolTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_all_localized_base_urls_have_one_hidden_navigation_with_native_links(self):
        self.assertEqual(31, len(RELATED_TOOLS))
        counts = []
        for locale in ALL_LOCALES:
            paths = baseline_destinations(locale)
            counts.append(len(paths))
            for path, source in paths.items():
                with self.subTest(path=path):
                    response = self.client.get(path)
                    self.assertEqual(200, response.status_code)
                    nav = RelatedNav(response)
                    self.assertEqual(source["tool"], nav.nav["data-source"])
                    self.assertEqual(locale, nav.nav["data-locale"])
                    self.assertEqual("false", nav.nav["data-ssr-success"])
                    self.assertIn("hidden", nav.nav)
                    self.assertLessEqual(len(nav.cards), 2)
                    for key, link in nav.cards.items():
                        target = link["href"]
                        self.assertEqual("no-referrer", link["referrerpolicy"])
                        self.assertIn(target, paths)
                        self.assertNotEqual(source["tool"], key)
                        self.assertNotEqual(key, "life_timeline")
                        self.assertEqual(paths[target]["tool"], key)
                        self.assertEqual(str(target not in PRIVACY_NO_THIRD_PARTY_PATHS).lower(), link["data-measurable"])
        self.assertEqual([27, 9, 11, 8, 10, 8], counts)

    def test_all_reachable_copy_including_optional_modes_is_required(self):
        for locale in ALL_LOCALES:
            original = catalog(locale)["related_tools"]
            for key in original["cards"]:
                for index in (None, 0, 1):
                    with self.subTest(locale=locale, key=key, index=index):
                        copy = deepcopy(original)
                        if index is None:
                            del copy["cards"][key]
                        else:
                            copy["cards"][key][index] = "  "
                        with self.assertRaisesRegex(ValueError, f"{locale}/{key}"):
                            validate_related_copy(locale, copy)

    def test_publication_validator_checks_conditional_translations(self):
        changed = deepcopy(catalog("ko"))
        changed["related_tools"]["cards"]["cohort_school"][0] = "{birth_date}년생"
        with patch("content.i18n.catalog", side_effect=lambda code: changed if code == "ko" else catalog(code)):
            with self.assertRaisesRegex(ValueError, "ko/cohort_school"):
                validate_translations()

    def test_release_policy_filters_hidden_merged_and_staged_destinations(self):
        target = PAGE_BY_KEY["date_add_subtract"]
        for changes in ({"release_batch": "staged"}, {"indexable": False}, {"content_action": "merge"}):
            with self.subTest(changes=changes), patch.dict(target, changes):
                nav = RelatedNav(self.client.get("/en/days-between-dates"))
                self.assertEqual({}, nav.cards)
                # Baseline data uses the same immutable registry, cached per locale.
                self.assertNotIn("/en/date-add-subtract-calculator", baseline_destinations.__wrapped__("en"))

    def test_language_specific_age_and_calendar_destinations(self):
        for locale, prefix in [("en", "/en"), ("ja", "/ja"), ("es", "/es"), ("pt-BR", "/pt-br"), ("zh-CN", "/zh-cn")]:
            age = RelatedNav(self.client.get(prefix + "/age-calculator"))
            expected = ["age_gap_calculator"] + (["birth_date_range"] if locale in ("en", "pt-BR") else [])
            self.assertEqual(expected, list(age.cards))
            dates = RelatedNav(self.client.get(prefix + "/days-between-dates"))
            expected = ["date_add_subtract"] + (["business_days"] if locale in ("ja", "pt-BR") else [])
            self.assertEqual(expected, list(dates.cards))

    @patch("app._current_local_date", return_value=date(2026, 11, 22))
    def test_validated_year_reuse_and_korean_calendar_modes(self, _today):
        cases = [
            ("/age?birth_date=20000229&calendar_type=solar", ["/annual-age-calculator?birth_year=2000", "/birthday-dday-calculator"]),
            ("/age?birth_date=20000101&calendar_type=lunar", ["/lunar-birthday-calculator", "/annual-age-calculator?birth_year=2000"]),
            ("/annual-age-calculator?birth_year=1900", ["/age", "/birth-year-age-table"]),
            ("/annual-age-calculator?birth_year=1992", ["/age", "/birth-year-age-table?year=1992"]),
            ("/birth-year-age-table?year=2010", ["/annual-age-calculator?birth_year=2010", "/school-grade-calculator?year=2010"]),
            ("/grade-birth-year-table?stage=high&grade=3", ["/school-grade-calculator", "/college-entry-year-calculator?year=2027"]),
            ("/grade-birth-year-table?stage=elementary&grade=1", ["/school-grade-calculator", "/college-entry-year-calculator"]),
            ("/college-entry-year-calculator?year=2026", ["/birth-year-age-table?year=2007", "/school-grade-calculator?year=2007"]),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                nav = RelatedNav(self.client.get(path))
                self.assertNotIn("hidden", nav.nav)
                self.assertEqual("true", nav.nav["data-ssr-success"])
                self.assertEqual(expected, [link["href"] for link in nav.cards.values()])
                for target in expected:
                    self.assertEqual(200, self.client.get(target).status_code)
        nav = RelatedNav(self.client.get("/age?birth_date=20010229"))
        self.assertEqual("false", nav.nav["data-ssr-success"])
        self.assertIn("hidden", nav.nav)

    @patch("app._current_local_date", return_value=date(2026, 11, 22))
    def test_conditional_month_ranges_and_adoption(self, _today):
        for birth, include_table in [("20261122", True), ("20231122", True), ("20231022", False)]:
            nav = RelatedNav(self.client.get("/baby-months", query_string={"birth_date": birth}))
            self.assertEqual(["hundred_day_calculator"] + (["baby_months_table"] if include_table else []), list(nav.cards))
        for species in ("cat", "dog"):
            for years, months, expected in [(0, 1, "pet_months_table"), (2, 0, "pet_months_table"),
                                            (2, 1, "pet_age_table"), (20, 0, "pet_age_table"), (21, 0, None)]:
                with self.subTest(species=species, years=years, months=months):
                    query = dict(mode="known-age", years=years, months=months, birth_date="", adoption_date="")
                    nav = RelatedNav(self.client.get("/" + species, query_string=query))
                    self.assertEqual("true", nav.nav["data-ssr-success"])
                    self.assertEqual([expected] if expected else [], list(nav.cards))
                    self.assertEqual(not expected, "hidden" in nav.nav)
            query = dict(mode="adoption-date", years="", months="", birth_date="", adoption_date="20220101")
            nav = RelatedNav(self.client.get("/" + species, query_string=query))
            self.assertEqual(["d_day"], list(nav.cards))
            for months in (11, 12, 24):
                nav = RelatedNav(self.client.get("/pet-months-table", query_string={"pet": species, "months": months}))
                self.assertEqual([species] + (["pet_age_table"] if months >= 12 else []), list(nav.cards))
            nav = RelatedNav(self.client.get("/pet-age-table", query_string={"pet": species, "years": 5}))
            self.assertEqual([species], list(nav.cards))

    def test_sensitive_inputs_stay_out_of_recommendations(self):
        cases = [
            ("/parent-child?parent_role=mother&parent_birth=19800213&child_role=son&child_birth=20150831&child_role=daughter&child_birth=20191216",
             ["school_grade_calculator", "birthday_dday_calculator"]),
            ("/d-day?date=20270102&mode=until&label=private-event", ["days_between_dates", "hundred_day_calculator"]),
            ("/life-timeline?birth_date=19970312", ["birthday_dday_calculator", "birth_year_zodiac_table"]),
        ]
        for path, expected in cases:
            with self.subTest(path=path):
                nav = RelatedNav(self.client.get(path))
                self.assertEqual(expected, list(nav.cards))
                self.assertNotIn("hidden", nav.nav)
                self.assertTrue(all(not urlsplit(link["href"]).query for link in nav.cards.values()))

    def test_regional_post_distinguishes_success_failure_and_mode(self):
        path = "/ja/business-days-calculator"
        for mode, destination in [("count", "days_between_dates"), ("add", "date_add_subtract"), ("subtract", "date_add_subtract")]:
            nav = RelatedNav(self.client.post(path, data=dict(mode=mode, start="2026-01-07", end="2026-01-09", amount="2")))
            self.assertNotIn("hidden", nav.nav)
            self.assertEqual([destination], list(nav.cards))
        response = self.client.post(path, data={"mode": "other", "start": "2026-01-07"})
        self.assertEqual(400, response.status_code)
        self.assertIn("hidden", RelatedNav(response).nav)

    def test_baseline_exposes_only_local_destinations_and_existing_result_state(self):
        with patch.dict(app.config, RELATED_TOOLS_LAYOUT="baseline"):
            for path, locale, success in [("/pet-age-table?years=2", "ko", "true"), ("/en/age-calculator", "en", "false")]:
                response = self.client.get(path)
                nav = RelatedNav(response)
                self.assertEqual("baseline", nav.nav["data-layout"])
                self.assertEqual(success, nav.nav["data-ssr-success"])
                self.assertIn("hidden", nav.nav)
                self.assertFalse(nav.cards)
                match = re.search(r'data-baseline-destinations>(.*?)</script>', response.get_data(as_text=True))
                self.assertEqual(baseline_destinations(locale), json.loads(match[1]))
