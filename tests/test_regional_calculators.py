import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch


try:
    from models.regional_calculators import calculate
except ImportError:
    calculate = None


class RegionalCalculatorTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.holiday_path = Path(self.tempdir.name) / "regional_holidays.json"
        self.holiday_path.write_text(
            json.dumps(
                {
                    "start_year": 2025,
                    "end_year": 2027,
                    "checked": "2026-09-15",
                    "calendars": {
                        "ja": {
                            "2026-01-01": "元日",
                            "2026-01-12": "成人の日",
                        },
                        "pt-BR": {
                            "2026-01-01": "Confraternização universal",
                        },
                    },
                    "sources": {"ja": "official", "pt-BR": "official"},
                }
            ),
            encoding="utf-8",
        )
        self.holiday_patch = patch(
            "models.regional_calculators.HOLIDAY_DATA_PATH", self.holiday_path
        )
        self.holiday_patch.start()

    def tearDown(self):
        self.holiday_patch.stop()
        self.tempdir.cleanup()

    def test_birth_date_range_is_inclusive_for_completed_age(self):
        result = calculate(
            "birth_date_range", {"reference": "2026-09-15", "age": "30"}, "en"
        )
        self.assertEqual(
            result["rows"],
            [("earliest", "1995-09-16"), ("latest", "1996-09-15")],
        )
        self.assertEqual(result["note"], "birth_date_range_note")

    def test_birth_date_range_uses_march_first_leap_day_anniversary(self):
        result = calculate(
            "birth_date_range", {"reference": "2025-02-28", "age": "1"}, "en"
        )
        self.assertEqual(
            result["rows"],
            [("earliest", "2023-03-01"), ("latest", "2024-02-28")],
        )
        older_boundary = calculate(
            "birth_date_range", {"reference": "1999-02-28", "age": "2"}, "en"
        )
        self.assertEqual(
            older_boundary["rows"],
            [("earliest", "1996-02-29"), ("latest", "1997-02-28")],
        )

    def test_school_april_first_is_in_earlier_cohort_than_april_second(self):
        april_first = calculate(
            "school_year",
            {"birth": "2020-04-01", "gap": "0", "course": "4"},
            "ja",
        )
        april_second = calculate(
            "school_year",
            {"birth": "2020-04-02", "gap": "0", "course": "4"},
            "ja",
        )
        self.assertEqual(april_first["rows"][0], ("elementary_entry", "2026-04-01"))
        self.assertEqual(april_second["rows"][0], ("elementary_entry", "2027-04-01"))

    def test_school_gap_and_course_change_only_university_milestones(self):
        result = calculate(
            "school_year",
            {"birth": "2020-04-01", "gap": "2", "course": "6"},
            "ja",
        )
        self.assertEqual(
            result["rows"],
            [
                ("elementary_entry", "2026-04-01"),
                ("elementary_graduation", "2032-03-31"),
                ("junior_high_entry", "2032-04-01"),
                ("junior_high_graduation", "2035-03-31"),
                ("high_school_entry", "2035-04-01"),
                ("high_school_graduation", "2038-03-31"),
                ("university_entry", "2040-04-01"),
                ("university_graduation", "2046-03-31"),
            ],
        )

    def test_japanese_era_exact_boundaries(self):
        fixtures = {
            "1989-01-07": "昭和64年1月7日",
            "1989-01-08": "平成元年1月8日",
            "2019-05-01": "令和元年5月1日",
        }
        for date, era_date in fixtures.items():
            with self.subTest(date=date):
                result = calculate(
                    "japanese_era", {"mode": "to_era", "date": date}, "ja"
                )
                self.assertEqual(result["rows"], [("era_date", era_date)])

    def test_japanese_era_reverse_conversion_checks_boundary(self):
        result = calculate(
            "japanese_era",
            {
                "mode": "from_era",
                "era": "reiwa",
                "era_year": "1",
                "month": "5",
                "day": "1",
            },
            "ja",
        )
        self.assertEqual(result["rows"], [("gregorian_date", "2019-05-01")])
        with self.assertRaisesRegex(ValueError, "^invalid_era_date$"):
            calculate(
                "japanese_era",
                {
                    "mode": "from_era",
                    "era": "reiwa",
                    "era_year": "1",
                    "month": "4",
                    "day": "30",
                },
                "ja",
            )

    def test_japanese_era_rejects_pre_gregorian_support(self):
        with self.assertRaisesRegex(ValueError, "^unsupported_range$"):
            calculate(
                "japanese_era", {"mode": "to_era", "date": "1872-12-31"}, "ja"
            )

    def test_lunar_regular_new_year_and_next_occurrence(self):
        result = calculate(
            "lunar_birthday",
            {"month": "1", "day": "1", "reference": "2026-01-01"},
            "ko",
        )
        self.assertEqual(result["rows"], [("next_birthday", "2026-02-17")])
        self.assertEqual(result["table"][0], ["2025", "2025-01-29", "available"])
        self.assertEqual(result["table"][1], ["2026", "2026-02-17", "available"])
        self.assertEqual(len(result["table"]), 6)

    def test_lunar_late_month_birthday_before_new_year_is_not_skipped(self):
        result = calculate(
            "lunar_birthday",
            {"month": "12", "day": "15", "reference": "2026-01-01"},
            "ko",
        )
        self.assertEqual(result["rows"], [("next_birthday", "2026-02-02")])
        self.assertEqual(result["table"][0], ["2025", "2026-02-02", "available"])

    def test_lunar_missing_leap_month_is_explicitly_unavailable(self):
        result = calculate(
            "lunar_birthday",
            {"month": "1", "day": "1", "leap": "1", "reference": "2026-01-01"},
            "ko",
        )
        self.assertEqual(result["table"][0], ["2025", "", "missing_leap_month"])

    def test_lunar_day_uses_lunar_validation_not_gregorian_validation(self):
        result = calculate(
            "lunar_birthday",
            {"month": "2", "day": "30", "reference": "2026-01-01"},
            "ko",
        )
        self.assertEqual(result["table"][0], ["2025", "", "invalid_lunar_date"])

    def test_lunar_boundary_years_are_reported_unavailable(self):
        result = calculate(
            "lunar_birthday",
            {"month": "1", "day": "1", "reference": "2049-01-01"},
            "ko",
        )
        self.assertEqual(result["table"][0][2], "available")
        self.assertTrue(all(row[2] == "unsupported_year" for row in result["table"][2:]))

    def test_lunar_reports_when_no_future_occurrence_is_in_supported_range(self):
        result = calculate(
            "lunar_birthday",
            {"month": "1", "day": "1", "reference": "2049-12-31"},
            "ko",
        )
        self.assertEqual(result["rows"], [("next_birthday", "next_unavailable")])

    def test_shipped_holiday_dataset_has_complete_declared_years(self):
        production_path = Path(__file__).resolve().parents[1] / "data" / "regional_holidays.json"
        payload = json.loads(production_path.read_text(encoding="utf-8"))
        self.assertEqual((2025, 2027), (payload["start_year"], payload["end_year"]))
        for locale, minimum_per_year in (("ja", 16), ("pt-BR", 9)):
            calendar_data = payload["calendars"][locale]
            parsed = [date.fromisoformat(raw) for raw in calendar_data]
            for year in range(2025, 2028):
                self.assertGreaterEqual(
                    sum(day.year == year for day in parsed), minimum_per_year,
                    f"{locale}/{year}",
                )
        self.assertIn("2026-05-06", payload["calendars"]["ja"])
        self.assertIn("2026-11-20", payload["calendars"]["pt-BR"])

    def test_business_count_excludes_weekend_holiday_and_custom_without_duplicates(self):
        result = calculate(
            "business_days",
            {
                "mode": "count",
                "start": "2026-01-01",
                "end": "2026-01-05",
                "include_end": "1",
                "excluded": "2026-01-01\n2026-01-03",
            },
            "ja",
        )
        self.assertEqual(result["rows"], [("workdays", "2")])

    def test_business_count_can_exclude_final_day(self):
        included = calculate(
            "business_days",
            {"mode": "count", "start": "2026-01-02", "end": "2026-01-05", "include_end": "1"},
            "ja",
        )
        excluded = calculate(
            "business_days",
            {"mode": "count", "start": "2026-01-02", "end": "2026-01-05"},
            "ja",
        )
        self.assertEqual(included["rows"], [("workdays", "2")])
        self.assertEqual(excluded["rows"], [("workdays", "1")])

    def test_business_add_subtract_excludes_start_and_supports_zero(self):
        fixtures = [
            ({"mode": "add", "start": "2026-01-09", "amount": "1"}, "2026-01-13"),
            ({"mode": "subtract", "start": "2026-01-13", "amount": "1"}, "2026-01-09"),
            ({"mode": "add", "start": "2026-01-10", "amount": "0"}, "2026-01-10"),
        ]
        for values, expected in fixtures:
            with self.subTest(values=values):
                self.assertEqual(
                    calculate("business_days", values, "ja")["rows"],
                    [("result_date", expected)],
                )

        with self.assertRaisesRegex(ValueError, "^invalid_range$"):
            calculate(
                "business_days",
                {"mode": "add", "start": "2026-01-09", "amount": "-1"},
                "ja",
            )

    def test_business_rejects_input_or_result_outside_holiday_range(self):
        for values in (
            {"mode": "count", "start": "2024-12-31", "end": "2025-01-02"},
            {"mode": "add", "start": "2027-12-31", "amount": "1"},
        ):
            with self.subTest(values=values), self.assertRaisesRegex(
                ValueError, "^unsupported_range$"
            ):
                calculate("business_days", values, "ja")

    def test_dispatch_rejects_invalid_locale_unknown_parameters_and_custom_date_flood(self):
        cases = [
            ("lunar_birthday", {"month": "1", "day": "1", "reference": "2026-01-01"}, "ja", "invalid_locale"),
            ("birth_date_range", {"reference": "2026-01-01", "age": "3", "extra": "x"}, "en", "invalid_parameters"),
            ("business_days", {"mode": "count", "start": "2026-01-01", "end": "2026-01-02", "excluded": "\n".join(["2026-01-01"] * 101)}, "ja", "too_many_excluded_dates"),
        ]
        for kind, values, locale, error in cases:
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, f"^{error}$"):
                calculate(kind, values, locale)

    def test_dispatch_rejects_unknown_kind(self):
        with self.assertRaisesRegex(ValueError, "^invalid_kind$"):
            calculate("unknown", {}, "en")

    def test_only_business_days_loads_holiday_data(self):
        missing = Path(self.tempdir.name) / "missing.json"
        with patch("models.regional_calculators.HOLIDAY_DATA_PATH", missing):
            birth_result = calculate(
                "birth_date_range",
                {"reference": "2026-09-15", "age": "30"},
                "en",
            )
            self.assertEqual(birth_result["rows"][0], ("earliest", "1995-09-16"))
            with self.assertRaisesRegex(ValueError, "^holiday_data_unavailable$"):
                calculate(
                    "business_days",
                    {"mode": "count", "start": "2026-01-01", "end": "2026-01-02"},
                    "ja",
                )

    def test_date_arithmetic_overflow_fails_gracefully(self):
        cases = [
            ("birth_date_range", {"reference": "0001-01-01", "age": "1"}, "en"),
            ("school_year", {"birth": "9999-04-02", "gap": "10", "course": "6"}, "ja"),
        ]
        for kind, values, locale in cases:
            with self.subTest(kind=kind), self.assertRaisesRegex(
                ValueError, "^unsupported_range$"
            ):
                calculate(kind, values, locale)

    def test_numeric_ranges_and_invalid_dates_fail_with_stable_keys(self):
        cases = [
            ("birth_date_range", {"reference": "2026-02-30", "age": "3"}, "en", "invalid_date"),
            ("birth_date_range", {"reference": "2026-01-01", "age": "151"}, "en", "invalid_range"),
            ("school_year", {"birth": "2020-01-01", "gap": "11", "course": "4"}, "ja", "invalid_range"),
            ("school_year", {"birth": "2020-01-01", "gap": "0", "course": "3"}, "ja", "invalid_range"),
            ("lunar_birthday", {"month": "13", "day": "1", "reference": "2026-01-01"}, "ko", "invalid_range"),
        ]
        for kind, values, locale, error in cases:
            with self.subTest(kind=kind, values=values), self.assertRaisesRegex(ValueError, f"^{error}$"):
                calculate(kind, values, locale)


if __name__ == "__main__":
    unittest.main()
