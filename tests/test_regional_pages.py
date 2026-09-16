"""Regional calculators expose only their intended locale documents."""
import re
import unittest
from unittest.mock import patch

from app import app


URLS = {
    '/lunar-birthday-calculator': ('ko', '음력 생일'),
    '/ja/business-days-calculator': ('ja', '営業日'),
    '/pt-br/business-days-calculator': ('pt-BR', 'dias úteis'),
    '/ja/school-year-calculator': ('ja', '入学'),
    '/en/date-of-birth-calculator': ('en', 'Date of Birth'),
    '/pt-br/date-of-birth-calculator': ('pt-BR', 'data de nascimento'),
    '/ja/japanese-era-converter': ('ja', '和暦'),
}


class RegionalPageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_seven_get_documents_are_ssr_indexable_and_canonical(self):
        for path, (locale, phrase) in URLS.items():
            with self.subTest(path=path):
                response = self.client.get(path)
                html = response.get_data(as_text=True)
                self.assertEqual(200, response.status_code)
                self.assertIn(f'<html lang="{locale}"', html)
                self.assertIn(phrase, html)
                self.assertIn('<form', html)
                self.assertIn('method="post"', html)
                self.assertIn(f'<link rel="canonical" href="https://agecalc.cloud{path}"', html)
                self.assertNotIn('noindex', response.headers.get('X-Robots-Tag', ''))

    def test_pages_exist_only_for_supported_locales(self):
        unsupported = [
            '/en/business-days-calculator', '/ko/business-days-calculator',
            '/pt-br/school-year-calculator', '/en/school-year-calculator',
            '/ja/date-of-birth-calculator', '/date-of-birth-calculator',
            '/en/japanese-era-converter', '/ja/lunar-birthday-calculator',
        ]
        for path in unsupported:
            with self.subTest(path=path):
                self.assertEqual(404, self.client.get(path, follow_redirects=True).status_code)

    def test_real_equivalents_alone_have_reciprocal_hreflang(self):
        expected = {
            '/ja/business-days-calculator': {'ja': 'https://agecalc.cloud/ja/business-days-calculator', 'pt-BR': 'https://agecalc.cloud/pt-br/business-days-calculator'},
            '/pt-br/business-days-calculator': {'ja': 'https://agecalc.cloud/ja/business-days-calculator', 'pt-BR': 'https://agecalc.cloud/pt-br/business-days-calculator'},
            '/en/date-of-birth-calculator': {'en': 'https://agecalc.cloud/en/date-of-birth-calculator', 'pt-BR': 'https://agecalc.cloud/pt-br/date-of-birth-calculator'},
            '/pt-br/date-of-birth-calculator': {'en': 'https://agecalc.cloud/en/date-of-birth-calculator', 'pt-BR': 'https://agecalc.cloud/pt-br/date-of-birth-calculator'},
        }
        for path in URLS:
            html = self.client.get(path).get_data(as_text=True)
            actual = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', html))
            self.assertEqual(expected.get(path, {}), actual, path)

    def test_post_results_are_private_and_server_rendered(self):
        cases = [
            ('/en/date-of-birth-calculator', {'reference': '2026-09-15', 'age': '30'}, '1995-09-16'),
            ('/pt-br/date-of-birth-calculator', {'reference': '2026-09-15', 'age': '30'}, '1996-09-15'),
            ('/ja/school-year-calculator', {'birth': '2020-04-01', 'gap': '0', 'course': '4'}, '2026年4月'),
            ('/ja/japanese-era-converter', {'mode': 'to_era', 'date': '2019-05-01'}, '令和元年5月1日'),
            ('/ja/business-days-calculator', {'mode': 'count', 'start': '2026-01-01', 'end': '2026-01-05', 'include_end': '1', 'excluded': ''}, '2'),
            ('/pt-br/business-days-calculator', {'mode': 'count', 'start': '2026-09-05', 'end': '2026-09-08', 'include_end': '1', 'excluded': ''}, '1'),
            ('/lunar-birthday-calculator', {'month': '1', 'day': '1', 'reference': '2026-01-01'}, '2026-02-17'),
        ]
        for path, form, expected in cases:
            with self.subTest(path=path):
                response = self.client.post(path, data=form)
                html = response.get_data(as_text=True)
                self.assertEqual(200, response.status_code)
                self.assertIn(expected, html)
                self.assertIn('noindex', response.headers.get('X-Robots-Tag', ''))
                self.assertEqual('no-store', response.headers.get('Cache-Control'))

        localized_dates = {
            '/en/date-of-birth-calculator': (
                {'reference': '2026-09-15', 'age': '30'},
                'September 16, 1995',
            ),
            '/pt-br/date-of-birth-calculator': (
                {'reference': '2026-09-15', 'age': '30'},
                '16/09/1995',
            ),
            '/lunar-birthday-calculator': (
                {'month': '1', 'day': '1', 'reference': '2026-01-01'},
                '2026년 2월 17일',
            ),
        }
        for path, (form, expected) in localized_dates.items():
            with self.subTest(localized_path=path):
                self.assertIn(expected, self.client.post(path, data=form).get_data(as_text=True))

    def test_bad_post_shows_error_without_reflecting_unknown_fields(self):
        response = self.client.post('/en/date-of-birth-calculator', data={
            'reference': 'not-a-date', 'age': '30', 'unknown': '<script>alert(1)</script>'
        })
        self.assertEqual(400, response.status_code)
        html = response.get_data(as_text=True)
        self.assertNotIn('<script>alert(1)</script>', html)
        self.assertIn('noindex', response.headers.get('X-Robots-Tag', ''))

    def test_review_sitemap_has_exact_regional_documents(self):
        with patch('app.ADSENSE_REVIEW_MODE', True):
            index = self.client.get('/sitemap.xml').get_data(as_text=True)
            urls = []
            for sitemap_url in re.findall(r'<loc>(.*?)</loc>', index):
                child = self.client.get(sitemap_url.removeprefix('https://agecalc.cloud')).get_data(as_text=True)
                urls.extend(re.findall(r'<loc>(.*?)</loc>', child))
        expected = {'https://agecalc.cloud' + path for path in URLS}
        self.assertEqual(expected, {url for url in urls if any(slug in url for slug in (
            'lunar-birthday-calculator', 'business-days-calculator', 'school-year-calculator',
            'date-of-birth-calculator', 'japanese-era-converter'))})
        self.assertEqual(len(urls), len(set(urls)))

    def test_existing_locale_pages_link_to_the_new_tools(self):
        expectations = {
            '/birthday-dday-calculator': ('/lunar-birthday-calculator',),
            '/en/age-calculator': ('/en/date-of-birth-calculator',),
            '/ja/age-calculator': (
                '/ja/business-days-calculator',
                '/ja/school-year-calculator',
                '/ja/japanese-era-converter',
            ),
            '/pt-br/age-calculator': (
                '/pt-br/business-days-calculator',
                '/pt-br/date-of-birth-calculator',
            ),
        }
        for source, targets in expectations.items():
            html = self.client.get(source).get_data(as_text=True)
            for target in targets:
                with self.subTest(source=source, target=target):
                    self.assertIn(f'href="{target}"', html)


if __name__ == '__main__':
    unittest.main()
