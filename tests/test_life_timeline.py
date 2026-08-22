import json
import subprocess
import unittest
from datetime import date
from pathlib import Path

from app import app


class LifeTimelineTests(unittest.TestCase):
    def build(self, birth_date, as_of):
        try:
            from services.life_timeline import build_life_timeline
        except ModuleNotFoundError:
            self.fail("services.life_timeline.build_life_timeline is not implemented")

        return build_life_timeline(birth_date, as_of)

    def test_builds_all_results_from_one_reference_date(self):
        result = self.build(date(2000, 8, 24), date(2026, 8, 23))

        self.assertEqual(25, result["full_age"])
        self.assertEqual(26, result["korean_year_age"])
        self.assertEqual(9495, result["days_lived"])
        self.assertEqual(date(2026, 8, 24), result["next_birthday"])
        self.assertEqual(1, result["days_until_birthday"])
        self.assertEqual("용", result["zodiac"])
        self.assertEqual("처녀자리", result["constellation"])

    def test_birthday_today_has_zero_days_remaining(self):
        result = self.build(date(2000, 8, 23), date(2026, 8, 23))

        self.assertEqual(26, result["full_age"])
        self.assertEqual(date(2026, 8, 23), result["next_birthday"])
        self.assertEqual(0, result["days_until_birthday"])

    def test_leap_day_age_changes_on_march_first_and_next_birthday_stays_exact(self):
        before = self.build(date(2000, 2, 29), date(2025, 2, 28))
        after = self.build(date(2000, 2, 29), date(2025, 3, 1))

        self.assertEqual(24, before["full_age"])
        self.assertEqual(25, after["full_age"])
        self.assertEqual(date(2028, 2, 29), before["next_birthday"])
        self.assertEqual(1096, before["days_until_birthday"])

    def test_year_end_birth_date_rolls_birthday_into_next_year(self):
        result = self.build(date(1990, 12, 31), date(2026, 12, 30))

        self.assertEqual(35, result["full_age"])
        self.assertEqual(date(2026, 12, 31), result["next_birthday"])
        self.assertEqual(1, result["days_until_birthday"])
        self.assertEqual("염소자리", result["constellation"])

    def test_rejects_birth_date_after_reference_date(self):
        with self.assertRaisesRegex(ValueError, "기준일보다 늦을 수 없습니다"):
            self.build(date(2026, 8, 24), date(2026, 8, 23))


class LifeTimelineBrowserTests(unittest.TestCase):
    def test_browser_calculator_matches_domain_result_without_network_requests(self):
        program = r"""
const timeline = require('./static/js/life-timeline.js');
const result = timeline.buildLifeTimeline('2000-08-24', '2026-08-23');
process.stdout.write(JSON.stringify(result));
"""
        completed = subprocess.run(
            ["node", "-e", program],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertEqual(
            {
                "fullAge": 25,
                "yearAge": 26,
                "daysLived": 9495,
                "nextBirthday": "2026-08-24",
                "daysUntilBirthday": 1,
                "zodiac": "용",
                "constellation": "처녀자리",
            },
            json.loads(completed.stdout),
        )
        javascript = Path("static/js/life-timeline.js").read_text(encoding="utf-8")
        self.assertNotIn("fetch(", javascript)
        self.assertNotIn("XMLHttpRequest", javascript)


class LifeTimelinePageTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_page_is_client_only_and_masks_birth_date(self):
        response = self.client.get("/life-timeline")
        html = response.get_data(as_text=True)

        self.assertEqual(200, response.status_code)
        self.assertIn("<title>내 생애 타임라인 계산기 | AgeCalc</title>", html)
        self.assertIn("<h1>내 생애 타임라인 계산기</h1>", html)
        self.assertIn('id="life-birth-date"', html)
        self.assertIn('data-clarity-mask="true"', html)
        self.assertNotIn("js/clarity-init.js", html)
        self.assertIn("life-timeline.js", html)
        self.assertIn('id="life-timeline-result"', html)

    def test_query_and_post_cannot_carry_birth_date(self):
        query_response = self.client.get("/life-timeline?birth_date=2000-08-24")
        post_response = self.client.post(
            "/life-timeline",
            data={"birth_date": "2000-08-24"},
        )

        self.assertEqual(302, query_response.status_code)
        self.assertEqual("/life-timeline", query_response.headers["Location"])
        self.assertEqual(405, post_response.status_code)


if __name__ == "__main__":
    unittest.main()
