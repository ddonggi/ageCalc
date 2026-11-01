"""Pure-data contract tests: no app, environment, network or DB imports."""
import importlib.util
import unittest
from datetime import date, datetime
from unittest.mock import patch


class HolidayCalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = importlib.util.find_spec('content.korean_holidays')
        if cls.spec:
            from content import korean_holidays
            cls.h = korean_holidays

    def setUp(self):
        self.assertIsNotNone(self.spec, 'official holiday module is missing')

    def test_official_dates_counts_and_no_inferred_substitutes(self):
        result = self.h.build_holiday_calendar(date(2026, 11, 1))
        self.assertEqual(result['counts'], dict(named=24, substitute=7, sundays=52, overlap=4, total=72))
        rows = [r for month in result['months'] for r in month['holidays']]
        self.assertEqual([r['date'] for r in rows], [
            '2027-01-01', '2027-02-06', '2027-02-07', '2027-02-08', '2027-02-09',
            '2027-03-01', '2027-05-01', '2027-05-03', '2027-05-05', '2027-05-13',
            '2027-06-06', '2027-07-17', '2027-07-19', '2027-08-15', '2027-08-16',
            '2027-09-14', '2027-09-15', '2027-09-16', '2027-10-03', '2027-10-04',
            '2027-10-09', '2027-10-11', '2027-12-25', '2027-12-27'])
        self.assertEqual(rows[0]['original_label'], '1월 1일')
        self.assertEqual(rows[1]['original_label'], '설날(연휴)')
        self.assertEqual(rows[9]['original_label'], '부처님 오신 날')
        self.assertEqual(rows[15]['original_label'], '추석(연휴)')
        self.assertEqual(rows[0]['weekday'], 4)
        self.assertEqual(len(result['months']), 12)
        sundays = {d for m in result['months'] for d in m['sundays']}
        self.assertEqual(sundays & {r['date'] for r in rows}, {'2027-02-07', '2027-06-06', '2027-08-15', '2027-10-03'})
        self.assertEqual([(r['date'], r['jurisdiction']) for r in result['local_holidays']], [
            ('2027-04-03', '제주특별자치도'), ('2027-05-11', '전북특별자치도 정읍시'), ('2027-05-18', '광주광역시')])
        self.assertEqual(result['local_holidays'][0]['weekday'], 5)

    def test_original_middle_dot_preserved_separately_from_display(self):
        result = self.h.build_holiday_calendar(date(2026, 11, 1))
        national = [r for month in result['months'] for r in month['holidays']]
        march = next(r for r in national if r['date'] == '2027-03-01')
        self.assertEqual((march['original_label'], march['label']), ('3\u22191절', '3\u00b71절'))
        self.assertEqual([(r['original_label'], r['label']) for r in result['local_holidays']], [
            ('4\u22193희생자 추념일', '4\u00b73희생자 추념일'),
            ('동학농민혁명 기념일', '동학농민혁명 기념일'),
            ('5\u221918민주화운동 기념일', '5\u00b718민주화운동 기념일')])

    def test_review_boundaries_and_wrapper_match(self):
        for day, state in [(date(2026, 10, 31), 'needs_review'), (date(2026, 11, 1), 'current'),
                           (date(2026, 11, 7), 'current'), (date(2026, 11, 8), 'current'),
                           (date(2026, 11, 9), 'needs_review')]:
            with self.subTest(day=day):
                result = self.h.build_holiday_calendar(day)
                self.assertEqual(result['state'], state)
                self.assertEqual(result['today'], day.isoformat())
                self.assertEqual(self.h.holiday_calendar_available(day), state == 'current')
                if state != 'current':
                    self.assertEqual(result['months'], [])
                    self.assertEqual(result['local_holidays'], [])
                    self.assertIsNone(result['counts'])

    def test_disabled_and_future_verification(self):
        for changes, want in [({'active': False}, 'disabled'), ({'verified_on': '2026-11-02', 'next_review': '2026-11-09'}, 'needs_review')]:
            with patch.object(self.h, 'HOLIDAY_METADATA', dict(self.h.HOLIDAY_METADATA, **changes)):
                result = self.h.build_holiday_calendar(date(2026, 11, 1))
                self.assertEqual(result['state'], want)
                self.assertFalse(result['available'])
                self.assertEqual(result['months'], [])

    def test_rejects_bad_metadata(self):
        cases = {'year': 2028, 'source_url': 'javascript:bad', 'source_sha256': 'f' * 64,
                 'notice_number': '', 'source_id': 'unknown', 'published_on': '2026-02-30',
                 'verified_on': '2026-11-1', 'next_review': '2026-10-31', 'active': 1,
                 'reviewer': '', 'maintenance_role': '', 'version': ''}
        for field, value in cases.items():
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.h.validate_holiday_data(dict(self.h.HOLIDAY_METADATA, **{field: value}), self.h.NATIONAL_HOLIDAYS, self.h.LOCAL_HOLIDAYS)

    def test_rejects_bad_rows_and_missing_records(self):
        cases = {'date': '2027-02-30', 'id': '', 'original_label': '', 'label': '',
                 'type': 'local', 'scope': '', 'source_page': 3, 'source_id': 'unknown'}
        for field, value in cases.items():
            records = [dict(r) for r in self.h.NATIONAL_HOLIDAYS]
            records[0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.h.validate_holiday_data(self.h.HOLIDAY_METADATA, records, self.h.LOCAL_HOLIDAYS)
        for mutate in ('duplicate_date', 'duplicate_id', 'wrong_year', 'wrong_official_date', 'missing'):
            records = [dict(r) for r in self.h.NATIONAL_HOLIDAYS]
            if mutate == 'duplicate_date': records[1]['date'] = records[0]['date']
            if mutate == 'duplicate_id': records[1]['id'] = records[0]['id']
            if mutate == 'wrong_year': records[0]['date'] = '2028-01-01'
            if mutate == 'wrong_official_date': records[0]['date'] = '2027-01-02'
            if mutate == 'missing': records.pop()
            with self.subTest(mutate=mutate), self.assertRaises(ValueError):
                self.h.validate_holiday_data(self.h.HOLIDAY_METADATA, records, self.h.LOCAL_HOLIDAYS)
        local = [dict(r) for r in self.h.LOCAL_HOLIDAYS]
        local[0]['jurisdiction'] = '전국'
        with self.assertRaises(ValueError):
            self.h.validate_holiday_data(self.h.HOLIDAY_METADATA, self.h.NATIONAL_HOLIDAYS, local)

    def test_invalid_metadata_fails_closed_and_uses_safe_source(self):
        with patch.object(self.h, 'HOLIDAY_METADATA', {'source_url': 'https://evil.invalid', 'reviewer': '<script>'}):
            result = self.h.build_holiday_calendar(date(2026, 11, 1))
        self.assertEqual(result['state'], 'invalid')
        self.assertEqual(result['metadata']['source_url'], self.h.SOURCE_INFO['source_url'])
        self.assertNotIn('<script>', str(result))
        self.assertEqual(result['months'], [])
        self.assertEqual(result['local_holidays'], [])
        self.assertIsNone(result['counts'])

    def test_invalid_record_fails_closed(self):
        with patch.object(self.h, 'NATIONAL_HOLIDAYS', ({'date': 'oops'},)):
            self.assertFalse(self.h.holiday_calendar_available(date(2026, 11, 1)))
            self.assertEqual(self.h.build_holiday_calendar(date(2026, 11, 1))['state'], 'invalid')

    def test_constants_immutable_and_output_mutation_cannot_change_facts(self):
        with self.assertRaises(TypeError): self.h.HOLIDAY_METADATA['active'] = False
        with self.assertRaises(TypeError): self.h.NATIONAL_HOLIDAYS[0]['date'] = '2027-01-02'
        with self.assertRaises(TypeError): self.h.LOCAL_HOLIDAYS[0]['jurisdiction'] = '전국'
        result = self.h.build_holiday_calendar(date(2026, 11, 1))
        result['metadata']['active'] = False
        result['months'][0]['holidays'][0]['label'] = 'bad'
        result['local_holidays'].clear()
        fresh = self.h.build_holiday_calendar(date(2026, 11, 1))
        self.assertTrue(fresh['available'])
        self.assertEqual(fresh['months'][0]['holidays'][0]['label'], '1월 1일')
        self.assertEqual(len(fresh['local_holidays']), 3)

    def test_today_requires_plain_date(self):
        for value in (None, '2026-11-01', datetime(2026, 11, 1)):
            with self.subTest(value=value), self.assertRaises(TypeError):
                self.h.build_holiday_calendar(value)


if __name__ == '__main__':
    unittest.main()
