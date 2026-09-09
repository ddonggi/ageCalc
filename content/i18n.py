"""Small SSR localization layer built on the existing public page registry."""
from functools import lru_cache
import json
from pathlib import Path
import re

from flask import g, redirect, render_template

from content.locale_config import LOCALE_CONFIG, LOCALE_FEATURES
from content.page_registry import PUBLIC_PAGE_REGISTRY

TRANSLATION_ROOT = Path(__file__).resolve().parent.parent / 'translations'
PAGE_BY_KEY = {page['key']: page for page in PUBLIC_PAGE_REGISTRY}


@lru_cache(maxsize=None)
def catalog(locale):
    if locale not in LOCALE_CONFIG:
        raise ValueError('Unsupported locale')
    return json.loads((TRANSLATION_ROOT / f'{locale}.json').read_text(encoding='utf-8'))


def supported_locales(page):
    return tuple(page.get('supported_locales', ('ko',)))


def localized_url(page_key, locale):
    page = PAGE_BY_KEY[page_key]
    if locale not in supported_locales(page):
        raise ValueError(f'{page_key} does not support {locale}')
    if locale == 'ko':
        return page['path']
    return f"/{LOCALE_CONFIG[locale]['prefix']}/{page['localization']['slug']}"


def language_links(page, base_url):
    if not page or len(supported_locales(page)) < 2:
        return []
    return [
        {'locale': code, 'hreflang': LOCALE_CONFIG[code]['hreflang'],
         'name': LOCALE_CONFIG[code]['name'], 'path': localized_url(page['key'], code),
         'url': base_url + localized_url(page['key'], code)}
        for code in supported_locales(page)
    ]


def navigation_language_links(page):
    """Site navigation may use a fallback; SEO alternates never do."""
    links = []
    for code, config in LOCALE_CONFIG.items():
        equivalent = page is not None and code in supported_locales(page)
        target = page if equivalent else next(
            (candidate for candidate in (PAGE_BY_KEY['age'], *PUBLIC_PAGE_REGISTRY)
             if code in supported_locales(candidate) and candidate.get('localization')), None)
        if target is None:
            continue
        path = localized_url(target['key'], code)
        if code == 'ko' and not equivalent:
            path = '/'
        links.append({'locale': code, 'hreflang': config['hreflang'],
                      'name': config['name'], 'path': path,
                      'fallback': not equivalent and code != 'ko'})
    return links


def i18n_context(page, base_url):
    locale = getattr(g, 'locale_code', 'ko')
    return {
        'locale_code': locale,
        'locale_config': LOCALE_CONFIG[locale],
        'features': {**LOCALE_FEATURES[locale], **((page or {}).get('locale_features', {}).get(locale, {}))},
        'language_links': language_links(page, base_url),
        'navigation_language_links': navigation_language_links(page),
        'language_label': catalog(locale)['common']['language'],
        'language_fallback_notice': catalog(locale)['common']['language_fallback_notice'],
    }


def localized_sitemap_entries(pages):
    """Expand only entries that the existing sitemap policy already allows."""
    for page in pages:
        yield page
        for locale in supported_locales(page):
            if locale != 'ko':
                yield {**page, 'path': localized_url(page['key'], locale), 'lastmod': '2026-09-09'}


def _leaf_strings(value, path=''):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _leaf_strings(item, f'{path}.{key}')
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _leaf_strings(item, f'{path}[{index}]')
    elif isinstance(value, str):
        yield path, value
    else:
        raise ValueError(f'Invalid translation at {path}')


def validate_translations():
    """Fail publication on incomplete catalogs, placeholders or URL collisions."""
    def validate_section(actual_section, reference_section, locale):
        baseline = dict(_leaf_strings(reference_section))
        actual = dict(_leaf_strings(actual_section))
        if actual.keys() != baseline.keys():
            raise ValueError(f'Translation keys differ: {locale}')
        for key, value in actual.items():
            blank_allowed = key == '.duration_separator'
            if (not blank_allowed and not value.strip()) or set(re.findall(r'\{\w+\}', value)) != set(re.findall(r'\{\w+\}', baseline[key])):
                raise ValueError(f'Invalid translation: {locale}{key}')

    paths = set()
    for page in PUBLIC_PAGE_REGISTRY:
        if not set(supported_locales(page)).issubset(LOCALE_CONFIG):
            raise ValueError(f'Unsupported page locale: {page["key"]}')
    for locale in LOCALE_CONFIG:
        if locale != 'ko':
            validate_section(catalog(locale)['common'], catalog('en')['common'], locale)
        for page in PUBLIC_PAGE_REGISTRY:
            if locale not in supported_locales(page):
                continue
            path = localized_url(page['key'], locale)
            if path in paths:
                raise ValueError(f'Duplicate locale URL: {path}')
            paths.add(path)
            if locale != 'ko':
                if page['key'] not in catalog(locale)['pages']:
                    raise ValueError(f'Missing page translation: {locale}/{page["key"]}')
                # Compare only real language equivalents; a culture-specific page
                # need not exist in English or in every other foreign catalog.
                reference_locale = next(code for code in supported_locales(page) if code != 'ko')
                validate_section(catalog(locale)['pages'][page['key']], catalog(reference_locale)['pages'][page['key']], locale)


def register_localized_routes(app, base_url):
    validate_translations()

    def render_localized(page_key, locale):
        page = PAGE_BY_KEY[page_key]
        g.locale_code = locale
        g.localized_page = page
        g.page_canonical_url = base_url + localized_url(page_key, locale)
        resources = catalog(locale)
        copy = resources['pages'][page_key]
        nav = [{'url': localized_url(p['key'], locale), 'label': resources['pages'][p['key']]['h1']}
               for p in PUBLIC_PAGE_REGISTRY if locale in supported_locales(p)]
        home_key = 'age' if locale in supported_locales(PAGE_BY_KEY['age']) else page_key
        breadcrumb_items = [
            {'label': f"AgeCalc ({resources['common']['korean_only']})", 'url': base_url + '/'},
            {'label': copy['h1'], 'url': g.page_canonical_url},
        ]
        schema = [
            {'@context': 'https://schema.org', '@type': 'WebPage', 'name': copy['h1'],
             'description': copy['description'], 'url': g.page_canonical_url, 'inLanguage': locale},
            {'@context': 'https://schema.org', '@type': 'BreadcrumbList',
             'itemListElement': [{'@type': 'ListItem', 'position': index, 'name': item['label'], 'item': item['url']}
                                for index, item in enumerate(breadcrumb_items, 1)]},
        ]
        if page_key == 'age':
            schema += [
                {'@context': 'https://schema.org', '@type': 'SoftwareApplication', 'name': copy['h1'],
                 'description': copy['description'], 'url': g.page_canonical_url, 'inLanguage': locale,
                 'applicationCategory': 'UtilitiesApplication', 'operatingSystem': 'Web',
                 'author': {'@type': 'Organization', 'name': 'AgeCalc'}},
                {'@context': 'https://schema.org', '@type': 'FAQPage', 'inLanguage': locale,
                 'mainEntity': [{'@type': 'Question', 'name': f['question'],
                                 'acceptedAnswer': {'@type': 'Answer', 'text': f['answer']}} for f in copy['faq']]},
            ]
        return render_template(page['localization']['template'], copy=copy, ui=resources['common'],
                               global_nav=nav, global_schema=schema, page_key=page_key,
                               global_breadcrumbs=breadcrumb_items,
                               global_home=localized_url(home_key, locale),
                               calculator_config={'kind': page_key, 'locale': LOCALE_CONFIG[locale]['intl'],
                                                  'ui': resources['common']})

    def normalize_localized(page_key, locale):
        # A language link always points at the public document, never a result.
        return redirect(localized_url(page_key, locale), code=301)

    for page in PUBLIC_PAGE_REGISTRY:
        for locale in supported_locales(page):
            if locale == 'ko':
                continue
            path = localized_url(page['key'], locale)
            defaults = {'page_key': page['key'], 'locale': locale}
            app.add_url_rule(path, endpoint=f'i18n_{locale}_{page["key"]}', view_func=render_localized, defaults=defaults)
            app.add_url_rule(path + '/', endpoint=f'i18n_slash_{locale}_{page["key"]}', view_func=normalize_localized, defaults=defaults)
