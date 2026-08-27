import re
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
        self.assertIn('id="home-birth-input"', html)
        self.assertIn('aria-describedby="home-birth-help home-birth-error"', html)
        self.assertIn('id="home-age-result"', html)

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
