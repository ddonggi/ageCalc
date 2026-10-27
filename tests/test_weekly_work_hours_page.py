"""Weekly page publication and privacy contracts, independently expected URLs."""
import json
import re
import unittest
from html.parser import HTMLParser
from app import app
from content.page_registry import PUBLIC_PAGE_REGISTRY, PRIVACY_NO_THIRD_PARTY_PATHS

PATH = '/weekly-work-hours-calculator'
class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.elements = []; self.feed(html)
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

class WeeklyWorkHoursPageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
    def test_canonical_korean_only_and_schema(self):
        response = self.client.get(PATH)
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertIn('<html lang="ko"', html)
        self.assertIn('href="https://agecalc.cloud' + PATH + '"', html)
        self.assertNotRegex(html, r'<link[^>]+hreflang=')
        self.assertEqual(1, len(re.findall(r'<h1\b', html)))
        for data in re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
            json.loads(data)
        for locale in ('en','ja','es','pt-br','zh-cn'):
            self.assertEqual(404, self.client.get('/' + locale + PATH).status_code)
    def test_no_query_restore_and_no_store(self):
        for query in ('start=09%3A17&end=18%3A43', 'private=weekly-private-sentinel'):
            response = self.client.get(PATH + '?' + query)
            self.assertEqual(200, response.status_code)
            self.assertIn('noindex', response.headers.get('X-Robots-Tag',''))
            self.assertIn('no-store', response.headers.get('Cache-Control',''))
            html = response.get_data(as_text=True)
            self.assertNotIn('weekly-private-sentinel', html)
            self.assertNotIn('value="09:17"', html)
    def test_private_boundary_and_disabled_inputs(self):
        self.assertIn(PATH, PRIVACY_NO_THIRD_PARTY_PATHS)
        html = self.client.get(PATH).get_data(as_text=True)
        elements = Elements(html).elements
        inputs = [a for t,a in elements if t == 'input']
        self.assertEqual(14, sum(a.get('type') == 'time' for a in inputs))
        self.assertEqual(7, sum(a.get('type') == 'checkbox' for a in inputs))
        self.assertEqual(28, len(inputs))
        for attrs in inputs: self.assertNotIn('name', attrs)
        fieldset = next(a for t,a in elements if a.get('id') == 'weekly-inputs')
        self.assertIn('disabled', fieldset)
        self.assertIn('<noscript>', html)
        self.assertIn('data-disable-analytics="true"', html)
        self.assertIn('data-disable-clarity="true"', html)
        for loader in ('clarity-init.js','clarity.ms','googletagmanager.com','google-analytics.com','pagead2.googlesyndication.com'):
            self.assertNotIn(loader, html)
        self.assertEqual(405, self.client.post(PATH, data={'start':'09:17'}).status_code)
    def test_registry_and_sitemap_single_public_path(self):
        entries = [p for p in PUBLIC_PAGE_REGISTRY if p['path'] == PATH]
        self.assertEqual(1, len(entries))
        self.assertEqual(('ko',), entries[0]['supported_locales'])
        xml = self.client.get('/sitemap.xml').get_data(as_text=True)
        if '<sitemapindex' in xml:
            urls = re.findall(r'<loc>(.*?)</loc>', xml)
            xml = ''.join(self.client.get(u.removeprefix('https://agecalc.cloud')).get_data(as_text=True) for u in urls)
        self.assertEqual(1, xml.count('<loc>https://agecalc.cloud' + PATH + '</loc>'))
    def test_existing_daily_link_and_home_discovery(self):
        self.assertIn('href="' + PATH + '"', self.client.get('/time-duration-calculator').get_data(as_text=True))
        self.assertIn('href="' + PATH + '"', self.client.get('/').get_data(as_text=True))
        self.assertIn('href="/time-duration-calculator"', self.client.get(PATH).get_data(as_text=True))

if __name__ == '__main__': unittest.main()
