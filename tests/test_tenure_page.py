"""B9 scoped reference mode and privacy; existing locale policy remains distinct."""
import unittest
from unittest.mock import patch
from html.parser import HTMLParser
from app import app
from content.tool_finder import build_tool_finder_items

class TenurePageTests(unittest.TestCase):
    def setUp(self): self.client = app.test_client()
    def test_korean_opt_in_and_no_tracking(self):
        r = self.client.get('/days-between-dates'); text = r.get_data(as_text=True)
        self.assertIn('id="tenure-mode" type="checkbox"', text)
        self.assertNotIn('id="tenure-mode" type="checkbox" checked', text)
        self.assertIn('js/tenure-calculations.js', text)
        self.assertIn('id="tenure-result"', text)
        self.assertEqual('no-referrer', r.headers['Referrer-Policy'])
        for marker in ['js/analytics.js', 'js/cookie-consent.js', 'id="cookie-banner"', 'id="consent-defaults"', 'id="tracking-config"', 'pagead2.googlesyndication.com', 'coupang.com']:
            self.assertNotIn(marker, text)
    def test_unrelated_pages_keep_existing_policy(self):
        for path in ['/en/days-between-dates', '/ja/days-between-dates', '/es/days-between-dates', '/pt-br/days-between-dates', '/zh-cn/days-between-dates', '/date-add-subtract-calculator']:
            r=self.client.get(path); text=r.get_data(as_text=True)
            self.assertNotIn('id="tenure-mode"',text)
            self.assertNotIn('js/tenure-calculations.js',text)
            self.assertIn('js/analytics.js',text)
            self.assertEqual('strict-origin-when-cross-origin',r.headers['Referrer-Policy'])
    def test_query_policy_and_canonical_remain(self):
        r=self.client.get('/days-between-dates?start=2024-02-29&end=2025-02-28')
        self.assertEqual(200,r.status_code)
        self.assertNotIn('X-Robots-Tag',r.headers)
        self.assertNotIn('Cache-Control',r.headers)
        self.assertIn('rel="canonical" href="https://agecalc.cloud/days-between-dates"',r.get_data(as_text=True))
    def test_finder_aliases_reuse_existing_tool(self):
        items=build_tool_finder_items(); self.assertEqual(24,len(items))
        item=next(i for i in items if i['endpoint']=='days_between_dates')
        self.assertEqual('/days-between-dates',item['path'])
        self.assertTrue({'날짜 차이','기간','근속기간','재직기간','입사일'} <= set(item['aliases']))

    def test_verification_meta_survives_without_loader(self):
        with patch('app.ADSENSE_CLIENT_ID','ca-pub-scoped-test'), patch('app.GOOGLE_SITE_VERIFICATION','verification-scoped-test'):
            text=self.client.get('/days-between-dates').get_data(as_text=True)
        self.assertIn('name="google-adsense-account" content="ca-pub-scoped-test"',text)
        self.assertIn('name="google-site-verification" content="verification-scoped-test"',text)
        self.assertNotIn('adsbygoogle.js',text)

    def test_query_does_not_prefill_or_enable_mode(self):
        class Tags(HTMLParser):
            def __init__(self,text): super().__init__(); self.items=[]; self.feed(text)
            def handle_starttag(self,tag,attrs): self.items.append((tag,dict(attrs)))
        text=self.client.get('/days-between-dates?start=2024-02-29&end=2025-02-28&tenure=true').get_data(as_text=True)
        tags=Tags(text).items
        mode=next(a for t,a in tags if a.get('id')=='tenure-mode')
        self.assertNotIn('checked',mode)
        for tag,a in tags:
            if a.get('id') in ['start-year','start-day','end-year','end-day']:
                self.assertNotIn('value',a)
        inputs=next(a for t,a in tags if a.get('id')=='calculator-inputs')
        self.assertIn('disabled',inputs)
        self.assertIn('id="calculator-unavailable"',text)
