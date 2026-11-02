"""Optional holiday UI preserves private Korean form and locale scope."""
import unittest
from html.parser import HTMLParser
from app import app


class Tags(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.items = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.items.append((tag, dict(attrs)))


class HolidayCountUITests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_optional_private_form_and_safe_render_contract(self):
        response = self.client.get('/days-between-dates?holiday=true&start=2027-01-01')
        text = response.get_data(as_text=True)
        attrs = next(attrs for _, attrs in Tags(text).items if attrs.get('id') == 'holiday-mode')
        self.assertNotIn('checked', attrs)
        self.assertNotIn('name', attrs)
        self.assertIn('id="holiday-result" hidden', text)
        self.assertIn('id="holiday-status" role="status"', text)
        self.assertIn('js/holiday-count.js', text)
        self.assertIn('날짜 입력 없이 공용 달력 자료만 조회', text)
        self.assertNotIn('adsbygoogle.js', text)
        self.assertNotIn('js/analytics.js', text)
        self.assertEqual(response.headers['Referrer-Policy'], 'no-referrer')
        self.assertNotIn('X-Robots-Tag', response.headers)
        self.assertIn('href="https://agecalc.cloud/days-between-dates"', text)

    def test_other_pages_unchanged(self):
        for path in ['/en/days-between-dates','/ja/days-between-dates','/es/days-between-dates','/pt-br/days-between-dates','/zh-cn/days-between-dates','/date-add-subtract-calculator']:
            with self.subTest(path=path):
                text = self.client.get(path).get_data(as_text=True)
                self.assertNotIn('id="holiday-mode"', text)
                self.assertNotIn('js/holiday-count.js', text)
