"""World time page publication and privacy contracts, independently expected URLs."""
import json
import re
import unittest
from html.parser import HTMLParser
from app import app
from content.page_registry import PUBLIC_PAGE_REGISTRY, PRIVACY_NO_THIRD_PARTY_PATHS

PATH = '/world-time-converter'
class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__(); self.elements = []; self.feed(html)
    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

class WorldTimePageTests(unittest.TestCase):
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
        for query in ('start=09%3A17&end=18%3A43', 'private=world-private-sentinel'):
            response = self.client.get(PATH + '?' + query)
            self.assertEqual(200, response.status_code)
            self.assertIn('noindex', response.headers.get('X-Robots-Tag',''))
            self.assertIn('no-store', response.headers.get('Cache-Control',''))
            html = response.get_data(as_text=True)
            self.assertNotIn('world-private-sentinel', html)
            self.assertNotIn('value="09:17"', html)
    def test_private_boundary_and_disabled_inputs(self):
        self.assertIn(PATH, PRIVACY_NO_THIRD_PARTY_PATHS)
        self.assertEqual('no-referrer', self.client.get(PATH).headers.get('Referrer-Policy'))
        html = self.client.get(PATH).get_data(as_text=True)
        elements = Elements(html).elements
        inputs = [a for t,a in elements if t == 'input']
        self.assertEqual(2, len(inputs))
        self.assertEqual({'date', 'time'}, {a.get('type') for a in inputs})
        date = next(a for a in inputs if a.get('type') == 'date')
        self.assertEqual('2020-01-01', date['min'])
        self.assertEqual('2030-12-31', date['max'])
        self.assertNotIn('value', date)
        selects = [a for t,a in elements if t == 'select']
        self.assertEqual(1, len(selects))
        self.assertNotIn('name', selects[0])
        options = [a for t,a in elements if t == 'option']
        self.assertEqual({'0', '540'}, {a['value'] for a in options})
        self.assertIn('selected', next(a for a in options if a['value'] == '540'))
        self.assertTrue(any(t == 'caption' for t,a in elements))
        self.assertTrue(any(a.get('tabindex') == '0' and a.get('role') == 'region' for t,a in elements))
        for attrs in inputs: self.assertNotIn('name', attrs)
        fieldset = next(a for t,a in elements if a.get('id') == 'world-inputs')
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
        self.assertIn('href="' + PATH + '"', self.client.get('/').get_data(as_text=True))
        self.assertIn('href="/time-duration-calculator"', self.client.get(PATH).get_data(as_text=True))

if __name__ == '__main__': unittest.main()
