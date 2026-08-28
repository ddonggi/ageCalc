import re
import subprocess
import unittest
from pathlib import Path

from app import app

PUBLIC_THEME_TEMPLATES = (
    "100-day-calculator.html",
    "age-comparison-table.html",
    "age-gap-calculator.html",
    "baby-months-table.html",
    "birth-year-age-table.html",
    "birth-year-zodiac-table.html",
    "college-entry-year-calculator.html",
    "contact.html",
    "d-day.html",
    "faq.html",
    "grade-age-table.html",
    "grade-birth-year-table.html",
    "hub-detail.html",
    "korean-age-guide.html",
    "life-timeline.html",
    "parent-child.html",
    "pet-age-table.html",
    "pet-months-table.html",
    "privacy.html",
    "school-entry-year-table.html",
    "terms.html",
)


class EditorialLuxuryThemeTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def _css_without_comments(self, css):
        return re.sub(r"/\*.*?\*/", "", css, flags=re.S)

    def _ordinary_css_rules(self, css):
        css = self._css_without_comments(css)
        return [
            (
                tuple(" ".join(selector.split()) for selector in match.group("selectors").split(",") if selector.strip()),
                match.group("body"),
            )
            for match in re.finditer(r"(?P<selectors>[^{}@][^{}]*)\{(?P<body>[^{}]+)\}", css, re.S)
            if match.group("selectors").strip()
        ]

    def _css_rule_bodies(self, css, selector):
        css = self._css_without_comments(css)
        return "\n".join(
            match.group("body")
            for match in re.finditer(
                rf"(?P<selectors>[^{{}}]+)\{{(?P<body>[^}}]+)\}}",
                css,
                re.S,
            )
            if selector in match.group("selectors")
        )

    def _css_selector_groups_with_property(self, css, property_name):
        css = self._css_without_comments(css)
        return [
            match.group("selectors")
            for match in re.finditer(
                rf"(?P<selectors>[^{{}}]+)\{{(?P<body>[^}}]*\b{re.escape(property_name)}\s*:[^}}]+)\}}",
                css,
                re.S,
            )
        ]

    def _css_rule_body_for_exact_selector(self, css, selector):
        css = self._css_without_comments(css)
        for match in re.finditer(r"(?P<selectors>[^{}]+)\{(?P<body>[^}]+)\}", css, re.S):
            normalized_selector = " ".join(match.group("selectors").split())
            if normalized_selector == selector:
                return match.group("body")
        return ""

    def _selector_targets_result_table_or_numeric_ui(self, selector):
        element_pattern = r"(^|[\s>+~,(]){element}(?=[:.#\[\s>+~,)]+|$)"
        return (
            ".editorial-result-grid" in selector
            or ".metric-value" in selector
            or ".age-number" in selector
            or re.search(r"\.age-result-[\w-]+", selector)
            or any(
                re.search(element_pattern.format(element=element), selector)
                for element in ("output", "table", "th", "td")
            )
        )

    def _result_table_numeric_wrap_violations(self, css):
        violations = []
        for selectors, body in self._ordinary_css_rules(css):
            has_bad_wrapping = (
                re.search(r"\boverflow-wrap\s*:", body)
                or re.search(r"\bword-break\s*:\s*break-all\b", body)
            )
            if not has_bad_wrapping:
                continue
            for selector in selectors:
                if self._selector_targets_result_table_or_numeric_ui(selector):
                    violations.append((selector, " ".join(body.split())))
        return violations

    def test_representative_public_pages_load_final_theme(self):
        for path in ("/", "/age", "/about", "/references"):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(200, response.status_code)
                self.assertIn("css/editorial-luxury.css", response.get_data(as_text=True))

    def test_calculator_pages_use_shared_editorial_structure(self):
        for path in (
            "/age",
            "/annual-age-calculator",
            "/school-grade-calculator",
            "/birthday-dday-calculator",
            "/baby-months",
            "/dog",
            "/cat",
        ):
            with self.subTest(path=path):
                html = self.client.get(path).get_data(as_text=True)
                self.assertIn("editorial-calculator-page", html)
                self.assertIn("editorial-calculator-shell", html)
                self.assertIn("css/editorial-luxury.css", html)

    def test_content_templates_load_theme_and_keep_readable_prose_hook(self):
        for template_name in ("blog-list.html", "blog-detail.html", "guide.html", "guide-detail.html"):
            source = Path("templates", template_name).read_text()
            self.assertIn("editorial-luxury.css", source)
            self.assertRegex(source, r"editorial-(?:index|article|prose)")

    def test_remaining_public_templates_load_theme_after_legacy_css(self):
        for name in PUBLIC_THEME_TEMPLATES:
            source = Path("templates", name).read_text()
            self.assertLess(source.index("css/style.css"), source.index("css/editorial-luxury.css"), name)

    def test_theme_defines_public_page_family_layout_rules(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        self.assertRegex(css, r"\.data-table-wrap\s+thead\s+th[\s\S]*position:\s*sticky;")
        self.assertRegex(css, r"\.section-shell\.direct-answer\s*\~\s*section:not\(\[class\]\)[\s\S]*max-width:\s*65ch;")
        self.assertRegex(css, r"body\.life-hub-page\s+\.life-hub-hero[\s\S]*grid-template-columns:\s*minmax\(0,\s*1\.1fr\)\s+minmax\(280px,\s*\.75fr\);")

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

    def test_calculator_shell_footer_links_have_accessible_targets(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        blocks = "\n".join(
            match.group("body")
            for match in re.finditer(
                r"[^{}]*\.editorial-calculator-shell[^{}]*\.footer-links\s+a[^{}]*\{(?P<body>[^}]+)\}",
                css,
                re.S,
            )
        )
        self.assertRegex(blocks, r"\bdisplay:\s*inline-flex;")
        self.assertRegex(blocks, r"\balign-items:\s*center;")
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

    def test_home_quick_calculator_has_no_persistence_or_query_transport(self):
        script = Path("static/js/home-age-calculator.js").read_text()
        self.assertNotIn("localStorage", script)
        self.assertNotIn("sessionStorage", script)
        self.assertNotIn("URLSearchParams", script)
        self.assertNotIn("fetch(", script)

    def test_theme_has_touch_target_and_mobile_overflow_guards(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        public_body_selector = 'body:not(.games-hub-page):not(.snake-page):not([class$="-game-page"])'
        self.assertRegex(css, r"min-height:\s*44px")
        self.assertNotIn("overflow-wrap", self._css_rule_body_for_exact_selector(css, public_body_selector))

        expected_overflow_selectors = (
            f"{public_body_selector} .editorial-prose",
            f"{public_body_selector} .blog-content",
            f"{public_body_selector} .guide-content",
            f"{public_body_selector} .section-shell.direct-answer ~ section:not([class])",
            f"{public_body_selector} .contact-info",
            f"{public_body_selector} .contact-info a",
            f"{public_body_selector} .footer .footer-links a",
            f"{public_body_selector} .editorial-filter-nav a",
            f"{public_body_selector} [data-editorial-related-paths] a",
            f"{public_body_selector} .editorial-article .article-links a",
            f"{public_body_selector} .editorial-story-summary",
            f"{public_body_selector} .coupang-disclosure",
            f"{public_body_selector} .home-coupang-disclosure",
            f"{public_body_selector} .coupang-partners-aside p",
        )
        overflow_groups = [
            tuple(" ".join(selector.split()) for selector in group.split(","))
            for group in self._css_selector_groups_with_property(css, "overflow-wrap")
        ]
        self.assertIn(expected_overflow_selectors, overflow_groups)
        self.assertIn("overflow-wrap: anywhere", self._css_rule_bodies(css, ".editorial-prose"))
        overflow_group = "\n".join(expected_overflow_selectors)
        for excluded_selector in (
            ".editorial-result-grid",
            "output",
            ".data-table",
            " table",
            " th",
            " td",
            ".metric-value",
        ):
            self.assertNotIn(excluded_selector, overflow_group)
        self.assertEqual([], self._result_table_numeric_wrap_violations(css))
        self.assertNotRegex(css, r"transition:\s*(?:all\s+)?(?:linear|ease-in-out)")

    def test_theme_overflow_guard_detects_result_table_numeric_mutations(self):
        css = """
        .safe-prose {
          overflow-wrap: anywhere;
        }

        .editorial-result-grid output,
        .metric-value,
        .age-result-summary-item,
        table,
        th,
        td {
          word-break: break-all;
        }
        """
        violations = self._result_table_numeric_wrap_violations(css)
        self.assertEqual(
            [
                (".editorial-result-grid output", "word-break: break-all;"),
                (".metric-value", "word-break: break-all;"),
                (".age-result-summary-item", "word-break: break-all;"),
                ("table", "word-break: break-all;"),
                ("th", "word-break: break-all;"),
                ("td", "word-break: break-all;"),
            ],
            violations,
        )

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
