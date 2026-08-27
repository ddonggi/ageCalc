import re
import unittest

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
