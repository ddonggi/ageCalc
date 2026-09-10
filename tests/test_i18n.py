"""Public localization contracts: preserve Korean URLs and expose real alternates."""
import json
import re
import unittest
from html.parser import HTMLParser
from unittest.mock import patch

from app import app
from content.i18n import catalog, validate_translations
from tests.i18n_expected import REVIEW_URLS
from content.i18n import PAGE_BY_KEY, language_links, localized_sitemap_entries, localized_url, i18n_context
from flask import g


PATHS = {
    '/days-between-dates': 'days-between-dates',
    '/date-add-subtract-calculator': 'date-add-subtract-calculator',
    '/age': 'age-calculator',
    '/birthday-dday-calculator': 'birthday-dday-calculator',
    '/d-day': 'd-day',
    '/baby-months': 'baby-months',
    '/100-day-calculator': '100-day-calculator',
    '/age-gap-calculator': 'age-gap-calculator',
}
LANGUAGES = {'ko': '', 'en': 'en', 'ja': 'ja', 'es': 'es', 'pt-BR': 'pt-br', 'zh-CN': 'zh-cn'}


class Markup(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.tags = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def attrs(self, tag, **match):
        return [a for t, a in self.tags if t == tag and all(a.get(k) == v for k, v in match.items())]


class LocalizedPageTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_language_clusters_have_self_canonical_and_reciprocal_real_alternates(self):
        for korean_path, slug in PATHS.items():
            expected = {lang: 'https://agecalc.cloud' + (f'/{prefix}/{slug}' if prefix else korean_path)
                        for lang, prefix in LANGUAGES.items()}
            for lang, url in expected.items():
                with self.subTest(path=url):
                    response = self.client.get(url.replace('https://agecalc.cloud', ''))
                    self.assertEqual(200, response.status_code)
                    markup = Markup(response.get_data(as_text=True))
                    self.assertEqual(lang, markup.attrs('html')[0]['lang'])
                    self.assertEqual([url], [a['href'] for a in markup.attrs('link', rel='canonical')])
                    self.assertEqual(expected, {a['hreflang']: a['href'] for a in markup.attrs('link', rel='alternate') if 'hreflang' in a})
                    self.assertEqual(url, markup.attrs('meta', property='og:url')[0]['content'])
                    self.assertNotIn('noindex', response.headers.get('X-Robots-Tag', ''))

    def test_global_content_is_rendered_without_javascript(self):
        titles = {'en': 'Age Calculator', 'ja': '年齢計算', 'es': 'Calculadora de edad',
                  'pt-br': 'Calculadora de idade', 'zh-cn': '年龄计算器'}
        for prefix, title in titles.items():
            response = self.client.get(f'/{prefix}/age-calculator')
            html = response.get_data(as_text=True)
            self.assertEqual(200, response.status_code)
            self.assertIn(title, html)
            self.assertIn('<h1>', html)
            self.assertIn('<h2', html)
            self.assertNotIn('현재 나이로 가능한 권리', html)
            self.assertNotIn('coupang.com', html)
            for raw in re.findall(r'<script[^>]+type="application/ld\+json"[^>]*>(.*?)</script>', html, re.S):
                json.loads(raw)

    def test_unsupported_paths_do_not_redirect_to_another_language(self):
        for path in ['/fr/age-calculator', '/abc/age-calculator', '/ko/age-calculator',
                     '/en/annual-age-calculator', '/en/age', '/ja/korean-age-guide']:
            with self.subTest(path=path):
                self.assertEqual(404, self.client.get(path).status_code)
        self.assertEqual(301, self.client.get('/en/age-calculator/').status_code)
        self.assertEqual('/en/age-calculator', self.client.get('/en/age-calculator/').headers['Location'])

    def test_language_does_not_follow_accept_language_or_query(self):
        response = self.client.get('/en/age-calculator?lang=ja', headers={'Accept-Language': 'ja'})
        self.assertEqual(200, response.status_code)
        self.assertEqual('en', Markup(response.get_data(as_text=True)).attrs('html')[0]['lang'])

    def test_sitemap_adds_only_supported_localized_urls(self):
        with patch('app.ADSENSE_REVIEW_MODE', True):
            root = self.client.get('/sitemap.xml').get_data(as_text=True)
            urls = []
            for url in re.findall(r'<loc>(.*?)</loc>', root):
                xml = self.client.get(url.replace('https://agecalc.cloud', '')).get_data(as_text=True)
                urls.extend(re.findall(r'<loc>(.*?)</loc>', xml))
        expected = {f'https://agecalc.cloud/{prefix}/{slug}' for prefix in list(LANGUAGES.values())[1:] for slug in PATHS.values()}
        localized = {url for url in urls if any(f'/{prefix}/' in url for prefix in list(LANGUAGES.values())[1:])}
        self.assertEqual(expected, localized)
        self.assertEqual(REVIEW_URLS, set(urls))
        self.assertEqual(len(urls), len(set(urls)))
        self.assertIn('https://agecalc.cloud/age', urls)
        self.assertNotIn('https://agecalc.cloud/age-calculator', urls)

    def test_catalog_validation_accepts_whitespace_duration_separators(self):
        validate_translations()

    def test_korean_only_pages_offer_navigation_without_false_seo_alternates(self):
        for path in ('/', '/annual-age-calculator', '/korean-age-guide', '/about'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                menu = re.search(r'<details class="language-switcher">(.*?)</details>', html, re.S).group(1)
                links = Markup(menu).attrs('a')
                self.assertEqual(6, len(links))
                self.assertEqual(path, next(a['href'] for a in links if a['hreflang'] == 'ko'))
                self.assertEqual('/en/age-calculator', next(a['href'] for a in links if a['hreflang'] == 'en'))
                self.assertIn('language-fallback-notice', menu)
                self.assertFalse([a for a in Markup(html).attrs('link', rel='alternate') if 'hreflang' in a])
                self.assertEqual('https://agecalc.cloud' + path, Markup(html).attrs('link', rel='canonical')[0]['href'])

    def test_equivalent_page_language_navigation_keeps_the_calculator(self):
        html = self.client.get('/ja/birthday-dday-calculator').get_data(as_text=True)
        menu = re.search(r'<details class="language-switcher">(.*?)</details>', html, re.S).group(1)
        links = Markup(menu).attrs('a')
        self.assertEqual('/birthday-dday-calculator', next(a['href'] for a in links if a['hreflang'] == 'ko'))
        self.assertEqual('/en/birthday-dday-calculator', next(a['href'] for a in links if a['hreflang'] == 'en'))
        self.assertNotIn('language-fallback-notice', menu)

    def test_catalog_validation_rejects_missing_text_and_mismatched_placeholders(self):
        from copy import deepcopy
        broken = deepcopy(catalog('es'))
        broken['common']['calculate'] = ''
        real_catalog = catalog
        with patch('content.i18n.catalog', side_effect=lambda code: broken if code == 'es' else real_catalog(code)):
            with self.assertRaisesRegex(ValueError, 'Invalid translation'):
                validate_translations()
        broken['common']['calculate'] = 'Calcular'
        broken['common']['units']['year']['one'] = '{count} año'
        with patch('content.i18n.catalog', side_effect=lambda code: broken if code == 'es' else real_catalog(code)):
            with self.assertRaisesRegex(ValueError, 'Invalid translation'):
                validate_translations()

    def test_page_specific_locales_and_features_control_links_and_context(self):
        page = PAGE_BY_KEY['age']
        with patch.dict(page, {'supported_locales': ('ko', 'en'), 'locale_features': {'en': {'year_age': True}}}):
            self.assertEqual(['ko', 'en'], [link['locale'] for link in language_links(page, 'https://agecalc.cloud')])
            self.assertEqual(['/age', '/en/age-calculator'], [p['path'] for p in localized_sitemap_entries([page])])
            with self.assertRaises(ValueError):
                localized_url('age', 'ja')
            with app.test_request_context('/en/age-calculator'):
                g.locale_code = 'en'
                self.assertTrue(i18n_context(page, 'https://agecalc.cloud')['features']['year_age'])

    def test_date_shift_calculator_has_six_indexable_equivalent_pages(self):
        page = PAGE_BY_KEY['date_add_subtract']
        paths = [entry['path'] for entry in localized_sitemap_entries([page])]
        self.assertEqual([
            '/date-add-subtract-calculator',
            '/en/date-add-subtract-calculator',
            '/ja/date-add-subtract-calculator',
            '/es/date-add-subtract-calculator',
            '/pt-br/date-add-subtract-calculator',
            '/zh-cn/date-add-subtract-calculator',
        ], paths)
        for path in paths:
            response = self.client.get(path)
            self.assertEqual(200, response.status_code, path)
            markup = Markup(response.get_data(as_text=True))
            self.assertEqual(1, len(markup.attrs('h1')))
            self.assertEqual(6, len(markup.attrs('link', rel='alternate')))
            self.assertNotIn('noindex', response.headers.get('X-Robots-Tag', ''))

    def test_localized_tool_renders_when_age_does_not_support_its_language(self):
        with patch.dict(PAGE_BY_KEY['age'], {'supported_locales': ('ko', 'en')}), \
                patch.dict(app.config, {'PROPAGATE_EXCEPTIONS': False}):
            validate_translations()
            response = self.client.get('/ja/baby-months')
            self.assertEqual(200, response.status_code)
            markup = Markup(response.get_data(as_text=True))
            self.assertEqual('/ja/baby-months', markup.attrs('a', **{'class': 'brand'})[0]['href'])
            self.assertNotIn('/ja/age-calculator', [a.get('href') for a in markup.attrs('a')])


if __name__ == '__main__':
    unittest.main()
