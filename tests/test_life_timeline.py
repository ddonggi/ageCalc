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

    def test_ten_hand_checked_samples_match_python_and_browser_calculators(self):
        samples = (
            ("2000-08-24", "2026-08-23", {"full_age": 25, "korean_year_age": 26, "days_lived": 9495, "next_birthday": "2026-08-24", "days_until_birthday": 1, "zodiac": "용", "constellation": "처녀자리"}),
            ("2000-08-24", "2026-08-25", {"full_age": 26, "korean_year_age": 26, "days_lived": 9497, "next_birthday": "2027-08-24", "days_until_birthday": 364, "zodiac": "용", "constellation": "처녀자리"}),
            ("2000-08-23", "2026-08-23", {"full_age": 26, "korean_year_age": 26, "days_lived": 9496, "next_birthday": "2026-08-23", "days_until_birthday": 0, "zodiac": "용", "constellation": "처녀자리"}),
            ("2000-02-29", "2025-02-28", {"full_age": 24, "korean_year_age": 25, "days_lived": 9131, "next_birthday": "2028-02-29", "days_until_birthday": 1096, "zodiac": "용", "constellation": "물고기자리"}),
            ("1990-12-31", "2026-12-30", {"full_age": 35, "korean_year_age": 36, "days_lived": 13148, "next_birthday": "2026-12-31", "days_until_birthday": 1, "zodiac": "말", "constellation": "염소자리"}),
            ("1999-12-31", "2026-01-01", {"full_age": 26, "korean_year_age": 27, "days_lived": 9498, "next_birthday": "2026-12-31", "days_until_birthday": 364, "zodiac": "토끼", "constellation": "염소자리"}),
            ("2000-01-01", "2026-01-01", {"full_age": 26, "korean_year_age": 26, "days_lived": 9497, "next_birthday": "2026-01-01", "days_until_birthday": 0, "zodiac": "용", "constellation": "염소자리"}),
            ("2000-01-20", "2026-01-20", {"full_age": 26, "korean_year_age": 26, "days_lived": 9497, "next_birthday": "2026-01-20", "days_until_birthday": 0, "zodiac": "용", "constellation": "물병자리"}),
            ("2000-02-19", "2026-02-19", {"full_age": 26, "korean_year_age": 26, "days_lived": 9497, "next_birthday": "2026-02-19", "days_until_birthday": 0, "zodiac": "용", "constellation": "물고기자리"}),
            ("2000-03-21", "2026-03-21", {"full_age": 26, "korean_year_age": 26, "days_lived": 9496, "next_birthday": "2026-03-21", "days_until_birthday": 0, "zodiac": "용", "constellation": "양자리"}),
        )
        program = r"""
const timeline = require('./static/js/life-timeline.js');
const samples = JSON.parse(process.argv[1]);
process.stdout.write(JSON.stringify(samples.map(([birthDate, asOf]) => timeline.buildLifeTimeline(birthDate, asOf))));
"""
        completed = subprocess.run(
            ["node", "-e", program, json.dumps([(birth_date, as_of) for birth_date, as_of, _ in samples])],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        browser_results = json.loads(completed.stdout)
        for (birth_iso, as_of_iso, expected), browser_result in zip(samples, browser_results):
            with self.subTest(birth_date=birth_iso, reference_date=as_of_iso):
                self.assertEqual(
                    {
                        **expected,
                        "next_birthday": date.fromisoformat(expected["next_birthday"]),
                    },
                    self.build(date.fromisoformat(birth_iso), date.fromisoformat(as_of_iso)),
                )
                self.assertEqual(
                    {
                        "fullAge": expected["full_age"],
                        "yearAge": expected["korean_year_age"],
                        "daysLived": expected["days_lived"],
                        "nextBirthday": expected["next_birthday"],
                        "daysUntilBirthday": expected["days_until_birthday"],
                        "zodiac": expected["zodiac"],
                        "constellation": expected["constellation"],
                    },
                    browser_result,
                )


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

    def test_tracks_only_safe_completion_and_related_tool_events_after_rendering(self):
        program = r"""
const listeners = {};
function element() {
  return {
    value: '', hidden: true, innerHTML: '', dataset: {}, listeners: {},
    classList: { add() {}, remove() {} },
    addEventListener(name, listener) { this.listeners[name] = listener; }
  };
}
const form = element();
form.dataset.today = '2026-08-23';
const input = element();
const error = element();
const result = element();
result.listeners.click = () => {};
const elements = {
  'life-timeline-form': form,
  'life-birth-date': input,
  'life-timeline-error': error,
  'life-timeline-result': result
};
const events = [];
global.window = {
  AgeCalcTracking: {
    trackEvent(name, params) {
      events.push({ name, params, rendered: !result.hidden && Boolean(result.innerHTML) });
    }
  },
  AgeCalcDateRules: {
    formatDateDigits(value) { return value; },
    parseDateDigits(value) {
      const [year, month, day] = value.split('.').map(Number);
      return new Date(Date.UTC(year, month - 1, day));
    }
  }
};
global.document = {
  addEventListener(name, listener) { listeners[name] = listener; },
  getElementById(id) { return elements[id]; }
};
require('./static/js/life-timeline.js');
listeners.DOMContentLoaded();
input.value = '2000.08.24';
input.listeners.input();
for (const href of ['/age', '/birthday-dday-calculator', '/birth-year-zodiac-table']) {
  result.listeners.click({
    target: { closest() { return { getAttribute() { return href; } }; } },
    preventDefault() {}
  });
}
process.stdout.write(JSON.stringify(events));
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
            [
                {"name": "life_timeline_complete", "params": {"calculator": "life_timeline"}, "rendered": True},
                {"name": "life_timeline_related_tool_click", "params": {"calculator": "life_timeline", "destination": "age"}, "rendered": True},
                {"name": "life_timeline_related_tool_click", "params": {"calculator": "life_timeline", "destination": "birthday_dday"}, "rendered": True},
                {"name": "life_timeline_related_tool_click", "params": {"calculator": "life_timeline", "destination": "birth_year_zodiac"}, "rendered": True},
            ],
            json.loads(completed.stdout),
        )


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
