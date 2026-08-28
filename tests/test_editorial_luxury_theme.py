import re
import subprocess
import unittest
from pathlib import Path

from app import app


class EditorialLuxuryThemeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_representative_public_pages_load_final_theme(self):
        for path in ("/", "/age", "/about", "/references"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                self.assertIn("css/editorial-luxury.css", response.get_data(as_text=True))

    def test_theme_defines_approved_tokens_and_reduced_motion(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        for value in ("#F6F1E8", "#FCF9F3", "#241D18", "#66705A", "#A68B61", "#A34C3D"):
            self.assertIn(value.lower(), css.lower())
        self.assertNotIn("#efe6d8", css.lower())
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn(":focus-visible", css)
        self.assertTrue(Path("static/fonts/PretendardVariable.subset.woff2").read_bytes().startswith(b"wOF2"))

    def test_theme_limits_motion_to_transform_and_opacity(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        allowed_motion_properties = {"none", "transform", "opacity"}
        for match in re.finditer(r"(?<!-)\btransition\s*:\s*([^;]+);", css):
            transition_value = match.group(1).strip()
            for transition_part in transition_value.split(","):
                animated_property = transition_part.strip().split()[0]
                self.assertIn(animated_property, allowed_motion_properties, transition_value)
        for match in re.finditer(r"(?<!-)\banimation\s*:\s*([^;]+);", css):
            self.assertEqual("none !important", match.group(1).strip())

    def test_theme_enforces_accessible_mobile_menu_targets(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        for selector in (".menu-toggle", ".mobile-nav-close"):
            with self.subTest(selector=selector):
                blocks = "\n".join(
                    match.group("body")
                    for match in re.finditer(
                        rf"[^{{}}]*{re.escape(selector)}[^{{}}]*\{{(?P<body>[^}}]+)\}}",
                        css,
                        re.S,
                    )
                )
                self.assertRegex(blocks, r"\bmin-width:\s*44px;")
                self.assertRegex(blocks, r"\bmin-height:\s*44px;")

    def test_home_exposes_accessible_quick_age_calculator(self):
        html = self.client.get("/").get_data(as_text=True)
        self.assertIn('id="home-age-form"', html)
        self.assertIn('data-today="', html)
        self.assertIn('id="home-birth-input"', html)
        self.assertIn('type="date"', html)
        self.assertIn('aria-describedby="home-birth-help home-birth-error"', html)
        self.assertIn('id="home-birth-error" role="alert"', html)
        self.assertIn('id="home-age-result"', html)
        self.assertIn('id="home-age-value"', html)
        self.assertIn('href="/school-grade-calculator"', html)
        self.assertIn('href="/birthday-dday-calculator"', html)
        self.assertIn("js/home-age-calculator.js", html)
        self.assertNotIn('class="age-hub-dashboard"', html)
        self.assertNotIn('class="age-hub-result-card"', html)

    def test_home_calculator_module_handles_birthday_boundaries(self):
        program = r"""
const assert = require('assert');
global.document = { addEventListener() {} };
const { calculateSolarAge } = require('./static/js/home-age-calculator.js');
assert.deepStrictEqual(calculateSolarAge('1992-10-02', '2026-10-01').age, 33);
assert.deepStrictEqual(calculateSolarAge('1992-10-02', '2026-10-02').age, 34);
assert.strictEqual(calculateSolarAge('1992-10-02', '2026-10-01').daysToBirthday, 1);
assert.strictEqual(calculateSolarAge('1992-10-02', '2026-10-02').daysToBirthday, 0);
assert.strictEqual(calculateSolarAge('2000-02-29', '2026-02-28').daysToBirthday, 731);
assert.strictEqual(calculateSolarAge('2000-02-29', '2028-02-28').daysToBirthday, 1);
assert.strictEqual(calculateSolarAge('2000-02-29', '2028-02-29').daysToBirthday, 0);
assert.strictEqual(calculateSolarAge('2027-01-01', '2026-08-28').ok, false);
assert.strictEqual(calculateSolarAge('2024-02-30', '2026-08-28').ok, false);
"""
        result = subprocess.run(["node", "-e", program], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_archived_games_stay_reachable_but_hidden(self):
        for path in ("/minigames", "/minigames/guess", "/minigames/snake"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                self.assertEqual("noindex, nofollow", response.headers["X-Robots-Tag"])
                self.assertNotIn("css/editorial-luxury.css", response.get_data(as_text=True))

    def test_public_navigation_has_no_minigame_discovery_link(self):
        for path in ("/", "/age", "/about"):
            html = self.client.get(path).get_data(as_text=True)
            self.assertIsNone(re.search(r'href=["\']\/minigames(?:\/|["\'])', html))
