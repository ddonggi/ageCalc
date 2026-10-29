"""Public discovery policy: never turn registry metadata into unrestricted links."""
import unittest
from copy import deepcopy
from content import tool_finder
from content.page_registry import STATIC_PAGE_REGISTRY

EXPECTED_CURATED_TOOLS = (('age', '/age', 'age', 0, ('만나이', '만 나이')), ('annual_age_calculator', '/annual-age-calculator', 'age', 1, ('연도별 나이',)), ('age_gap_calculator', '/age-gap-calculator', 'age', 2, ('나이 차이',)), ('age_comparison_table', '/age-comparison-table', 'age', 3, ('나이 비교',)), ('birth_year_age_table', '/birth-year-age-table', 'age', 4, ('출생연도',)), ('birth_year_zodiac_table', '/birth-year-zodiac-table', 'age', 5, ('띠',)), ('baby_months', '/baby-months', 'age', 6, ('아기 월령',)), ('baby_months_table', '/baby-months-table', 'age', 7, ('개월 수',)), ('parent_child', '/parent-child', 'age', 8, ('부모 자녀',)), ('school_grade_calculator', '/school-grade-calculator', 'school', 9, ('학년',)), ('college_entry_year_calculator', '/college-entry-year-calculator', 'school', 10, ('대학 학번',)), ('grade_birth_year_table', '/grade-birth-year-table', 'school', 11, ('학년별 출생연도',)), ('d_day', '/d-day', 'anniversary', 12, ('디데이',)), ('birthday_dday_calculator', '/birthday-dday-calculator', 'anniversary', 13, ('생일',)), ('hundred_day_calculator', '/100-day-calculator', 'anniversary', 14, ('백일', '100일', '첫돌', '천일', '1000일')), ('dog', '/dog', 'pets', 15, ('강아지',)), ('cat', '/cat', 'pets', 16, ('고양이',)), ('pet_age_table', '/pet-age-table', 'pets', 17, ('반려동물',)), ('pet_months_table', '/pet-months-table', 'pets', 18, ('반려동물',)), ('days_between_dates', '/days-between-dates', 'anniversary', 19, ('날짜 차이', '기간', '근속기간', '재직기간', '입사일')), ('date_add_subtract', '/date-add-subtract-calculator', 'anniversary', 20, ('날짜 더하기', '날짜 빼기', 'ISO 주차', '연간 진행률')), ('time_duration_calculator', '/time-duration-calculator', 'anniversary', 21, ('휴게시간', '익일', '근무시간')), ('lunar_birthday', '/lunar-birthday-calculator', 'anniversary', 22, ('음력 생일',)), ('weekly_work_hours_calculator', '/weekly-work-hours-calculator', 'anniversary', 23, ('주간 근무시간', '주간 시간', '근무표')), ('world_time_converter', '/world-time-converter', 'anniversary', 24, ('세계시간', '시차', '회의시간', 'UTC')))

class ToolFinderTests(unittest.TestCase):
    def test_reviewed_full_curation_fixture(self):
        self.assertEqual(tuple((x["endpoint"], x["path"], x["group"], x["order"], x["aliases"]) for x in tool_finder.build_tool_finder_items()), EXPECTED_CURATED_TOOLS)

    def test_reviewed_current_candidates(self):
        items = tool_finder.build_tool_finder_items()
        self.assertEqual(len(items), 25)
        self.assertEqual(len({item['path'] for item in items}), 25)
        self.assertTrue({'/100-day-calculator', '/time-duration-calculator', '/date-add-subtract-calculator', '/lunar-birthday-calculator'}.issubset({x['path'] for x in items}))

    def test_unpublished_nonindexable_and_foreign_only_excluded(self):
        for field, value in [('indexable', False), ('release_batch', 'future'), ('supported_locales', ('en',))]:
            pages = deepcopy(STATIC_PAGE_REGISTRY)
            for page in pages:
                if page['endpoint'] == 'age': page[field] = value
            self.assertNotIn('age', {x['endpoint'] for x in tool_finder.build_tool_finder_items(pages=pages)})

    def test_rejects_invalid_paths_and_unregistered_routes(self):
        for bad in ['https://evil.test', '//evil.test', '#', 'javascript:alert(1)', '/age?q=secret', '/age#x', '/blog/drafts/x']:
            pages = deepcopy(STATIC_PAGE_REGISTRY)
            for page in pages:
                if page['endpoint'] == 'age': page['path'] = bad
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tool_finder.build_tool_finder_items(pages=pages)
        with self.assertRaises(ValueError):
            tool_finder.build_tool_finder_items(registered_paths={})

    def test_rejects_duplicates_and_unknown_candidates(self):
        pages = deepcopy(STATIC_PAGE_REGISTRY)
        for page in pages:
            if page['endpoint'] == 'dog': page['path'] = '/age'
        with self.assertRaises(ValueError): tool_finder.build_tool_finder_items(pages=pages)
        with self.assertRaises(ValueError): tool_finder.build_tool_finder_items(pages=())

    def test_registry_is_title_and_summary_source(self):
        source = {p['endpoint']: p for p in STATIC_PAGE_REGISTRY}
        for item in tool_finder.build_tool_finder_items():
            self.assertEqual(item['title'], source[item['endpoint']]['title'])
            self.assertEqual(item['summary'], source[item['endpoint']]['search_intent'])


class ToolFinderHomeTests(unittest.TestCase):
    def test_home_routes_and_ssr_discovery(self):
        from app import app
        from html.parser import HTMLParser
        class Elements(HTMLParser):
            def __init__(self, html):
                super().__init__(); self.elements = []; self.feed(html)
            def handle_starttag(self, tag, attrs):
                self.elements.append((tag, dict(attrs)))
        with app.test_client() as client:
            response = client.get('/')
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            elements = Elements(html).elements
            self.assertEqual(len([a for t,a in elements if 'data-tool-endpoint' in a]), 25)
            input_attrs = next(a for t,a in elements if a.get('id') == 'tool-finder-input')
            self.assertNotIn('name', input_attrs)
            self.assertTrue(any('hidden' in a for t,a in elements if 'data-tool-controls' in a))
            for item in tool_finder.build_tool_finder_items():
                with self.subTest(endpoint=item['endpoint']):
                    rules = [r for r in app.url_map.iter_rules() if r.endpoint == item['endpoint']]
                    self.assertEqual([r.rule for r in rules], [item['path']])
                    page = client.get(item['path'])
                    self.assertEqual(page.status_code, 200)
                    self.assertIn('href="https://agecalc.cloud' + item['path'] + '"', page.get_data(as_text=True))

if __name__ == '__main__': unittest.main()
