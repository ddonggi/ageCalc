from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path
from types import SimpleNamespace

from flask import render_template

import app as app_module


app = app_module.app
PROJECT_ROOT = Path(__file__).resolve().parents[1]


class ReadingProgressPageTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)

    def test_public_guides_render_article_scoped_reading_progress(self):
        client = app.test_client()

        for path, content_type in (
            ("/guides/age-calculation-2026", "guide"),
            ("/korean-age-guide", "legacy-guide"),
        ):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                self.assertIn('role="progressbar"', html)
                self.assertIn('data-reading-progress-target', html)
                self.assertIn(f'data-content-type="{content_type}"', html)
                self.assertIn('js/reading-progress.js', html)

    def test_nonindexable_guide_does_not_render_reading_progress(self):
        response = app.test_client().get("/guides/age-gap-calculation-guide")

        self.assertEqual(200, response.status_code)
        html = response.get_data(as_text=True)
        self.assertNotIn('role="progressbar"', html)
        self.assertNotIn('js/reading-progress.js', html)

    def test_public_blog_renders_reading_progress_but_private_modes_do_not(self):
        post = SimpleNamespace(
            id=7,
            slug="2026-man-age-guide",
            title="테스트 글",
            excerpt="요약",
            content_html="<p>본문</p>",
            cover_image_url=None,
            status="published",
            published_at=None,
            created_at=None,
            updated_at=None,
            sources=[],
        )

        with app.test_request_context("/blog/2026-man-age-guide"):
            public_html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                structured_article=app_module._structured_blog_context(post),
            )
        self.assertIn('role="progressbar"', public_html)
        self.assertIn('data-content-type="blog"', public_html)
        self.assertIn('data-reading-progress-target', public_html)
        self.assertIn('js/reading-progress.js', public_html)

        for draft_mode, review_mode in ((True, False), (False, True)):
            with self.subTest(draft_mode=draft_mode, review_mode=review_mode), app.test_request_context(
                "/blog/private"
            ):
                private_html = render_template(
                    "blog-detail.html",
                    post=post,
                    draft_mode=draft_mode,
                    review_mode=review_mode,
                    blog_indexable=False,
                    structured_article=app_module._structured_blog_context(post),
                )
                self.assertNotIn('role="progressbar"', private_html)
                self.assertNotIn('js/reading-progress.js', private_html)


class ReadingProgressScriptTests(unittest.TestCase):
    def run_node(self, expression: str):
        script_path = PROJECT_ROOT / "static/js/reading-progress.js"
        program = f"""
const progress = require({json.dumps(str(script_path))});
const result = {expression};
process.stdout.write(JSON.stringify(result));
"""
        completed = subprocess.run(
            ["node", "-e", program],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_calculate_progress_uses_article_bounds_and_clamps_result(self):
        cases = self.run_node(
            "["
            "progress.calculateProgress(50, 100, 1100, 500),"
            "progress.calculateProgress(400, 100, 1100, 500),"
            "progress.calculateProgress(900, 100, 1100, 500)"
            "]"
        )

        self.assertEqual([0, 50, 100], cases)

    def test_new_milestones_returns_each_crossed_threshold_once(self):
        result = self.run_node(
            "(() => {"
            "const sent = new Set([25]);"
            "const first = progress.newMilestones(76, sent);"
            "first.forEach((value) => sent.add(value));"
            "const second = progress.newMilestones(100, sent);"
            "return { first, second };"
            "})()"
        )

        self.assertEqual({"first": [50, 75], "second": [100]}, result)

    def test_mobile_browser_chrome_resize_keeps_progress_viewport_height_stable(self):
        result = self.run_node(
            "(() => {"
            "const initial = progress.updateViewportMetrics(null, 390, 720);"
            "const chromeCollapsed = progress.updateViewportMetrics(initial, 390, 810);"
            "const rotated = progress.updateViewportMetrics(chromeCollapsed, 810, 390);"
            "return { initial, chromeCollapsed, rotated };"
            "})()"
        )

        self.assertEqual(
            {
                "initial": {"width": 390, "height": 720},
                "chromeCollapsed": {"width": 390, "height": 720},
                "rotated": {"width": 810, "height": 390},
            },
            result,
        )

    def run_analytics_node(self, consent: str):
        analytics_path = PROJECT_ROOT / "static/js/analytics.js"
        program = f"""
const fs = require('fs');
const vm = require('vm');
const nodes = new Map();
const listeners = new Map();
const document = {{
  cookie: 'cookieConsent={consent}',
  head: {{
    appendChild(node) {{
      nodes.set(node.id, node);
      node._listeners?.load?.();
    }}
  }},
  getElementById(id) {{
    if (id === 'tracking-config') {{
      return {{ textContent: JSON.stringify({{ ga_measurement_id: 'G-TEST', clarity_project_id: '' }}) }};
    }}
    return nodes.get(id) || null;
  }},
  createElement() {{
    return {{
      dataset: {{}},
      addEventListener(name, callback) {{
        this._listeners = this._listeners || {{}};
        this._listeners[name] = callback;
      }}
    }};
  }}
}};
const window = {{
  location: {{ href: 'https://agecalc.cloud/guides/test?birth_date=secret', pathname: '/guides/test' }},
  history: {{ replaceState() {{}} }},
  addEventListener(name, callback) {{ listeners.set(name, callback); }},
  dispatchEvent() {{}},
}};
const context = {{ window, document, URL, console, Date, encodeURIComponent }};
vm.runInNewContext(fs.readFileSync({json.dumps(str(analytics_path))}, 'utf8'), context);
const tracked = window.AgeCalcTracking.trackEvent('reading_progress', {{
  percent: 50,
  content_type: 'guide',
  page_path: '/guides/test'
}});
const events = (window.dataLayer || []).map((args) => Array.from(args));
process.stdout.write(JSON.stringify({{ tracked, events }}));
"""
        completed = subprocess.run(
            ["node", "-e", program],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return json.loads(completed.stdout)

    def test_tracking_interface_sends_reading_event_after_consent(self):
        result = self.run_analytics_node("accepted")

        self.assertTrue(result["tracked"])
        self.assertIn(
            [
                "event",
                "reading_progress",
                {"percent": 50, "content_type": "guide", "page_path": "/guides/test"},
            ],
            result["events"],
        )

    def test_tracking_interface_rejects_event_without_consent(self):
        result = self.run_analytics_node("rejected")

        self.assertFalse(result["tracked"])
        self.assertFalse(any(event[0] == "event" for event in result["events"]))


if __name__ == "__main__":
    unittest.main()
