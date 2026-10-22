"""Approved ACX-003/006 calendar contracts; run with an isolated test DB."""
import unittest
from datetime import date
from app import _build_hundred_day_snapshot


class AnniversaryBundleTests(unittest.TestCase):
    def snapshot(self, start, today):
        return _build_hundred_day_snapshot(date.fromisoformat(start), date.fromisoformat(today))

    def test_approved_calendar_examples(self):
        cases = [
            ('2024-02-29', ['2024-06-07', '2025-03-01', '2026-11-24']),
            ('2025-01-01', ['2025-04-10', '2026-01-01', '2027-09-27']),
            ('2026-10-23', ['2027-01-30', '2027-10-23', '2029-07-18']),
        ]
        for start, expected in cases:
            with self.subTest(start=start):
                result = self.snapshot(start, start)
                self.assertEqual([row['date'] for row in result['milestones']], [date.fromisoformat(value) for value in expected])
                self.assertTrue(all(row['available'] for row in result['milestones']))

    def test_century_leap_rule(self):
        for start, hundredth in [('1900-02-28', date(1900, 6, 7)), ('2000-02-29', date(2000, 6, 7))]:
            with self.subTest(start=start):
                result = self.snapshot(start, start)
                self.assertEqual(result['milestones'][0]['date'], hundredth)
        self.assertEqual(self.snapshot('2000-02-29', '2000-02-29')['milestones'][1]['date'], date(2001, 3, 1))

    def test_today_is_next_milestone(self):
        result = self.snapshot('2025-01-01', '2025-04-10')
        self.assertEqual(result['next_milestone']['date'], date(2025, 4, 10))
        self.assertEqual(result['next_milestone']['status_label'], 'D-Day')
        self.assertEqual(result['status_label'], 'D-Day')

    def test_next_after_hundred_days(self):
        result = self.snapshot('2025-01-01', '2025-04-11')
        self.assertEqual(result['next_milestone']['date'], date(2026, 1, 1))

    def test_all_past(self):
        result = self.snapshot('2025-01-01', '2027-09-28')
        self.assertIsNone(result['next_milestone'])
        self.assertTrue(result['all_milestones_past'])

    def test_overflow_keeps_valid_rows(self):
        result = self.snapshot('9999-01-01', '9999-01-01')
        self.assertEqual(result['milestones'][0]['date'], date(9999, 4, 10))
        self.assertEqual(sum(row['available'] for row in result['milestones']), 1)
        result = self.snapshot('9999-12-31', '9999-12-31')
        self.assertFalse(any(row['available'] for row in result['milestones']))
        self.assertIsNone(result['next_milestone'])

    def test_first_anniversary_is_not_fixed_365_days(self):
        result = self.snapshot('2023-03-01', '2023-03-01')
        self.assertEqual(result['milestones'][1]['date'], date(2024, 3, 1))


if __name__ == '__main__':
    unittest.main()
