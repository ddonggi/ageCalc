"""Curated Korean discovery, intersected with the registry's release policy."""
from urllib.parse import urlsplit
from content.page_registry import PUBLIC_RELEASE_BATCHES, STATIC_PAGE_REGISTRY

TOOL_FINDER_GROUPS = (
    {'id': 'age', 'label': '나이'},
    {'id': 'school', 'label': '학교'},
    {'id': 'anniversary', 'label': '기념일·날짜'},
    {'id': 'pets', 'label': '반려동물'},
)
# Only curation lives here. Titles, canonical paths and summaries remain registry-owned.
CURATION = (
    ('age', 'age', ('만나이', '만 나이')),
    ('annual_age_calculator', 'age', ('연도별 나이',)),
    ('age_gap_calculator', 'age', ('나이 차이',)),
    ('age_comparison_table', 'age', ('나이 비교',)),
    ('birth_year_age_table', 'age', ('출생연도',)),
    ('birth_year_zodiac_table', 'age', ('띠',)),
    ('baby_months', 'age', ('아기 월령',)),
    ('baby_months_table', 'age', ('개월 수',)),
    ('parent_child', 'age', ('부모 자녀',)),
    ('school_grade_calculator', 'school', ('학년',)),
    ('college_entry_year_calculator', 'school', ('대학 학번',)),
    ('grade_birth_year_table', 'school', ('학년별 출생연도',)),
    ('d_day', 'anniversary', ('디데이',)),
    ('birthday_dday_calculator', 'anniversary', ('생일',)),
    ('hundred_day_calculator', 'anniversary', ('백일', '100일', '첫돌', '천일', '1000일')),
    ('dog', 'pets', ('강아지',)),
    ('cat', 'pets', ('고양이',)),
    ('pet_age_table', 'pets', ('반려동물',)),
    ('pet_months_table', 'pets', ('반려동물',)),
    ('days_between_dates', 'anniversary', ('날짜 차이', '기간', '근속기간', '재직기간', '입사일')),
    ('date_add_subtract', 'anniversary', ('날짜 더하기', '날짜 빼기', 'ISO 주차', '연간 진행률')),
    ('time_duration_calculator', 'anniversary', ('휴게시간', '익일', '근무시간')),
    ('lunar_birthday', 'anniversary', ('음력 생일',)),
    ('weekly_work_hours_calculator', 'anniversary', ('주간 근무시간', '주간 시간', '근무표')),
    ('world_time_converter', 'anniversary', ('세계시간', '시차', '회의시간', 'UTC')),
)


def build_tool_finder_items(*, pages=None, registered_paths=None):
    """Fail closed on corrupt curation; unpublished candidates simply disappear.

    registered_paths is the application's endpoint -> actual canonical route map.
    Keeping it injectable allows policy checks without importing Flask or a DB.
    """
    pages = STATIC_PAGE_REGISTRY if pages is None else pages
    by_endpoint = {}
    for page in pages:
        endpoint = str(page['endpoint'])
        if endpoint in by_endpoint:
            raise ValueError('Duplicate registry endpoint')
        by_endpoint[endpoint] = page
    results, seen = [], set()
    for order, (endpoint, group, aliases) in enumerate(CURATION):
        if endpoint not in by_endpoint:
            raise ValueError('Unknown tool finder endpoint')
        page = by_endpoint[endpoint]
        if (not page['indexable'] or page['release_batch'] not in PUBLIC_RELEASE_BATCHES
                or 'ko' not in page.get('supported_locales', ('ko',))):
            continue
        path = str(page['path'])
        parsed = urlsplit(path)
        if (not path.startswith('/') or path.startswith('//') or parsed.scheme or parsed.netloc
                or parsed.query or parsed.fragment or '#' in path or '?' in path
                or any(ch.isspace() or ord(ch) < 32 for ch in path)
                or path.startswith(('/blog/', '/admin', '/auth'))):
            raise ValueError('Unsafe tool finder path')
        if path in seen:
            raise ValueError('Duplicate tool finder path')
        if registered_paths is not None and registered_paths.get(endpoint) != path:
            raise ValueError('Unregistered canonical tool finder path')
        seen.add(path)
        results.append({'endpoint': endpoint, 'path': path, 'title': str(page['title']),
                        'summary': str(page['search_intent']), 'group': group,
                        'aliases': aliases, 'order': order})
    return tuple(results)
