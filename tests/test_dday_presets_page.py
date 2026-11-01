"""B11 real-render boundary: existing GET, official-only payload, privacy and discovery."""
import json
import re
import unittest
from datetime import date
from unittest.mock import patch

import app as app_module
from content.page_registry import PRIVACY_NO_THIRD_PARTY_PATHS
from content.tool_finder import build_tool_finder_items


class DDayPresetPageTests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()
        self.clock = patch.object(app_module, '_current_local_date', return_value=date(2026, 10, 31))
        self.clock.start()
        self.addCleanup(self.clock.stop)

    def payload(self, html):
        return json.loads(re.search(r'<script[^>]*id="dday-exam-presets"[^>]*>(.*?)</script>', html, re.S).group(1))

    def test_korean_privacy_registration_and_existing_finder_entry(self):
        self.assertIn('/d-day', PRIVACY_NO_THIRD_PARTY_PATHS)
        self.assertNotIn('/en/d-day', PRIVACY_NO_THIRD_PARTY_PATHS)
        items = build_tool_finder_items()
        self.assertEqual(len(items), 25)
        match = [x for x in items if x['endpoint'] == 'd_day']
        self.assertEqual(len(match), 1)
        self.assertEqual(match[0]['path'], '/d-day')
        self.assertTrue({'수능','시험일','수능디데이','수능100일'}.issubset(match[0]['aliases']))

    def test_real_render_keeps_only_official_payload_and_disabled_no_js_buttons(self):
        html = self.client.get('/d-day').get_data(as_text=True)
        rows = self.payload(html)
        self.assertEqual([(x['id'],x['date_digits'],x['d100_date']) for x in rows], [
            ('csat-academic-2027','20261119','2026-08-11'),
            ('csat-academic-2028','20271118','2027-08-10')])
        self.assertEqual(len(re.findall(r'<button[^>]*data-dday-preset="[^"]+"[^>]*disabled',html)),2)
        self.assertIn('for="dday-label"',html)
        self.assertIn('datetime="2026-10-31"',html)
        self.assertIn('action="/d-day#dday-result-container" method="get"',html)
        self.assertNotIn('name="preset"',html)

    def test_get_values_stay_in_form_not_official_helper(self):
        response = self.client.get('/d-day', query_string={'date':'20261119','mode':'since','label':'PRIVATE-B11-LABEL'})
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code,200)
        self.assertIn('value="PRIVATE-B11-LABEL"',html)
        self.assertIn('2026.11.19',html)
        self.assertIn('D-19',html)
        self.assertNotIn('PRIVATE-B11-LABEL',json.dumps(self.payload(html)))
        self.assertIn('noindex',response.headers['X-Robots-Tag'])
        self.assertEqual(response.headers['Cache-Control'],'no-store')
        self.assertEqual(response.headers['Referrer-Policy'],'no-referrer')
        for query in ['date=20261119&mode=until&label=a&preset=x','date=20261119&date=20271118&mode=until&label=a','date=20260230&mode=until&label=a']:
            result=self.client.get('/d-day?'+query)
            self.assertEqual((result.status_code,result.headers['Location']),(302,'/d-day'))

    def test_official_editorial_review_matches_schedule_sources(self):
        from content.editorial_metadata import editorial_metadata_for
        from content.page_registry import find_page
        metadata=editorial_metadata_for(find_page('d_day'))
        self.assertEqual(metadata['reviewed_at'],'2026-10-31')
        self.assertEqual(len(metadata['sources']),2)
        self.assertTrue(all(s['institution']=='교육부' for s in metadata['sources']))

    def test_review_gate_is_render_time_snapshot(self):
        with patch.object(app_module,'_current_local_date',return_value=date(2026,11,13)):
            rows=self.payload(self.client.get('/d-day').get_data(as_text=True))
        self.assertEqual((rows[0]['state'],rows[0]['can_fill']),('needs_review',False))
        self.assertTrue(rows[1]['can_fill'])

    def test_no_tracking_or_consent_loaders_even_when_preaccepted(self):
        self.client.set_cookie('cookieConsent','accepted')
        response=self.client.get('/d-day?date=20261119&mode=until&label=PRIVATE-B11-LABEL')
        html=response.get_data(as_text=True)
        for marker in ['js/analytics.js','js/cookie-consent.js','id="tracking-config"','id="consent-defaults"','id="cookie-banner"','pagead2.googlesyndication.com/pagead/js','link.coupang.com']:
            self.assertNotIn(marker,html)
        self.assertIn('google-site-verification',self.client.get('/d-day').get_data(as_text=True)) if app_module.GOOGLE_SITE_VERIFICATION else None

    def test_foreign_page_does_not_gain_korean_presets_or_referrer_policy(self):
        response=self.client.get('/en/d-day')
        self.assertEqual(response.status_code,200)
        self.assertNotIn('dday-exam-presets',response.get_data(as_text=True))
        self.assertEqual(response.headers['Referrer-Policy'],'strict-origin-when-cross-origin')
