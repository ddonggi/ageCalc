"""Calendar-year previews must not change current school-year/query contracts."""
from datetime import date
import re
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

import app as app_module


class Preview2027Tests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def get(self, path, today=date(2026, 10, 15)):
        with patch.object(app_module, '_current_local_date', return_value=today):
            return self.client.get(path)

    def preview_section(self, path, today=date(2026, 10, 15)):
        response = self.get(path, today)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        section = re.search(r'<section[^>]*id="preview-2027"[^>]*>(.*?)</section>', html, re.S)
        self.assertIsNotNone(section, '2027 comparison must be server rendered')
        return section.group(1)

    def preview(self, path, today=date(2026, 10, 15)):
        return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', self.preview_section(path, today)))

    def table(self, html):
        table = re.search(r'<table\b[^>]*>.*?</table>', html, re.S)
        self.assertIsNotNone(table)
        return ElementTree.fromstring(table.group(0))

    def test_birth_year_compares_only_when_current_year_differs_from_2027(self):
        for today, expected_ages in (
            (date(2026, 12, 31), '16세 17세'),
            (date(2027, 1, 1), '17세'),
            (date(2028, 1, 1), '18세 17세'),
        ):
            with self.subTest(today=today):
                text = self.preview('/birth-year-age-table?year=2010', today)
                self.assertIn(f'2010년생 {expected_ages} 만 16~17세', text)
                self.assertIn('2027년 기준', text)

    def test_school_comparison_only_hides_duplicate_column_during_2027_school_year(self):
        for today, years, current_grade in (
            (date(2026, 12, 31), ('2026학년도', '2027학년도'), '취학 전'),
            (date(2027, 1, 1), ('2026학년도', '2027학년도'), '취학 전'),
            (date(2027, 2, 28), ('2026학년도', '2027학년도'), '취학 전'),
            (date(2027, 3, 1), ('2027학년도',), None),
            (date(2028, 1, 1), ('2027학년도',), None),
            (date(2028, 2, 29), ('2027학년도',), None),
            (date(2028, 3, 1), ('2028학년도', '2027학년도'), '초등학교 2학년'),
        ):
            with self.subTest(today=today):
                section = self.preview_section('/school-grade-calculator?year=2020', today)
                heading = '기준' if len(years) == 1 else ('참고' if today.year == 2028 else '미리보기')
                self.assertRegex(section, rf'<h2[^>]*>[^<]*{heading}[^<]*</h2>')
                table = self.table(section)
                headers = tuple(cell.text for cell in table.findall('./thead/tr/th'))
                self.assertEqual(headers, ('출생연도', *years))
                rows = [tuple(cell.text for cell in row) for row in table.findall('./tbody/tr')]
                expected_grades = (current_grade,) if current_grade else ()
                self.assertIn(('2020년생', *expected_grades, '초등학교 1학년'), rows)
                self.assertTrue(all(len(row) == len(headers) for row in rows))

    def test_all_2027_grades_have_expected_birth_year_and_age(self):
        text = self.preview('/grade-birth-year-table')
        for label, birth, age, full_age in (('초1', 2020, 7, '6~7'), ('초6', 2015, 12, '11~12'), ('중1', 2014, 13, '12~13'), ('중3', 2012, 15, '14~15'), ('고1', 2011, 16, '15~16'), ('고3', 2009, 18, '17~18')):
            self.assertIn(f'{label} {birth}년생 {age}세 만 {full_age}세', text)

    def test_grade_birth_year_keeps_fixed_2027_ages_after_calendar_rollover(self):
        path = '/grade-birth-year-table?stage=middle&grade=1'
        for today, heading, expected_current in (
            (date(2027, 2, 28), '미리보기', ('2013년생', '14세', '만 13~14세')),
            (date(2027, 3, 1), '기준', ('2014년생', '13세', '만 12~13세')),
            (date(2027, 12, 31), '기준', ('2014년생', '13세', '만 12~13세')),
            (date(2028, 1, 1), '기준', ('2014년생', '14세', '만 13~14세')),
            (date(2028, 2, 29), '기준', ('2014년생', '14세', '만 13~14세')),
            (date(2028, 3, 1), '참고', ('2015년생', '13세', '만 12~13세')),
        ):
            with self.subTest(today=today):
                section = self.preview_section(path, today)
                self.assertRegex(section, rf'<h2[^>]*>[^<]*{heading}[^<]*</h2>')
                table = self.table(section)
                rows = [tuple(cell.text for cell in row) for row in table.findall('./tbody/tr')]
                self.assertEqual(len(rows), 12)
                self.assertTrue(all(len(row) == 4 for row in rows))
                self.assertIn(('중1', '2014년생', '13세', '만 12~13세'), rows)

                html = self.get(path, today).get_data(as_text=True)
                current_html = html[html.index('<table class="data-table birth-year-table">'):]
                selected = self.table(current_html).find('./tbody/tr[@class="is-selected"]')
                self.assertIsNotNone(selected)
                self.assertEqual(tuple(cell.text for cell in selected[-3:]), expected_current)

    def test_college_entry_compares_only_when_current_year_differs_from_2027(self):
        for today, current_age in (
            (date(2026, 12, 31), '연나이 18세 / 만 17~18세'),
            (date(2027, 1, 1), None),
            (date(2028, 1, 1), '연나이 20세 / 만 19~20세'),
        ):
            with self.subTest(today=today):
                text = self.preview('/college-entry-year-calculator?year=2027', today)
                self.assertIn('2008년생', text)
                self.assertEqual(text.count('연나이 19세 / 만 18~19세'), 1)
                if current_age:
                    self.assertIn(f'{today.year}년 현재 {current_age}', text)

    def test_college_base_descriptions_drop_fixed_cohorts_in_2027(self):
        for today in (date(2026, 12, 31), date(2027, 1, 1), date(2028, 1, 1)):
            with self.subTest(today=today):
                response = self.get('/college-entry-year-calculator', today)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                for field in ('name="description"', 'property="og:description"'):
                    match = re.search(rf'<meta {field} content="([^"]+)"', html)
                    self.assertIsNotNone(match, field)
                    description = match.group(1)
                    self.assertRegex(description, r'출생연도|몇 ?년생')
                    if today.year < 2027:
                        self.assertIn('26학번', description)
                    else:
                        self.assertNotRegex(description, r'\d+학번')

    def test_query_meanings_and_indexing_are_preserved(self):
        for path in ('/birth-year-age-table?year=2027', '/school-grade-calculator?year=2027', '/grade-birth-year-table?year=2027', '/college-entry-year-calculator?year=bad', '/college-entry-year-calculator?year=2027&preview=1'):
            self.assertEqual(self.get(path).status_code, 302, path)
        for path in ('/college-entry-year-calculator?year=2027', '/school-grade-calculator?year=2020', '/grade-birth-year-table?stage=middle&grade=1'):
            response = self.get(path)
            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn('<meta name="robots" content="noindex,follow"', html)
            canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
            self.assertNotIn('?', canonical)
        response = self.get('/birth-year-age-table?year=2010')
        self.assertNotIn('<meta name="robots" content="noindex,follow"', response.get_data(as_text=True))
        self.assertIn('/birth-year-age-table?year=2010', response.get_data(as_text=True))
        self.assertEqual(self.get('/school-entry-year-table?year=2020').status_code, 301)


if __name__ == '__main__':
    unittest.main()
