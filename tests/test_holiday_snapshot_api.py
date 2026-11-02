"""Fixed anonymous calendar snapshot: no user calculation inputs or DB use."""
from datetime import datetime, timezone, timedelta
import os
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo


class HolidaySnapshotApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        from content import korean_holidays
        cls.module, cls.holidays = app, korean_holidays
        cls.client = app.app.test_client()

    def get_at(self, instant, path='/api/calendar/korea/2027', **kwargs):
        with patch.object(self.module, '_holiday_snapshot_now', return_value=instant):
            return self.client.get(path, **kwargs)

    def now(self, value='2026-11-02T12:00:00+09:00'):
        return datetime.fromisoformat(value)

    def test_current_detached_national_only_and_headers(self):
        response = self.get_at(self.now())
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertTrue(data['available'])
        self.assertEqual((data['state'], data['year']), ('current', 2027))
        self.assertEqual(len(data['holidays']), 24)
        self.assertTrue(all(set(row) == {'date', 'label', 'type'} for row in data['holidays']))
        self.assertEqual(sum(r['type'] == 'substitute' for r in data['holidays']), 7)
        self.assertFalse({'2027-04-03', '2027-05-11', '2027-05-18'} & {r['date'] for r in data['holidays']})
        self.assertEqual(set(data['metadata']), {'version', 'source_url', 'verified_on', 'next_review'})
        self.assertEqual(data['lease_ms'], 600000)
        self.assertEqual(datetime.fromisoformat(data['expires_at']) - datetime.fromisoformat(data['server_now']), timedelta(minutes=10))
        self.assertEqual(response.headers['Cache-Control'], 'no-store')
        self.assertIn('noindex', response.headers['X-Robots-Tag'])
        self.assertEqual(response.headers['X-Content-Type-Options'], 'nosniff')
        self.assertFalse(response.headers.getlist('Set-Cookie'))
        self.assertTrue(response.is_json)

    def test_deadline_midnight_and_stale_no_leak(self):
        deadline = self.get_at(self.now('2026-11-08T23:59:59+09:00')).get_json()
        self.assertTrue(deadline['available'])
        self.assertEqual(deadline['lease_ms'], 1000)
        self.assertEqual(deadline['expires_at'], '2026-11-09T00:00:00+09:00')
        for value in ('2026-11-09T00:00:00+09:00', '2026-10-31T23:59:59+09:00'):
            data = self.get_at(self.now(value)).get_json()
            self.assertFalse(data['available'])
            self.assertEqual(data['state'], 'needs_review')
            self.assertEqual(data['holidays'], [])
            self.assertEqual(data['lease_ms'], 0)
            self.assertEqual(data['expires_at'], data['server_now'])
            self.assertNotIn('counts', data)

    def test_disabled_invalid_future_and_recovery(self):
        original = dict(self.holidays.HOLIDAY_METADATA)
        for changes, state in (({'active': False}, 'disabled'), ({'version': ''}, 'invalid'),
                               ({'verified_on': '2026-11-03', 'next_review': '2026-11-10'}, 'needs_review')):
            with self.subTest(changes=changes), patch.object(self.holidays, 'HOLIDAY_METADATA', {**original, **changes}):
                data = self.get_at(self.now()).get_json()
                self.assertEqual((data['available'], data['state'], data['holidays'], data['lease_ms']), (False, state, [], 0))
        self.assertTrue(self.get_at(self.now()).get_json()['available'])

    def test_explicit_kst_clock_and_blog_timezone_independence(self):
        with patch.dict(os.environ, {'BLOG_TIMEZONE': 'America/Los_Angeles'}):
            self.assertEqual(str(self.module._holiday_snapshot_now().tzinfo), 'Asia/Seoul')
            with patch.object(self.module, '_current_local_date', side_effect=AssertionError('BLOG clock used')):
                # UTC Nov 8 15:00 is already Nov 9 in Korea.
                data = self.get_at(datetime(2026, 11, 8, 15, tzinfo=timezone.utc)).get_json()
                self.assertFalse(data['available'])
                self.assertEqual(data['state'], 'needs_review')

    def test_query_and_body_rejected_without_echo_or_cookie(self):
        for path, kwargs in (('/api/calendar/korea/2027?start=private-date', {}),
                             ('/api/calendar/korea/2027?', {}),
                             ('/api/calendar/korea/2027', {'data': 'private-date'})):
            response = self.get_at(self.now(), path, **kwargs)
            # Empty query marker has no input and is accepted.
            expected = 200 if path.endswith('?') else 400
            self.assertEqual(response.status_code, expected)
            self.assertNotIn('private-date', response.get_data(as_text=True))
            self.assertEqual(response.headers['Cache-Control'], 'no-store')
            self.assertIn('noindex', response.headers['X-Robots-Tag'])
            self.assertFalse(response.headers.getlist('Set-Cookie'))
        self.assertEqual(self.client.post('/api/calendar/korea/2027').status_code, 405)

    def test_api_not_registered_as_public_page(self):
        from content.page_registry import PUBLIC_PAGE_REGISTRY
        self.assertNotIn('/api/calendar/korea/2027', str(PUBLIC_PAGE_REGISTRY))


if __name__ == '__main__':
    unittest.main()
