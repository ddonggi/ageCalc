"""Consent must exist before ads, including when the analytics loader is blocked."""
import json
import re
import subprocess
import unittest

from app import app


class TrackingConsentTests(unittest.TestCase):
    def test_all_age_locales_initialize_consent_before_ads_with_csp_nonce(self):
        for path in ['/age'] + [f'/{code}/age-calculator' for code in ('en', 'ja', 'es', 'pt-br', 'zh-cn')]:
            with self.subTest(path=path):
                response = app.test_client().get(path)
                html = response.get_data(as_text=True)
                bootstrap = re.search(r'<script id="consent-defaults" nonce="([^"]+)">(.*?)</script>', html, re.S)
                self.assertIsNotNone(bootstrap, 'consent defaults missing before advertising loads')
                self.assertLess(bootstrap.start(), html.index('pagead/js/adsbygoogle.js'))
                self.assertIn("'nonce-" + bootstrap[1] + "'", response.headers['Content-Security-Policy'])
                self.assertIn('google-site-verification', html)
                self.assertIn('google-adsense-account', html)

    def test_default_restore_and_clicks_work_without_analytics_network(self):
        html = app.test_client().get('/en/age-calculator').get_data(as_text=True)
        bootstrap = re.search(r'<script id="consent-defaults" nonce="[^"]+">(.*?)</script>', html, re.S)
        self.assertIsNotNone(bootstrap)
        script = r'''
const vm = require('node:vm');
const code = CODE;
const run = cookie => {
  const listeners = {};
  const document = {cookie, addEventListener: (name, fn) => listeners[name] = fn};
  const window = {};
  vm.runInNewContext(code, {window, document});
  const before = window.dataLayer.map(x => Array.from(x));
  const click = id => listeners.click({target: {closest: () => ({id})}});
  click('accept-cookies');
  click('reject-cookies');
  return {before, after: window.dataLayer.map(x => Array.from(x))};
};
console.log(JSON.stringify(['', 'cookieConsent=rejected', 'cookieConsent=accepted'].map(run)));
'''.replace('CODE', json.dumps(bootstrap[1]))
        result = subprocess.run(['node', '-e', script], check=True, capture_output=True, text=True)
        states = json.loads(result.stdout)
        denied = dict.fromkeys(('ad_storage', 'analytics_storage', 'ad_user_data', 'ad_personalization'), 'denied')
        granted = dict.fromkeys(denied, 'granted')
        for state in states:
            self.assertEqual(['consent', 'default', denied], state['before'][0])
            self.assertEqual(['consent', 'update', granted], state['after'][-2])
            self.assertEqual(['consent', 'update', denied], state['after'][-1])
        self.assertEqual(1, len(states[0]['before']))
        self.assertEqual(1, len(states[1]['before']))
        self.assertEqual(['consent', 'update', granted], states[2]['before'][1])

    def test_csp_allows_observed_image_export_and_consent_requests(self):
        response = app.test_client().get('/age')
        directives = dict(item.strip().split(' ', 1) for item in response.headers['Content-Security-Policy'].split(';') if item.strip())
        self.assertIn('https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js', directives['script-src'].split())
        self.assertIn('https://fundingchoicesmessages.google.com', directives['connect-src'].split())
        self.assertNotIn("'unsafe-inline'", directives['script-src'].split())
        self.assertNotIn('*', directives['script-src'].split())
