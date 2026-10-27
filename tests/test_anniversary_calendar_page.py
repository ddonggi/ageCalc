"""B7 server-confirmed export and scoped privacy contracts."""
import re
import unittest
from html.parser import HTMLParser
from unittest.mock import patch
from datetime import date
from app import app

class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.items=[]; self.feed(text)
    def handle_starttag(self, tag, attrs): self.items.append((tag,dict(attrs)))

class AnniversaryCalendarPageTests(unittest.TestCase):
    def setUp(self): self.client=app.test_client()
    def elements(self, response): return Elements(response.get_data(as_text=True)).items
    def test_start_date_survives_examples_and_default_is_empty(self):
        for query, expected in [('', ''), ('?start_date=20240229','20240229'), ('?start_date=00010101','00010101')]:
            items=self.elements(self.client.get('/100-day-calculator'+query))
            self.assertEqual(expected,next(a['value'] for t,a in items if a.get('id')=='hundred-day-date'))
    def test_confirmed_milestones_only(self):
        r=self.client.get('/100-day-calculator?start_date=20240229')
        buttons=[a for t,a in self.elements(r) if 'data-calendar-kind' in a]
        self.assertEqual(['20240607','20250301','20261124'],[a['data-calendar-date'] for a in buttons])
        self.assertTrue(all('disabled' in a for a in buttons))
        self.assertEqual(0,len([a for t,a in self.elements(self.client.get('/100-day-calculator')) if 'data-calendar-kind' in a]))
    def test_birthday_server_snapshot(self):
        with patch('app._current_local_date',return_value=date(2025,3,1)):
            r=self.client.get('/birthday-dday-calculator?month=2&day=29')
        buttons=[a for t,a in self.elements(r) if 'data-calendar-kind' in a]
        self.assertEqual(['20280229'],[a['data-calendar-date'] for a in buttons])
    def test_unexportable_boundary(self):
        r=self.client.get('/100-day-calculator?start_date=99990923')
        buttons=[a for t,a in self.elements(r) if 'data-calendar-kind' in a]
        self.assertEqual([],buttons)
    def test_scoped_privacy_and_query_policy(self):
        for path in ['/100-day-calculator','/birthday-dday-calculator']:
            for query in ['', '?start_date=20240229' if path.startswith('/100') else '?month=2&day=29']:
                r=self.client.get(path+query); text=r.get_data(as_text=True)
                self.assertEqual('no-referrer',r.headers.get('Referrer-Policy'))
                for removed in ['js/analytics.js','js/cookie-consent.js','js/clarity-init.js','pagead2.googlesyndication.com','id="cookie-banner"']:
                    self.assertNotIn(removed,text)
                if query:
                    self.assertIn('<noscript>',text)
                    self.assertEqual('noindex, follow',r.headers.get('X-Robots-Tag'))
                    self.assertIn('no-store',r.headers.get('Cache-Control',''))
        self.assertEqual('strict-origin-when-cross-origin',self.client.get('/age').headers.get('Referrer-Policy'))
