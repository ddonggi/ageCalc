import json
import re
import unittest
from html.parser import HTMLParser

from app import app
from content.page_registry import PUBLIC_PAGE_REGISTRY


class Elements(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.elements = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))


class TimeDurationPageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_public_document_and_structured_data(self):
        response = self.client.get('/time-duration-calculator')
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertIn('<html lang="ko"', html)
        self.assertIn('<title>시간 차이·하루 근무시간 계산기 | AgeCalc</title>', html)
        self.assertIn('href="https://agecalc.cloud/time-duration-calculator"', html)
        self.assertRegex(html, r'<h1[^>]*>시간 차이·하루 근무시간 계산기</h1>')
        self.assertNotRegex(html, r'<link[^>]+hreflang=')
        scripts = re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S)
        self.assertTrue(scripts)
        for script in scripts:
            json.loads(script)

    def test_privacy_page_excludes_third_party_scripts(self):
        import app as app_module
        import scripts.adsense_preflight as preflight
        self.assertFalse(app_module._adsense_is_enabled_for_path('/time-duration-calculator'))
        self.assertTrue(app_module._adsense_is_enabled_for_path('/age'))
        report = preflight.PreflightReport()
        response = type('Response', (), {'status_code': 200, 'headers': {}})()
        html = '<script src="https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-test"></script>'
        preflight._validate_public_page('/time-duration-calculator', response, html, 'ca-pub-test', report)
        self.assertIn('privacy_page_third_party_script', preflight.format_report(report))

    def test_queries_are_not_restored_and_are_noindex(self):
        for query in ['start=09%3A17&end=18%3A43&break=47', 'unexpected=private-sentinel', 'nextDay=true']:
            with self.subTest(query=query):
                response = self.client.get('/time-duration-calculator?' + query)
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                self.assertIn('noindex', response.headers.get('X-Robots-Tag', ''))
                self.assertIn('href="https://agecalc.cloud/time-duration-calculator"', html)
                self.assertNotIn('private-sentinel', html)
                self.assertNotIn('value="09:17"', html)
                self.assertNotIn('value="18:43"', html)

    def test_inputs_cannot_submit_and_tracking_loaders_absent(self):
        html = self.client.get('/time-duration-calculator').get_data(as_text=True)
        elements = Elements(html).elements
        inputs = [attrs for tag, attrs in elements if tag == 'input']
        self.assertEqual(2, sum(attrs.get('type') == 'time' for attrs in inputs))
        for attrs in inputs:
            self.assertNotIn('name', attrs)
        buttons = [attrs for tag, attrs in elements if tag == 'button']
        self.assertTrue(buttons)
        self.assertTrue(all(attrs.get('type') == 'button' for attrs in buttons))
        self.assertIn('data-clarity-mask="true"', html)
        self.assertIn('<noscript>', html)
        for loader in ['clarity-init.js', 'clarity.ms', 'googletagmanager.com', 'google-analytics.com']:
            self.assertNotIn(loader, html)

    def test_single_registry_and_sitemap_entry(self):
        entries = [page for page in PUBLIC_PAGE_REGISTRY if page['path'] == '/time-duration-calculator']
        self.assertEqual(1, len(entries))
        root = self.client.get('/sitemap.xml').get_data(as_text=True)
        urls = re.findall(r'<loc>(.*?)</loc>', root)
        if '<sitemapindex' in root:
            xml = ''.join(self.client.get(url.removeprefix('https://agecalc.cloud')).get_data(as_text=True) for url in urls)
        else:
            xml = root
        self.assertEqual(1, xml.count('<loc>https://agecalc.cloud/time-duration-calculator</loc>'))
        self.assertEqual(404, self.client.get('/work-hours-calculator', follow_redirects=True).status_code)

    def test_date_pages_link_to_time_tool_and_back(self):
        html = self.client.get('/time-duration-calculator').get_data(as_text=True)
        for path in ['/days-between-dates', '/date-add-subtract-calculator']:
            with self.subTest(path=path):
                self.assertIn(f'href="{path}"', html)
                self.assertIn('href="/time-duration-calculator"', self.client.get(path).get_data(as_text=True))

    def test_existing_get_contracts_survive(self):
        response = self.client.get('/100-day-calculator?start_date=20240229')
        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertIn('noindex', response.headers.get('X-Robots-Tag', ''))
        self.assertIn('2024.02.29 기준 100일 안내', html)
        self.assertIn('2025.03.01', html)
        self.assertIn('백일·첫돌·천일 함께 보기', html)


if __name__ == '__main__':
    unittest.main()
