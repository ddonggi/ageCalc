import unittest
import subprocess
from datetime import date
from pathlib import Path

from app import app
from models.date_rules import calculate_man_age, parse_iso_date


class DateRuleTests(unittest.TestCase):
    def test_browser_date_rules_execute_birthday_leap_and_hundred_day_cases(self):
        script = r"""
const assert = require('assert');
const rules = require('./static/js/date-rules.js');
assert.strictEqual(rules.calculateManAge('1992-10-02', '2026-10-01'), 33);
assert.strictEqual(rules.calculateManAge('1992-10-02', '2026-10-02'), 34);
assert.strictEqual(rules.calculateManAge('2000-02-29', '2026-02-28'), 25);
assert.strictEqual(rules.calculateManAge('2000-02-29', '2026-03-01'), 26);
assert.throws(() => rules.calculateManAge('2027-01-01', '2026-12-31'), /future/);
assert.strictEqual(rules.formatIsoDate(rules.parseBirthDateDigits('19270101', '2026-12-31')), '1927-01-01');
assert.throws(() => rules.parseBirthDateDigits('270101', '2026-12-31'), /8 digits/);
assert.throws(() => rules.parseBirthDateDigits('20270101', '2026-12-31'), /future/);
assert.throws(() => rules.parseIsoDate('2026-02-30'), /YYYY-MM-DD/);
assert.strictEqual(rules.formatIsoDate(rules.addUtcDays(rules.parseIsoDate('2026-01-31'), 99)), '2026-05-10');
assert.strictEqual(rules.formatIsoDate(rules.addUtcDays(rules.parseIsoDate('2024-02-29'), 99)), '2024-06-07');
assert.strictEqual(rules.calculateCompletedMonths('2025-01-31', '2025-02-28'), 1);
assert.strictEqual(rules.calculateCompletedMonths('2024-02-29', '2025-02-28'), 12);
assert.strictEqual(rules.calculateCompletedMonths('2025-06-15', '2026-02-14'), 7);
assert.strictEqual(rules.calculateCompletedMonths('2025-06-15', '2026-02-15'), 8);
assert.strictEqual(rules.formatDateDigits('19921002'), '1992.10.02');
assert.strictEqual(rules.formatDateDigits('1992-10-0'), '1992.10.0');
assert.strictEqual(rules.formatMonthDayDigits('0510'), '05.10');
assert.strictEqual(rules.formatIsoDate(rules.parseDateDigits('20260228')), '2026-02-28');
assert.deepStrictEqual(rules.parseMonthDayDigits('0229'), { month: 2, day: 29 });
assert.throws(() => rules.parseDateDigits('20260230'), /valid/);
assert.throws(() => rules.parseMonthDayDigits('0230'), /valid/);
"""
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_age_changes_on_birthday(self):
        birth_date = date(1992, 10, 2)

        self.assertEqual(calculate_man_age(birth_date, date(2026, 10, 1)), 33)
        self.assertEqual(calculate_man_age(birth_date, date(2026, 10, 2)), 34)

    def test_leap_day_birthday_changes_on_march_first_in_common_year(self):
        birth_date = date(2000, 2, 29)

        self.assertEqual(calculate_man_age(birth_date, date(2026, 2, 28)), 25)
        self.assertEqual(calculate_man_age(birth_date, date(2026, 3, 1)), 26)

    def test_future_birth_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "future"):
            calculate_man_age(date(2027, 1, 1), date(2026, 12, 31))

    def test_invalid_iso_date_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "YYYY-MM-DD"):
            parse_iso_date("2026-02-30")


class BirthDatePrivacyTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        self.client = app.test_client()

    def test_solar_age_post_is_rejected_as_client_only(self):
        response = self.client.post(
            "/age",
            data={"birth_date": "1992-10-02", "calendar_type": "solar"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(response.get_json()["client_only"])

    def test_lunar_conversion_response_is_not_cached(self):
        response = self.client.post(
            "/age",
            data={"birth_date": "1992-10-02", "calendar_type": "lunar"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers.get("Cache-Control"), "no-store")

    def test_legacy_age_and_family_links_redirect_without_birth_data(self):
        age_response = self.client.get("/age?birth_date=921002&calendar_type=solar")
        family_response = self.client.get("/parent-child?s=encoded-private-input")

        self.assertEqual(age_response.status_code, 302)
        self.assertEqual(age_response.headers["Location"], "/age")
        self.assertEqual(family_response.status_code, 302)
        self.assertEqual(family_response.headers["Location"], "/parent-child")

    def test_hundred_day_dates_are_calculated_locally_without_query_fields(self):
        legacy_response = self.client.get("/100-day-calculator?year=2026&month=1&day=1")
        clean_response = self.client.get("/100-day-calculator")
        html = clean_response.get_data(as_text=True)
        javascript = Path("static/js/hundred-day-calculator.js").read_text(encoding="utf-8")

        self.assertEqual(302, legacy_response.status_code)
        self.assertEqual("/100-day-calculator", legacy_response.headers["Location"])
        self.assertNotIn('name="year"', html)
        self.assertNotIn('name="month"', html)
        self.assertNotIn('name="day"', html)
        self.assertIn("hundred-day-calculator.js", html)
        self.assertIn("addUtcDays(startDate, 99)", javascript)
        self.assertNotIn("fetch(", javascript)
        self.assertNotIn("js/clarity-init.js", html)
        self.assertIn('data-clarity-mask="true"', html)

    def test_exact_date_calculators_use_unambiguous_inputs_and_disable_session_replay(self):
        for path in ("/age", "/baby-months", "/parent-child", "/dog", "/cat", "/d-day", "/100-day-calculator", "/birthday-dday-calculator"):
            with self.subTest(path=path):
                html = self.client.get(path).get_data(as_text=True)
                self.assertNotIn("js/clarity-init.js", html)
                self.assertIn('data-clarity-mask="true"', html)

        age_html = self.client.get("/age").get_data(as_text=True)
        baby_html = self.client.get("/baby-months").get_data(as_text=True)
        family_js = Path("static/js/parent-child.js").read_text(encoding="utf-8")
        self.assertIn('maxlength="10"', age_html)
        self.assertIn('maxlength="10"', baby_html)
        self.assertIn('maxlength="10"', family_js)
        self.assertNotIn('maxlength="6"', age_html)
        self.assertNotIn('maxlength="6"', baby_html)

    def test_age_page_busts_cached_date_calculator_assets_and_has_no_six_digit_contract(self):
        age_html = self.client.get("/age").get_data(as_text=True)
        age_js = Path("static/js/age-calculator.js").read_text(encoding="utf-8")

        self.assertRegex(age_html, r'static/js/date-rules\.js\?v=[^" ]+')
        self.assertRegex(age_html, r'static/js/age-calculator\.js\?v=[^" ]+')
        self.assertNotIn("6자리", age_js)
        self.assertNotIn("bind6DigitInputEvents", age_js)
        self.assertNotIn("validateBirth6", age_js)

    def test_annual_age_uses_birth_year_only(self):
        response = self.client.get("/annual-age-calculator?birth_year=1992")
        html = response.get_data(as_text=True)

        self.assertEqual(response.status_code, 200)
        self.assertIn('name="birth_year"', html)
        self.assertNotIn('name="birth_date"', html)
        self.assertNotIn('name="month"', html)
        self.assertNotIn('name="day"', html)
        self.assertIn("1992년생", html)

    def test_calculator_javascript_never_builds_birth_date_share_queries(self):
        age_js = Path("static/js/age-calculator.js").read_text(encoding="utf-8")
        family_js = Path("static/js/parent-child.js").read_text(encoding="utf-8")

        self.assertNotIn("ShareCodec", age_js)
        self.assertNotIn("params.set('birth_date'", age_js)
        self.assertNotIn("ShareCodec", family_js)
        self.assertNotIn("params.set(`p${idx + 1}b`", family_js)
        self.assertIn("calculateSolarAgeLocally", age_js)

    def test_tracking_and_nginx_logs_drop_query_strings(self):
        analytics_js = Path("static/js/analytics.js").read_text(encoding="utf-8")
        nginx_conf = Path("nginx/agecalc.conf").read_text(encoding="utf-8")

        self.assertIn("page_location: cleanPageLocation", analytics_js)
        self.assertIn("page_path: window.location.pathname", analytics_js)
        self.assertIn("sensitiveQueryKeys", analytics_js)
        self.assertIn("url.searchParams.delete", analytics_js)
        self.assertIn("$request_method $uri $server_protocol", nginx_conf)
        self.assertNotIn("$request_method $request_uri $server_protocol", nginx_conf)
        self.assertNotIn("$http_referer", nginx_conf)
        self.assertNotIn("$request_uri", nginx_conf)

    def test_javascript_assets_are_revalidated_after_deployments(self):
        nginx_conf = Path("nginx/agecalc.conf").read_text(encoding="utf-8")

        self.assertIn("location /static/js/", nginx_conf)
        self.assertIn('add_header Cache-Control "no-cache, must-revalidate"', nginx_conf)

    def test_privacy_notice_describes_browser_and_lunar_processing(self):
        html = self.client.get("/privacy").get_data(as_text=True)

        self.assertIn("양력 생년월일은 브라우저 안에서 계산", html)
        self.assertIn("음력 생년월일은 양력 변환을 위해서만 서버로 전송", html)
        self.assertIn("공유 주소에는 생년월일을 넣지 않습니다", html)

    def test_profile_date_storage_requires_explicit_save_and_rejects_damaged_values(self):
        script = r"""
const assert = require('assert');
const profile = require('./static/js/profile-date.js');
const values = new Map();
const storage = {
  getItem(key) { return values.has(key) ? values.get(key) : null; },
  setItem(key, value) { values.set(key, value); },
  removeItem(key) { values.delete(key); }
};

assert.strictEqual(profile.loadProfileDate(storage), null);
profile.saveProfileDate('1992-10-02', storage);
assert.strictEqual(values.get('agecalc.profileBirthDate.v1'), '1992-10-02');
assert.strictEqual(profile.loadProfileDate(storage), '1992-10-02');
profile.clearProfileDate(storage);
assert.strictEqual(profile.loadProfileDate(storage), null);

values.set('agecalc.profileBirthDate.v1', '1992-99-99');
assert.strictEqual(profile.loadProfileDate(storage), null);
assert.strictEqual(values.has('agecalc.profileBirthDate.v1'), false);
assert.throws(() => profile.saveProfileDate('not-a-date', storage), /valid/);

const profileInput = { dataset: { profileDateInput: 'full', profileDateCalendar: 'solar' } };
const solarDocument = { querySelector() { return { value: 'solar' }; } };
const lunarDocument = { querySelector() { return { value: 'lunar' }; } };
assert.strictEqual(profile.canStoreProfileDate(profileInput, solarDocument), true);
assert.strictEqual(profile.canStoreProfileDate(profileInput, lunarDocument), false);
"""
        completed = subprocess.run(
            ["node", "-e", script],
            cwd=Path.cwd(),
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)

    def test_profile_date_controls_explain_device_storage_and_deletion(self):
        timeline_html = self.client.get("/life-timeline").get_data(as_text=True)
        age_html = self.client.get("/age").get_data(as_text=True)
        birthday_html = self.client.get("/birthday-dday-calculator").get_data(as_text=True)
        baby_html = self.client.get("/baby-months").get_data(as_text=True)

        self.assertIn('id="profile-date-consent"', timeline_html)
        self.assertIn('id="profile-date-clear"', timeline_html)
        self.assertIn("공용 기기", timeline_html)
        self.assertIn('id="profile-date-consent"', age_html)
        self.assertIn('id="profile-date-clear"', age_html)
        self.assertIn("공용 기기", age_html)
        self.assertIn("양력", age_html)
        self.assertIn('data-profile-date-input="full"', timeline_html)
        self.assertIn('data-profile-date-input="full"', age_html)
        self.assertIn('data-profile-date-input="month-day"', birthday_html)
        self.assertIn('id="profile-date-consent"', baby_html)
        self.assertIn('id="profile-date-clear"', baby_html)
        self.assertIn("공용 기기", baby_html)
        self.assertIn('data-profile-date-input="full"', baby_html)
        for html in (timeline_html, age_html, birthday_html, baby_html):
            self.assertIn("profile-date.js", html)

    def test_age_page_describes_solar_and_lunar_processing_accurately(self):
        html = self.client.get("/age").get_data(as_text=True)

        self.assertIn("양력 생년월일은 브라우저 안에서 계산합니다", html)
        self.assertIn("음력 생년월일은 양력 변환을 위해서만 서버로 전송", html)
        self.assertNotIn("입력값은 계산을 위해 서버로 전송되며 저장하지 않습니다", html)
        self.assertNotIn("계산을 위해 서버로 전송되지만 저장하지 않습니다", html)
        self.assertIn("윤달 선택은 지원하지 않으며 평달로 계산합니다", html)
        self.assertIn("올해 돌아오는 음력 생일의 양력 날짜를 찾는 기능은 아닙니다", html)

    def test_age_page_uses_editorial_review_date_for_reference_dates(self):
        html = self.client.get("/age").get_data(as_text=True)

        self.assertIn("기준 확인일: 2026-06-22", html)
        self.assertNotIn("마지막 기준 확인일: 2026-02-09", html)


if __name__ == "__main__":
    unittest.main()
