"""B12 integration contracts: public state, discovery and canonical boundaries."""
from datetime import date
import json
import re
import unittest
from unittest.mock import patch
from xml.etree import ElementTree


class KoreanHolidayPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        cls.module = app
        cls.client = app.app.test_client()

    def get_on(self, path, today=date(2026, 11, 1)):
        with patch.object(self.module, '_current_local_date', return_value=today):
            return self.client.get(path)

    def sitemap_urls(self, today):
        root = ElementTree.fromstring(self.get_on('/sitemap.xml', today).data)
        urls = set()
        for loc in root.findall('{*}sitemap/{*}loc'):
            child = ElementTree.fromstring(self.get_on(loc.text.removeprefix('https://agecalc.cloud'), today).data)
            urls.update(node.text for node in child.findall('{*}url/{*}loc'))
        return urls

    def test_new_route_and_full_official_dates(self):
        response = self.get_on('/korean-holiday-calendar')
        self.assertEqual(response.status_code, 200)
        text = response.get_data(as_text=True)
        self.assertIn('href="https://agecalc.cloud/korean-holiday-calendar"', text)
        for value in ('2027-05-01', '2027-05-03', '2027-07-17', '2027-07-19', '2027-12-27'):
            self.assertIn(value, text)
        self.assertNotIn('<input', text)
        self.assertNotIn('<form', text)
        self.assertNotIn('noindex', response.headers.get('X-Robots-Tag', ''))

    def test_query_and_slash_normalize_without_new_get_input(self):
        for path in ('/korean-holiday-calendar?year=2028', '/korean-holiday-calendar?x=a&x=b', '/korean-holiday-calendar/'):
            response = self.get_on(path)
            self.assertIn(response.status_code, (301, 302, 308))
            self.assertTrue(response.headers['Location'].endswith('/korean-holiday-calendar'))
            self.assertNotIn('?', response.headers['Location'])

    def test_deadline_inclusive_then_page_and_discovery_stop_together(self):
        good = date(2026, 11, 8); expired = date(2026, 11, 9)
        valid = self.get_on('/korean-holiday-calendar', good)
        stale = self.get_on('/korean-holiday-calendar', expired)
        self.assertEqual(valid.status_code, 200)
        self.assertEqual(stale.status_code, 200)
        self.assertNotIn('noindex', valid.headers.get('X-Robots-Tag', ''))
        self.assertEqual(stale.headers.get('X-Robots-Tag'), 'noindex, follow')
        self.assertEqual(stale.headers.get('Cache-Control'), 'no-store')
        self.assertNotIn('2027-05-03', stale.get_data(as_text=True))
        self.assertIn('제2026-0078호', stale.get_data(as_text=True))
        valid_urls = self.sitemap_urls(good); stale_urls = self.sitemap_urls(expired)
        self.assertEqual(valid_urls - stale_urls, {'https://agecalc.cloud/korean-holiday-calendar'})
        self.assertFalse(stale_urls - valid_urls)
        current_home = self.get_on('/', good).get_data(as_text=True)
        stale_home = self.get_on('/', expired).get_data(as_text=True)
        self.assertIn('href="/korean-holiday-calendar"', current_home)
        self.assertNotIn('href="/korean-holiday-calendar"', stale_home)

    def test_invalid_and_disabled_share_fail_closed_discovery(self):
        from content import korean_holidays
        for changes in ({'active': False}, {'next_review': 'bad'}):
            meta = dict(korean_holidays.HOLIDAY_METADATA); meta.update(changes)
            with patch.object(korean_holidays, 'HOLIDAY_METADATA', meta):
                response = self.get_on('/korean-holiday-calendar')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get('X-Robots-Tag'), 'noindex, follow')
                self.assertNotIn('2027-05-03', response.get_data(as_text=True))
                self.assertNotIn('https://agecalc.cloud/korean-holiday-calendar', self.sitemap_urls(date(2026,11,1)))
                self.assertNotIn('href="/korean-holiday-calendar"', self.get_on('/').get_data(as_text=True))

    def test_state_can_recover_without_mutating_static_registry(self):
        from content import korean_holidays
        from content.page_registry import STATIC_PAGE_REGISTRY
        before = [dict(p) for p in STATIC_PAGE_REGISTRY]
        self.get_on('/', date(2026,11,9))
        meta = dict(korean_holidays.HOLIDAY_METADATA); meta.update(verified_on='2026-11-09', next_review='2026-11-16')
        with patch.object(korean_holidays, 'HOLIDAY_METADATA', meta):
            response = self.get_on('/korean-holiday-calendar', date(2026,11,9))
            self.assertNotIn('noindex', response.headers.get('X-Robots-Tag', ''))
            self.assertIn('2027-05-03', response.get_data(as_text=True))
            self.assertIn('href="/korean-holiday-calendar"', self.get_on('/', date(2026,11,9)).get_data(as_text=True))
        self.assertEqual(before, list(STATIC_PAGE_REGISTRY))

    def test_editorial_review_matches_the_same_renewed_response_metadata(self):
        from content import korean_holidays
        from flask import template_rendered
        captured = []
        def record(sender, template, context, **extra):
            captured.append(context)
        meta = dict(korean_holidays.HOLIDAY_METADATA)
        meta.update(verified_on="2026-11-09", next_review="2026-11-16")
        template_rendered.connect(record, self.module.app)
        try:
            with patch.object(korean_holidays, "HOLIDAY_METADATA", meta):
                response = self.get_on("/korean-holiday-calendar", date(2026,11,9))
            self.assertEqual(response.status_code, 200)
            self.assertEqual(captured[-1]["editorial_metadata"]["reviewed_at"], "2026-11-09")
            self.assertEqual(captured[-1]["editorial_metadata"]["sources"][0]["checked_at"], "2026-11-09")
        finally:
            template_rendered.disconnect(record, self.module.app)


    def test_adsense_exclusion_preserves_consent_and_analytics(self):
        with patch.object(self.module, 'ADSENSE_CLIENT_ID', 'ca-pub-test-b12'), patch.object(self.module, 'ADSENSE_REVIEW_MODE', False):
            holiday = self.get_on('/korean-holiday-calendar').get_data(as_text=True)
            about = self.get_on('/about').get_data(as_text=True)
            self.assertFalse(self.module._adsense_is_enabled_for_path('/korean-holiday-calendar'))
            self.assertTrue(self.module._adsense_is_enabled_for_path('/about'))
            # Only this exact route is excluded, not its similarly named siblings.
            self.assertTrue(self.module._adsense_is_enabled_for_path('/korean-holiday-calendar-other'))
        self.assertNotIn('adsbygoogle.js', holiday)
        self.assertNotIn('name="google-adsense-account"', holiday)
        self.assertIn('adsbygoogle.js?client=ca-pub-test-b12', about)
        self.assertIn('name="google-adsense-account"', about)
        for html, expected_client in ((holiday, ''), (about, 'ca-pub-test-b12')):
            config = json.loads(re.search(r'<script id="tracking-config"[^>]*>(.*?)</script>', html, re.S).group(1))
            self.assertEqual(config['adsense_client'], expected_client)
            self.assertTrue(config['ga_measurement_id'])
            self.assertTrue(config['clarity_project_id'])
            self.assertIn('id="consent-defaults"', html)
            self.assertIn('js/analytics.js', html)
            self.assertIn('js/clarity-init.js', html)
        self.assertNotIn('/korean-holiday-calendar', self.module.PRIVACY_NO_THIRD_PARTY_PATHS)

    def test_month_navigation_uses_page_scoped_instant_document_scroll(self):
        html = self.get_on('/korean-holiday-calendar').get_data(as_text=True)
        self.assertIn('<html lang="ko" class="holiday-calendar-document">', html)
        with self.client.get('/static/css/korean-holiday-calendar.css') as response:
            css = response.get_data(as_text=True)
        self.assertRegex(css, r'html\.holiday-calendar-document\s*\{\s*scroll-behavior:\s*auto;\s*\}')
        for month in range(1, 13):
            self.assertIn(f'href="#holiday-month-{month}"', html)
            self.assertRegex(html, rf'<h3[^>]*id="holiday-month-{month}"[^>]*tabindex="-1"')
        self.assertNotIn('holiday-calendar-document', self.get_on('/about').get_data(as_text=True))
