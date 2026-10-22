"""Calendar-year previews must not change current school-year/query contracts."""
from datetime import date
import re
import unittest
from unittest.mock import patch

import app as app_module


class Preview2027Tests(unittest.TestCase):
    def setUp(self):
        self.client = app_module.app.test_client()

    def get(self, path, today=date(2026, 10, 15)):
        with patch.object(app_module, '_current_local_date', return_value=today):
            return self.client.get(path)

    def preview(self, path, today=date(2026, 10, 15)):
        response = self.get(path, today)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        section = re.search(r'<section[^>]*id="preview-2027"[^>]*>(.*?)</section>', html, re.S)
        self.assertIsNotNone(section, '2027 comparison must be server rendered')
        return re.sub(r'\s+', ' ', re.sub('<[^>]+>', ' ', section.group(1)))

    def test_birth_year_keeps_current_and_2027_ages_separate(self):
        for today, current_age in ((date(2026, 12, 31), '16세'), (date(2027, 1, 1), '17세')):
            with self.subTest(today=today):
                text = self.preview('/birth-year-age-table?year=2010', today)
                self.assertIn(f'2010년생 {current_age} 17세 만 16~17세', text)
                self.assertIn('2027년 기준', text)

    def test_school_preview_does_not_roll_current_school_year_in_january(self):
        for today, current in ((date(2026, 12, 31), '취학 전'), (date(2027, 1, 1), '취학 전'), (date(2027, 2, 28), '취학 전'), (date(2027, 3, 1), '초등학교 1학년')):
            with self.subTest(today=today):
                text = self.preview('/school-grade-calculator?year=2020', today)
                self.assertIn(f'2020년생 {current} 초등학교 1학년', text)

    def test_all_2027_grades_have_expected_birth_year_and_age(self):
        text = self.preview('/grade-birth-year-table')
        for label, birth, age, full_age in (('초1', 2020, 7, '6~7'), ('초6', 2015, 12, '11~12'), ('중1', 2014, 13, '12~13'), ('중3', 2012, 15, '14~15'), ('고1', 2011, 16, '15~16'), ('고3', 2009, 18, '17~18')):
            self.assertIn(f'{label} {birth}년생 {age}세 만 {full_age}세', text)

    def test_college_entry_and_current_ages_are_distinct(self):
        for today, age, full_age in ((date(2026, 12, 31), 18, '17~18'), (date(2027, 1, 1), 19, '18~19')):
            text = self.preview('/college-entry-year-calculator?year=2027', today)
            self.assertIn('2008년생', text)
            self.assertIn(f'{today.year}년 현재 연나이 {age}세 / 만 {full_age}세', text)
            self.assertIn('2027년 입학연도 연나이 19세 / 만 18~19세', text)

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
