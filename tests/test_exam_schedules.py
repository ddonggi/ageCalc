"""B11 official-date expectations and safe preset boundary contracts."""
import importlib.util
import unittest
from datetime import date
from unittest.mock import patch


class ExamSchedulesTests(unittest.TestCase):
    def schedules(self):
        self.assertIsNotNone(importlib.util.find_spec('content.exam_schedules'), 'B11 schedule module must exist')
        from content import exam_schedules
        return exam_schedules

    def test_official_dates_and_derived_hundred_days(self):
        rows = self.schedules().build_exam_presets(date(2026, 10, 31))
        self.assertEqual([(r['academic_year'], r['execution_year'], r['exam_date'], r['d100_date'], r['date_digits']) for r in rows], [
            (2027, 2026, '2026-11-19', '2026-08-11', '20261119'),
            (2028, 2027, '2027-11-18', '2027-08-10', '20271118')])
        self.assertTrue(all(r['can_fill'] and r['state'] == 'upcoming' for r in rows))

    def test_review_deadline_and_ended_priority(self):
        module = self.schedules()
        for today, state, fill in [(date(2026,11,12),'upcoming',True), (date(2026,11,13),'needs_review',False), (date(2026,11,19),'needs_review',False), (date(2026,11,20),'ended',False)]:
            with self.subTest(today=today):
                row = module.build_exam_presets(today)[0]
                self.assertEqual((row['state'],row['can_fill']), (state,fill))
        records = [dict(r) for r in module.EXAM_SCHEDULES]
        records[0]['review_due'] = '2026-11-19'
        with patch.object(module, 'EXAM_SCHEDULES', records):
            self.assertEqual(module.build_exam_presets(date(2026,11,19))[0]['state'], 'today')
        records[0]['enabled'] = False
        with patch.object(module, 'EXAM_SCHEDULES', records):
            row = module.build_exam_presets(date(2027,1,1))[0]
            self.assertEqual((row['state'], row['can_fill']), ('under_review', False))
        self.assertEqual(module.build_exam_presets(date(2027,3,31))[1]['state'], 'upcoming')
        self.assertEqual(module.build_exam_presets(date(2027,4,1))[1]['state'], 'needs_review')

    def test_projection_does_not_mutate_source(self):
        module = self.schedules()
        rows = module.build_exam_presets(date(2026,10,31))
        rows[0]['exam_date'] = '2000-01-01'
        self.assertEqual(module.build_exam_presets(date(2026,10,31))[0]['exam_date'], '2026-11-19')
        with self.assertRaises(TypeError):
            module.EXAM_SCHEDULES[0]['enabled'] = False

    def test_invalid_metadata_is_rejected(self):
        module = self.schedules()
        for key, value in [('academic_year',True), ('execution_year',2025), ('exam_date','2026-02-30'), ('exam_date','20261119'), ('enabled',1), ('source_url','javascript:alert(1)'), ('source_title',''), ('published_on','bad'), ('verified_on','2026-13-01'), ('review_due',''), ('label','x'*41), ('id','')]:
            with self.subTest(key=key,value=value):
                record = dict(module.EXAM_SCHEDULES[0]); record[key] = value
                with self.assertRaises(ValueError):
                    module.validate_exam_schedules([record])
        with self.assertRaises(ValueError):
            module.validate_exam_schedules([module.EXAM_SCHEDULES[0]] * 2)


class DDayIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import app
        cls.module = app
        cls.client = app.app.test_client()

    def test_single_server_today_snapshot_and_get_preserved(self):
        from flask import template_rendered
        captured = []
        def receive(sender, template, context, **extra):
            captured.append(context)
        template_rendered.connect(receive, self.module.app)
        try:
            with patch.object(self.module, '_current_local_date', return_value=date(2026,10,31)):
                response = self.client.get('/d-day?date=20261119&mode=until&label=exam')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get('Cache-Control'), 'no-store')
            self.assertEqual(response.headers.get('X-Robots-Tag'), 'noindex, follow')
            self.assertEqual(captured[-1].get('dday_today'), '2026-10-31')
            self.assertEqual(captured[-1]['dday_result']['days'], 19)
            self.assertEqual(captured[-1]['dday_values']['label'], 'exam')
            self.assertEqual(captured[-1]['dday_exam_presets'][0]['state'], 'upcoming')
        finally:
            template_rendered.disconnect(receive, self.module.app)

    def test_korean_referrer_and_query_rejection(self):
        self.assertEqual(self.client.get('/d-day').headers.get('Referrer-Policy'), 'no-referrer')
        self.assertEqual(self.client.get('/en/d-day').headers.get('Referrer-Policy'), 'strict-origin-when-cross-origin')
        for query in ['date=20261119&mode=until&label=a&extra=b', 'date=20261119&date=20261120&mode=until&label=a', 'date=20260230&mode=until&label=a', 'date=20261119&mode=invalid&label=a']:
            response = self.client.get('/d-day?' + query)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.headers['Location'], '/d-day')
