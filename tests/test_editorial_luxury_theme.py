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

    def _css_hex_token(self, css, token):
        match = re.search(rf"{re.escape(token)}\s*:\s*(#[0-9a-f]{{6}})\s*;", css, re.I)
        self.assertIsNotNone(match, token)
        return match.group(1)

    def _contrast_ratio(self, foreground, background):
        def relative_luminance(color):
            channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            channels = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]

        lighter, darker = sorted(
            (relative_luminance(foreground), relative_luminance(background)),
            reverse=True,
        )
        return (lighter + 0.05) / (darker + 0.05)

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
                response = self.client.get(path, follow_redirects=True)
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

    def test_calculator_flat_layout_prioritizes_form_without_flattening_inner_cards(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        self.assertIn("body.calculator-flat-page .container > *", css)
        self.assertIn("body.calculator-flat-page .calculator-page-heading.hero-band", css)
        self.assertIn("body.calculator-flat-page .container > .editorial-calculator-shell", css)
        self.assertIn("body.calculator-flat-page .container > .section-shell.direct-answer", css)
        self.assertIn("body.calculator-flat-page .editorial-supporting-content .info", css)
        self.assertRegex(
            css,
            r"body\.calculator-flat-page \.section-shell,\nbody\.calculator-flat-page \.age-form,\nbody\.calculator-flat-page \.result-container\.show[\s\S]*?\{[\s\S]*?border:\s*0;[\s\S]*?background:\s*transparent;[\s\S]*?box-shadow:\s*none;",
        )
        self.assertIn("body.calculator-flat-page .section-card-grid", css)
        self.assertIn("body.calculator-flat-page .section-card:not(.birth-year-summary)", css)
        self.assertIn("body.calculator-flat-page .container > .section-shell.direct-answer", css)
        self.assertIn("background: transparent;", css)
        self.assertIn("border: 0;", css)
        self.assertIn("box-shadow: none;", css)
        self.assertIn("@media (max-width: 760px)", css)

    def test_calendar_toggle_uses_an_animated_selected_slider(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        slider = self._css_rule_body_for_exact_selector(
            css,
            "body.editorial-calculator-page .editorial-calculator-shell .calendar-toggle .toggle-slider"
        )

        self.assertIn("transition: transform 180ms", slider)
        self.assertRegex(
            css,
            r"#lunar:checked\s*~\s*\.toggle-slider\s*\{[^}]*transform:\s*translateX\(100%\);",
        )
        self.assertRegex(
            css,
            r"@media\s*\(prefers-reduced-motion:\s*reduce\)[\s\S]*?transition:\s*none\s*!important;",
        )

    def test_calculator_inputs_stack_vertically_without_a_toggle_container_outline(self):
        editorial_css = Path("static/css/editorial-luxury.css").read_text()
        base_css = Path("static/css/style.css").read_text()

        input_layout = self._css_rule_bodies(
            editorial_css,
            "body.editorial-calculator-page .editorial-calculator-shell .form-group",
        )
        self.assertIn("display: flex;", input_layout)
        self.assertIn("flex-direction: column;", input_layout)
        self.assertIn("gap: .75rem;", input_layout)
        self.assertNotIn(".calendar-toggle:focus-within", self._css_without_comments(base_css))

    def test_age_form_primary_button_matches_the_input_width(self):
        css = Path("static/css/style.css").read_text()
        button_rule = self._css_rule_body_for_exact_selector(css, ".age-form .btn-primary")

        self.assertIn("width: 100%;", button_rule)

    def test_calculator_and_home_panels_share_a_control_layout_rhythm(self):
        css = Path("static/css/editorial-luxury.css").read_text()

        self.assertRegex(
            css,
            r"body\.calculator-flat-page \.editorial-calculator-shell,[\s\S]*?"
            r"body\.calculator-flat-page \.section-shell:has\(> \.age-form\)\s*\{[\s\S]*?"
            r"gap:\s*clamp\(1rem, 2\.5vw, 1\.5rem\);",
        )
        panel_core = self._css_rule_body_for_exact_selector(
            css,
            ".home-page .editorial-hero .editorial-panel-core",
        )
        self.assertIn("gap: clamp(1rem, 2.5vw, 1.5rem);", panel_core)
        self.assertNotIn("min-height", panel_core)

    def test_all_public_and_game_styles_use_the_body_font_except_brand_word(self):
        css_files = tuple(Path("static/css").glob("*.css"))
        for css_file in css_files:
            with self.subTest(css_file=css_file):
                css = self._css_without_comments(css_file.read_text())
                for selectors, body in self._ordinary_css_rules(css):
                    if (
                        "font-family:" not in body
                        or any(".brand-word" in selector for selector in selectors)
                        or any(selector.lstrip().startswith("@") for selector in selectors)
                        or "src:" in body
                    ):
                        continue
                    font_families = re.findall(r"font-family:\s*([^;]+);", body)
                    self.assertEqual(
                        ["var(--site-font)"] * len(font_families),
                        [font_family.strip() for font_family in font_families],
                        "Only .brand-word may use --lux-brand.",
                    )

    def test_public_heading_scale_is_compact_without_changing_games(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        compact_selector = (
            r"body"
        )
        for heading, expected in {
            "h1": "clamp(2.1rem, 4vw, 4.2rem)",
            "h2": "clamp(1.35rem, 2.2vw, 2.1rem)",
            "h3": "clamp(1rem, 1.5vw, 1.25rem)",
            "h4": "clamp(.95rem, 1.2vw, 1.05rem)",
        }.items():
            self.assertRegex(
                css,
                rf"{compact_selector}\s+{heading}\s*\{{[^}}]*font-size:\s*{re.escape(expected)}\s*!important;",
            )

    def test_heading_tags_do_not_have_max_width_constraints(self):
        for css_path in (Path("static/css/style.css"), Path("static/css/editorial-luxury.css")):
            css = self._css_without_comments(css_path.read_text())
            for selectors, body in self._ordinary_css_rules(css):
                for selector in selectors:
                    if re.search(r"(?:^|[ >+~])h[1-6](?::[\w-]+)?$", selector.strip()):
                        self.assertNotIn("max-width", body, selector)

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
        self.assertNotIn("life-hub-hero", css)

    def test_non_home_heroes_are_flat_and_header_has_no_active_style(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        base_css = Path("static/css/style.css").read_text()

        self.assertRegex(
            theme_css,
            r"body:not\(\.home-page\)\s+\.hero-band\s*\{[^}]*border:\s*0;[^}]*border-radius:\s*0;",
        )
        self.assertNotIn(".hub-nav-direct.is-active", theme_css)
        self.assertNotIn(".hub-nav-direct.is-active", base_css)

    def test_all_heroes_share_the_body_canvas_without_shadows(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        hero_selector = "body .hero-band"

        hero_rules = self._css_rule_bodies(theme_css, hero_selector)
        self.assertIn("border: 0;", hero_rules)
        self.assertIn("border-radius: 0;", hero_rules)
        self.assertIn("background: transparent;", hero_rules)
        self.assertIn("box-shadow: none;", hero_rules)
        self.assertNotIn("body .hero-band::after", theme_css)

    def test_public_sections_use_a_flat_canvas_with_editorial_dividers(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        public_selector = "body"

        section_shell_rules = self._css_rule_bodies(theme_css, f"{public_selector} .section-shell")
        self.assertIn("border: 0 !important;", section_shell_rules)
        self.assertIn("border-top: 1px solid var(--lux-border-strong) !important;", section_shell_rules)
        self.assertIn("border-radius: 0 !important;", section_shell_rules)
        self.assertNotIn("background: transparent !important;", section_shell_rules)
        self.assertIn("box-shadow: none !important;", section_shell_rules)

        for selector in (".info", ".related-paths"):
            with self.subTest(selector=selector):
                rules = self._css_rule_bodies(theme_css, f"{public_selector} {selector}")
                self.assertIn("border: 0;", rules)
                self.assertIn("border-radius: 0;", rules)
                self.assertNotIn("background: transparent;", rules)
                self.assertIn("box-shadow: none;", rules)

        footer_rules = self._css_rule_bodies(theme_css, f"{public_selector} .footer")
        self.assertIn("border: 0;", footer_rules)
        self.assertIn("border-radius: 0;", footer_rules)
        self.assertIn("background: transparent;", footer_rules)
        self.assertIn("box-shadow: none;", footer_rules)

    def test_full_bleed_footer_clips_viewport_unit_scrollbar_overflow(self):
        css = Path("static/css/editorial-luxury.css").read_text()

        html_rules = self._css_rule_bodies(css, "html")
        self.assertIn("overflow-x: clip;", html_rules)

    def test_home_editorial_hero_title_has_no_character_width_cap(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        title_rules = self._css_rule_bodies(theme_css, ".home-page .editorial-hero-copy h1")
        self.assertNotIn("max-width:", title_rules)

    def test_hub_tool_list_uses_the_life_hub_link_list_structure(self):
        source = Path("templates/hub-detail.html").read_text()
        tool_list = source.split('aria-labelledby="hub-tools-title"', 1)[1].split("</section>", 1)[0]
        self.assertIn('class="life-hub-link-list hub-tool-link-list"', tool_list)
        self.assertNotIn("hub-card calendar-card", tool_list)
        self.assertNotIn("자세히 보기", tool_list)

        theme_css = Path("static/css/editorial-luxury.css").read_text()
        self.assertRegex(
            theme_css,
            r"body \.life-hub-link-list\s*\{[^}]*gap:\s*\.75rem;[^}]*border:\s*0;",
        )
        self.assertRegex(
            theme_css,
            r"body \.life-hub-link-list a\s*\{[^}]*border:\s*1px solid var\(--lux-border\);[^}]*border-radius:\s*10px;",
        )
        self.assertNotIn("border-right: 1px solid var(--lux-border);", theme_css.split("body.home-page .home-life-hub-card", 1)[1].split("}", 1)[0])

    def test_home_life_hubs_use_editorial_dividers_instead_of_cards(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        grid_rules = self._css_rule_bodies(theme_css, "body.home-page .home-life-hub-grid")
        card_rules = self._css_rule_bodies(theme_css, "body.home-page .home-life-hub-card")
        article_rules = self._css_rule_bodies(theme_css, "body.home-page .home-life-hub-card article")

        self.assertIn("border: 0;", grid_rules)
        self.assertNotIn("border-right: 1px solid var(--lux-border);", card_rules)
        self.assertIn("background: transparent !important;", card_rules)
        self.assertIn("box-shadow: none !important;", card_rules)
        self.assertIn("transform: none !important;", card_rules)
        self.assertIn("border: 1px solid rgba(166, 139, 97, .42) !important;", article_rules)
        self.assertIn("background: var(--lux-surface) !important;", article_rules)
        self.assertIn("box-shadow: 0 16px 36px rgba(36, 29, 24, .10) !important;", article_rules)
        self.assertNotIn("body.home-page .life-hub-link-list a", theme_css)

        self.assertRegex(
            theme_css,
            r"@media\s*\(max-width:\s*760px\)\s*\{[\s\S]*?body\.home-page\s+\.home-life-hub-grid\s*\{[^}]*grid-template-columns:\s*1fr;",
        )

    def test_all_public_hero_surfaces_and_decorations_are_flat(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        public_selector = "body"
        hero_rules = self._css_rule_bodies(
            theme_css,
            f"{public_selector} :is(.hero-band, [class*=\"-hero\"])",
        )
        self.assertIn("background: transparent !important;", hero_rules)
        self.assertIn("box-shadow: none !important;", hero_rules)
        decoration_rules = self._css_rule_bodies(
            theme_css,
            f"{public_selector} [class*=\"-hero\"]::before",
        )
        self.assertIn("background: none !important;", decoration_rules)
        self.assertIn("box-shadow: none !important;", decoration_rules)

    def test_header_category_links_do_not_change_on_hover(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        base_css = Path("static/css/style.css").read_text()

        self.assertNotIn(".hub-nav-direct:hover", theme_css)
        self.assertNotIn(".hub-nav-direct:hover", base_css)
        self.assertIn(":focus-visible", theme_css)

    def test_mobile_menu_toggle_stays_flat_when_interacted_with(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()

        self.assertRegex(
            theme_css,
            r"body \.menu-toggle,\s*body \.menu-toggle:hover,\s*body \.menu-toggle:focus-visible\s*\{[^}]*"
            r"border:\s*0;[^}]*background:\s*transparent;[^}]*transform:\s*none;",
        )

    def test_navigation_panels_have_no_border_or_radius(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        panel_rules = self._css_rule_bodies(theme_css, "body .mega-menu-panel,\nbody .mobile-nav-panel")
        self.assertIn("border: 0;", panel_rules)
        self.assertIn("border-radius: 0;", panel_rules)

    def test_home_hero_and_header_use_a_single_unstacked_surface(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        base_css = Path("static/css/style.css").read_text()
        header_selector = "body .site-header"

        self.assertRegex(
            theme_css,
            r"\.home-page\s+\.editorial-hero\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\);[^}]*align-items:\s*start;",
        )
        self.assertRegex(
            theme_css,
            r"\.home-page\s+\.editorial-hero\s+\.editorial-panel-shell\s*\{[^}]*justify-self:\s*stretch;[^}]*transform:\s*none;",
        )
        self.assertRegex(
            theme_css,
            r"\.editorial-panel-shell::before,[\s\S]*?\.editorial-panel-shell::after\s*\{[^}]*display:\s*none;",
        )
        self.assertNotRegex(base_css, r"\.calendar-card-1\s*\{[^}]*transform:")
        header_rules = self._css_rule_bodies(theme_css, header_selector)
        self.assertIn("border: 0;", header_rules)
        self.assertIn("border-bottom: 1px solid var(--lux-border);", header_rules)
        self.assertIn("border-radius: 0;", header_rules)
        self.assertIn("display: none;", self._css_rule_bodies(theme_css, f"{header_selector}::before"))
        self.assertNotRegex(
            theme_css,
            rf"{re.escape(header_selector)}\s*\{{[^}}]*border-radius:\s*16px;",
        )

    def test_home_title_and_calculator_panel_use_a_wider_flat_surface(self):
        theme_css = Path("static/css/editorial-luxury.css").read_text()
        title_rules = self._css_rule_bodies(theme_css, ".home-page .editorial-hero-copy h1")
        shell_rules = self._css_rule_bodies(theme_css, ".home-page .editorial-hero .editorial-panel-shell")
        core_rules = self._css_rule_bodies(theme_css, ".home-page .editorial-hero .editorial-panel-core")

        self.assertIn("font-size: clamp(1.9rem, 2.7vw, 2.4rem);", title_rules)
        self.assertIn("width: 100%;", shell_rules)
        self.assertIn("padding: 0;", shell_rules)
        self.assertNotIn("border: 1px solid rgba(166, 139, 97, .42);", shell_rules)
        self.assertIn("border-radius: 0;", shell_rules)
        self.assertIn("background: transparent;", shell_rules)
        self.assertIn("box-shadow: none;", shell_rules)
        self.assertIn("border: 0;", core_rules)
        self.assertIn("border-radius: var(--lux-radius-core);", core_rules)
        self.assertIn("box-shadow: none;", core_rules)

    def test_home_prioritizes_life_paths_and_aligns_hub_actions(self):
        source = Path("templates/index.html").read_text()
        self.assertLess(source.index('class="section-shell home-life-hubs"'), source.index('class="section-shell home-quick-tools"'))
        self.assertEqual(4, self.client.get("/").get_data(as_text=True).count("계산하러 가기"))
        self.assertNotIn("허브 보기", source)

        theme_css = Path("static/css/editorial-luxury.css").read_text()
        card_rules = self._css_rule_bodies(theme_css, "body.home-page .home-life-hub-card article")
        button_rules = self._css_rule_bodies(theme_css, "body.home-page #home-age-form .btn-primary")
        self.assertIn("grid-template-rows: auto auto auto 1fr auto;", card_rules)
        self.assertIn("background: var(--lux-gold);", button_rules)
        self.assertIn("border-color: var(--lux-gold);", button_rules)
        self.assertIn("color: var(--lux-espresso);", button_rules)

    def test_home_quick_reference_uses_the_life_hub_link_list(self):
        source = Path("templates/index.html").read_text()
        quick_tools = source.split('class="section-shell home-quick-tools"', 1)[1].split("</section>", 1)[0]
        self.assertIn('class="life-hub-link-list"', quick_tools)
        self.assertNotIn('class="home-quick-links"', quick_tools)

    def test_theme_defines_approved_tokens_and_reduced_motion(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        for value in ("#F6F1E8", "#FCF9F3", "#241D18", "#66705A", "#A68B61", "#A34C3D"):
            self.assertIn(value.lower(), css.lower())
        self.assertNotIn("#efe6d8", css.lower())
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)
        self.assertIn(":focus-visible", css)
        self.assertTrue(Path("static/fonts/PretendardVariable.subset.woff2").read_bytes().startswith(b"wOF2"))

    def test_theme_small_text_color_pairs_meet_wcag_aa(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        surface = self._css_hex_token(css, "--lux-surface")
        danger = self._css_hex_token(css, "--lux-danger")
        muted = self._css_hex_token(css, "--lux-muted")

        home_error = self._css_rule_bodies(css, ".home-page #home-birth-error:not(:empty)")
        self.assertIn("color: var(--lux-danger);", home_error)
        self.assertIn("background: var(--lux-surface);", home_error)

        for selector in (
            ".editorial-story-meta",
            ".editorial-meta dt",
            ".editorial-ad-label",
            ".coupang-disclosure",
            ".home-coupang-disclosure",
            ".coupang-partners-aside p",
        ):
            with self.subTest(selector=selector):
                self.assertIn(
                    "color: var(--lux-muted);",
                    self._css_rule_bodies(css, selector),
                )

        self.assertGreaterEqual(self._contrast_ratio(danger, surface), 4.5)
        self.assertGreaterEqual(self._contrast_ratio(muted, surface), 4.5)

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
        self.assertRegex(
            html,
            r'<input id="home-birth-input" type="text" placeholder="19921002" inputmode="numeric" pattern="\[0-9\]\*" maxlength="8"',
        )
        self.assertIn('aria-describedby="home-birth-error"', html)
        self.assertNotIn("입력한 날짜는 저장하지 않습니다.", html)
        self.assertIn('id="home-birth-error" role="alert"', html)
        self.assertIn('id="home-age-result"', html)
        self.assertIn('id="home-age-value"', html)
        self.assertIn('id="home-grade-link"', html)
        self.assertIn('data-calculator-url="/school-grade-calculator"', html)
        self.assertIn('href="/birthday-dday-calculator"', html)
        self.assertIn("js/home-age-calculator.js", html)
        self.assertNotIn('class="age-hub-dashboard"', html)
        self.assertNotIn('class="age-hub-result-card"', html)

    def test_calculator_forms_load_focus_and_enter_submit_behavior(self):
        html = self.client.get("/age").get_data(as_text=True)
        script_path = Path("static/js/calculator-form-focus.js")

        self.assertIn("js/calculator-form-focus.js", html)
        self.assertTrue(script_path.is_file())
        script = script_path.read_text()
        self.assertIn("form.requestSubmit()", script)
        self.assertIn("resultTarget", script)
        self.assertIn("input.focus", script)

    def test_home_grade_link_uses_the_calculated_birth_year(self):
        script = Path("static/js/home-age-calculator.js").read_text()

        self.assertIn('getElementById("home-grade-link")', script)
        self.assertIn('"?year=" + birthYear', script)

    def test_calculator_form_focus_script_focuses_and_submits_a_text_input(self):
        program = r"""
const assert = require('assert');
const listeners = {};
let prevented = false;
let submitCount = 0;

class FakeInput {
  constructor() {
    this.type = 'text';
    this.disabled = false;
    this.readOnly = false;
    this.focused = false;
  }
  focus(options) { this.focused = Boolean(options && options.preventScroll); }
  closest() { return form; }
}

const input = new FakeInput();
const form = {
  elements: [input],
  matches(selector) { return selector.includes('calculator-flat-page'); },
  requestSubmit() { submitCount += 1; }
};

global.HTMLInputElement = FakeInput;
global.window = { location: { hash: '' } };
global.document = {
  addEventListener(name, listener) { listeners[name] = listener; },
  getElementById() { return null; },
  querySelector() { return form; }
};

require('./static/js/calculator-form-focus.js');
listeners.DOMContentLoaded();
assert.strictEqual(input.focused, true);
listeners.keydown({
  key: 'Enter',
  target: input,
  preventDefault() { prevented = true; }
});
assert.strictEqual(prevented, true);
assert.strictEqual(submitCount, 1);
"""
        result = subprocess.run(["node", "-e", program], capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)

    def test_home_quick_calculator_has_no_persistence_or_query_transport(self):
        script = Path("static/js/home-age-calculator.js").read_text()
        self.assertNotIn("localStorage", script)
        self.assertNotIn("sessionStorage", script)
        self.assertNotIn("URLSearchParams", script)
        self.assertNotIn("fetch(", script)

    def test_theme_has_touch_target_and_mobile_overflow_guards(self):
        css = Path("static/css/editorial-luxury.css").read_text()
        public_body_selector = "body"
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
assert.deepStrictEqual(calculateSolarAge('19921002', '2026-10-02').age, 34);
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

    def test_removed_game_routes_are_not_reachable(self):
        for path in ("/minigames", "/minigames/guess", "/minigames/snake"):
            with self.subTest(path=path):
                response = self.client.get(path, follow_redirects=True)
                self.assertEqual(404, response.status_code)

    def test_public_navigation_has_no_minigame_discovery_link(self):
        for path in ("/", "/age", "/about"):
            html = self.client.get(path).get_data(as_text=True)
            self.assertIsNone(re.search(r'href=["\']\/minigames(?:\/|["\'])', html))
