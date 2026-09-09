"""Locale behavior, independent of translated text and page availability."""

LOCALE_CONFIG = {
    'ko': {'prefix': '', 'hreflang': 'ko', 'intl': 'ko-KR', 'name': '한국어', 'date_order': ('year', 'month', 'day')},
    'en': {'prefix': 'en', 'hreflang': 'en', 'intl': 'en', 'name': 'English', 'date_order': ('month', 'day', 'year')},
    'ja': {'prefix': 'ja', 'hreflang': 'ja', 'intl': 'ja-JP', 'name': '日本語', 'date_order': ('year', 'month', 'day')},
    'es': {'prefix': 'es', 'hreflang': 'es', 'intl': 'es', 'name': 'Español', 'date_order': ('day', 'month', 'year')},
    'pt-BR': {'prefix': 'pt-br', 'hreflang': 'pt-BR', 'intl': 'pt-BR', 'name': 'Português', 'date_order': ('day', 'month', 'year')},
    'zh-CN': {'prefix': 'zh-cn', 'hreflang': 'zh-CN', 'intl': 'zh-CN', 'name': '中文', 'date_order': ('year', 'month', 'day')},
}

ALL_LOCALES = tuple(LOCALE_CONFIG)
LOCALE_FEATURES = {
    code: {
        'korean_policy': code == 'ko',
        'year_age': code == 'ko',
        'lunar': code == 'ko',
        'korean_promotions': code == 'ko',
        'client_only': code != 'ko',
    }
    for code in LOCALE_CONFIG
}
