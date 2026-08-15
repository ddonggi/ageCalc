import json
import re
import unittest
from datetime import date, datetime
from html.parser import HTMLParser
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

from flask import render_template, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app as app_module
import content.guide_pages as guide_pages_module
from content.hub_pages import HUB_PAGES
from content.page_registry import PUBLIC_PAGE_REGISTRY
from app import PUBLIC_SITEMAP_ENDPOINTS, app, _current_local_date
from db import Base
from content.guide_pages import (
    GUIDE_CATEGORIES,
    GUIDE_PAGES,
    GUIDE_SLUGS,
)
from models.blog_models import GeneratedPost, PageFeedback


def _sitemap_leaf_locations(client) -> list[str]:
    root_xml = client.get("/sitemap.xml").get_data(as_text=True)
    root_locations = re.findall(r"<loc>(.*?)</loc>", root_xml)
    if "<sitemapindex" not in root_xml:
        return root_locations

    locations = []
    for child_location in root_locations:
        child_path = child_location.removeprefix("https://agecalc.cloud")
        child_xml = client.get(child_path).get_data(as_text=True)
        locations.extend(re.findall(r"<loc>(.*?)</loc>", child_xml))
    return locations


class _PageMarkupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_json_ld = False
        self.json_ld_buffer = []
        self.json_ld_blocks = []
        self.text_parts = []
        self.link_stack = []
        self.images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "a":
            self.link_stack.append(attributes)
        if tag == "img":
            self.images.append((attributes, self.link_stack[-1] if self.link_stack else None))
        if tag == "script" and attributes.get("type") == "application/ld+json":
            self.in_json_ld = True
            self.json_ld_buffer = []

    def handle_data(self, data):
        if self.in_json_ld:
            self.json_ld_buffer.append(data)
        else:
            self.text_parts.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self.in_json_ld:
            self.json_ld_blocks.append("".join(self.json_ld_buffer))
            self.in_json_ld = False
        if tag == "a" and self.link_stack:
            self.link_stack.pop()


def _parse_page_markup(html):
    parser = _PageMarkupParser()
    parser.feed(html)
    return [json.loads(block) for block in parser.json_ld_blocks], " ".join(parser.text_parts)


class PublicPageTests(unittest.TestCase):
    def test_public_images_reserve_space_and_have_accessible_text(self):
        client = app.test_client()

        for page in PUBLIC_PAGE_REGISTRY:
            path = str(page["path"])
            with self.subTest(path=path):
                parser = _PageMarkupParser()
                parser.feed(client.get(path).get_data(as_text=True))

                for image, parent_link in parser.images:
                    self.assertGreater(int(image.get("width", "0")), 0)
                    self.assertGreater(int(image.get("height", "0")), 0)
                    self.assertIn("alt", image)
                    if image["alt"] == "" and parent_link is not None:
                        self.assertTrue(parent_link.get("aria-label"))

    def test_optional_affiliate_images_follow_decorative_image_contract(self):
        partials = (
            "partials/coupang_age_affiliate.html",
            "partials/coupang_anniversary_affiliate.html",
            "partials/coupang_baby_promotions.html",
            "partials/coupang_carousel.html",
            "partials/coupang_pet_affiliate.html",
            "partials/coupang_student_affiliate.html",
            "partials/info_coupang_promotions.html",
        )
        promotion = {
            "title": "테스트 프로모션",
            "url": "https://example.com/promotion",
            "image_url": "https://example.com/promotion.png",
            "alt": "테스트 프로모션 이미지",
            "width": 800,
            "height": 800,
        }

        with app.test_request_context("/"):
            for partial in partials:
                with self.subTest(partial=partial):
                    html = render_template(
                        partial,
                        coupang_partners_enabled=True,
                        coupang_carousel_enabled=True,
                        coupang_active_baby_promotions=[promotion],
                        coupang_event_promotions=[promotion],
                    )
                    parser = _PageMarkupParser()
                    parser.feed(html)

                    self.assertTrue(parser.images)
                    for image, parent_link in parser.images:
                        self.assertGreater(int(image.get("width", "0")), 0)
                        self.assertGreater(int(image.get("height", "0")), 0)
                        self.assertIn("alt", image)
                        if image["alt"] == "":
                            self.assertIsNotNone(parent_link)
                            self.assertTrue(parent_link.get("aria-label"))

    def test_public_structured_data_uses_the_page_canonical(self):
        client = app.test_client()
        urls = [
            *(str(page["path"]) for page in PUBLIC_PAGE_REGISTRY),
            "/birth-year-age-table?year=2010",
            "/college-entry-year-calculator?year=2024",
            "/college-entry-year-calculator?year=2025",
            "/college-entry-year-calculator?year=2026",
        ]

        for url in urls:
            with self.subTest(url=url):
                response = client.get(url)
                html = response.get_data(as_text=True)
                canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
                schemas, _ = _parse_page_markup(html)
                web_pages = [schema for schema in schemas if schema.get("@type") == "WebPage"]

                self.assertEqual(1, len(web_pages))
                self.assertEqual(canonical, web_pages[0]["url"])
                self.assertIn(f'<meta property="og:url" content="{canonical}"', html)

                breadcrumbs = [
                    schema for schema in schemas if schema.get("@type") == "BreadcrumbList"
                ]
                if url != "/":
                    self.assertEqual(1, len(breadcrumbs))
                    self.assertEqual(
                        canonical,
                        breadcrumbs[0]["itemListElement"][-1]["item"],
                    )

    def test_faq_structured_data_is_visible_on_the_same_page(self):
        client = app.test_client()

        for url in ("/age", "/faq"):
            with self.subTest(url=url):
                html = client.get(url).get_data(as_text=True)
                schemas, visible_text = _parse_page_markup(html)
                visible_text = re.sub(r"\s+", " ", visible_text)
                faq_pages = [schema for schema in schemas if schema.get("@type") == "FAQPage"]

                self.assertEqual(1, len(faq_pages))
                for question in faq_pages[0]["mainEntity"]:
                    self.assertIn(re.sub(r"\s+", " ", question["name"]), visible_text)
                    self.assertIn(
                        re.sub(r"\s+", " ", question["acceptedAnswer"]["text"]),
                        visible_text,
                    )

    def test_health_api_is_available_but_blocked_from_indexing(self):
        client = app.test_client()

        for method in (client.get, client.head):
            with self.subTest(method=method.__name__):
                response = method("/health")

                self.assertEqual(200, response.status_code)
                self.assertTrue(response.content_type.startswith("application/json"))
                self.assertEqual("noindex, nofollow", response.headers.get("X-Robots-Tag"))

        self.assertEqual({"ok": True}, client.get("/health").get_json())

    def test_conflicting_legacy_hub_urls_redirect_to_dedicated_hub_paths(self):
        client = app.test_client()
        cases = {
            "/age/": "/age-tools/",
            "/health/": "/health-tools/",
        }

        for source, target in cases.items():
            with self.subTest(source=source):
                response = client.get(source, follow_redirects=False)
                self.assertEqual(301, response.status_code)
                self.assertEqual(target, response.headers["Location"])

                query_response = client.get(
                    f"{source}?source=legacy", follow_redirects=False
                )
                self.assertEqual(301, query_response.status_code)
                self.assertEqual(
                    f"{target}?source=legacy", query_response.headers["Location"]
                )

    def test_public_canonical_trailing_slash_variants_redirect_permanently(self):
        client = app.test_client()
        cases = {
            "/about/": "/about",
            "/birth-year-age-table/": "/birth-year-age-table",
            "/guides/age-calculation-2026/": "/guides/age-calculation-2026",
        }

        for source, target in cases.items():
            with self.subTest(source=source):
                response = client.get(source, follow_redirects=False)
                self.assertEqual(301, response.status_code)
                self.assertEqual(target, response.headers["Location"])

                query_response = client.get(
                    f"{source}?utm_source=test", follow_redirects=False
                )
                self.assertEqual(
                    f"{target}?utm_source=test", query_response.headers["Location"]
                )

        self.assertEqual(404, client.get("/unknown/", follow_redirects=False).status_code)
        self.assertEqual(404, client.get("/llms.txt/", follow_redirects=False).status_code)

        for page in PUBLIC_PAGE_REGISTRY:
            path = str(page["path"])
            with self.subTest(canonical_path=path):
                self.assertEqual(200, client.get(path).status_code)
                if path == "/" or path.endswith("/") or path in {"/age", "/health"}:
                    continue
                slash_response = client.head(f"{path}/", follow_redirects=False)
                self.assertEqual(301, slash_response.status_code)
                self.assertEqual(path, slash_response.headers["Location"])

    def test_hub_canonical_paths_and_slashless_redirects_are_consistent(self):
        client = app.test_client()
        cases = {
            "age-tools": "나이 계산",
            "family": "가족·육아",
            "health-tools": "건강·검진",
        }

        for slug, title in cases.items():
            with self.subTest(slug=slug):
                canonical_path = f"/{slug}/"
                response = client.get(canonical_path)
                self.assertEqual(200, response.status_code)
                self.assertIn(f"<h1>{title}</h1>", response.get_data(as_text=True))
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{canonical_path}" />',
                    response.get_data(as_text=True),
                )

                slashless = client.get(f"/{slug}", follow_redirects=False)
                self.assertEqual(308, slashless.status_code)
                self.assertTrue(slashless.headers["Location"].endswith(canonical_path))

    def test_non_review_sitemaps_use_only_dedicated_conflict_free_hub_paths(self):
        client = app.test_client()
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False):
            age_xml = client.get("/sitemaps/age.xml").get_data(as_text=True)
            health_xml = client.get("/sitemaps/health.xml").get_data(as_text=True)

        self.assertIn("https://agecalc.cloud/age-tools/", age_xml)
        self.assertNotIn("https://agecalc.cloud/age/</loc>", age_xml)
        self.assertIn("https://agecalc.cloud/health-tools/", health_xml)
        self.assertNotIn("https://agecalc.cloud/health/</loc>", health_xml)

    def test_llms_txt_is_served_at_root_as_plain_text(self):
        client = app.test_client()
        response = client.get("/llms.txt")
        body = response.get_data(as_text=True)
        response.close()
        expected_body = (Path(app.root_path) / "static" / "llms.txt").read_text(
            encoding="utf-8"
        )

        self.assertEqual(200, response.status_code)
        self.assertTrue(response.content_type.startswith("text/plain"))
        self.assertEqual(expected_body, body)
        self.assertTrue(body.startswith("# AgeCalc\n"))
        self.assertNotIn("?", body)
        self.assertNotIn("localhost", body)

        links = re.findall(r"\]\((https://agecalc\.cloud[^)]+)\)", body)
        self.assertEqual(len(links), len(set(links)))
        self.assertTrue(all("?" not in link and "#" not in link for link in links))
        for path in (
            "/age",
            "/birth-year-age-table",
            "/school-grade-calculator",
            "/college-entry-year-calculator",
            "/100-day-calculator",
            "/pet-age-table",
            "/references",
        ):
            self.assertIn(f"https://agecalc.cloud{path}", links)

        head_response = client.head("/llms.txt")
        head_response.close()
        self.assertEqual(200, head_response.status_code)
        self.assertNotIn("Location", head_response.headers)

    def test_llms_txt_trailing_slash_is_not_a_duplicate(self):
        response = app.test_client().get("/llms.txt/", follow_redirects=False)
        response.close()

        self.assertEqual(404, response.status_code)
        self.assertNotIn("Location", response.headers)

    def test_seo_query_routes_redirect_invalid_values_to_clean_urls(self):
        client = app.test_client()
        invalid_urls = {
            "/birth-year-age-table?year=": "/birth-year-age-table",
            "/birth-year-age-table?year=unknown": "/birth-year-age-table",
            "/birth-year-age-table?year=1800": "/birth-year-age-table",
            "/school-grade-calculator?year=": "/school-grade-calculator",
            "/school-entry-year-table?year=2024~2026": "/school-entry-year-table",
            "/grade-age-table?stage=middle&grade=4": "/grade-age-table",
            "/grade-birth-year-table?stage=unknown&grade=1": "/grade-birth-year-table",
            "/college-entry-year-calculator?year=": "/college-entry-year-calculator",
            "/college-entry-year-calculator?year=2024~2026": "/college-entry-year-calculator",
        }

        for url, expected_path in invalid_urls.items():
            with self.subTest(url=url):
                response = client.get(url)
                self.assertEqual(302, response.status_code)
                self.assertEqual(expected_path, response.headers["Location"])

    def test_result_queries_reject_ambiguous_or_noncanonical_inputs(self):
        client = app.test_client()
        invalid_urls = {
            "/birth-year-age-table?year=2010&year=2011": "/birth-year-age-table",
            "/school-grade-calculator?year=02010": "/school-grade-calculator",
            "/school-entry-year-table?year=2019&utm_source=test": "/school-entry-year-table",
            "/grade-age-table?stage=middle&grade=1&grade=2": "/grade-age-table",
            "/grade-birth-year-table?stage=middle&grade=1&extra=1": "/grade-birth-year-table",
            "/college-entry-year-calculator?year=2026&year=2025": "/college-entry-year-calculator",
            "/age-gap-calculator?year_a=2000": "/age-gap-calculator",
            "/age-gap-calculator?year_a=2000&year_b=": "/age-gap-calculator",
            "/baby-months-table?months=-1": "/baby-months-table",
            "/annual-age-calculator?birth_year=unknown": "/annual-age-calculator",
            "/age-comparison-table?year=2010&extra=1": "/age-comparison-table",
            "/pet-age-table?pet=dog&years=2": "/pet-age-table",
            "/pet-months-table?pet=bird&months=6&size=small": "/pet-months-table",
            "/birth-year-zodiac-table?year=2024~2026": "/birth-year-zodiac-table",
            "/birthday-dday-calculator?month=2&day=30": "/birthday-dday-calculator",
        }

        for url, expected_path in invalid_urls.items():
            with self.subTest(url=url):
                response = client.get(url, follow_redirects=False)

                self.assertEqual(302, response.status_code)
                self.assertEqual(expected_path, response.headers["Location"])

    def test_valid_result_queries_use_clean_canonical_and_noindex_header(self):
        client = app.test_client()
        cases = {
            "/school-grade-calculator?year=2019": "/school-grade-calculator",
            "/school-entry-year-table?year=2019": "/school-entry-year-table",
            "/grade-age-table?stage=middle&grade=1": "/grade-age-table",
            "/grade-birth-year-table?stage=high&grade=1": "/grade-birth-year-table",
            "/age-gap-calculator?year_a=2000&year_b=2002": "/age-gap-calculator",
            "/baby-months-table?months=12": "/baby-months-table",
            "/annual-age-calculator?birth_year=1992": "/annual-age-calculator",
            "/age-comparison-table?year=1992": "/age-comparison-table",
            "/pet-age-table?pet=dog&years=2&size=small": "/pet-age-table",
            "/pet-months-table?pet=cat&months=6&size=small": "/pet-months-table",
            "/birth-year-zodiac-table?year=1990": "/birth-year-zodiac-table",
            "/birthday-dday-calculator?month=5&day=10": "/birthday-dday-calculator",
        }

        for url, canonical_path in cases.items():
            with self.subTest(url=url):
                response = client.get(url)
                html = response.get_data(as_text=True)

                self.assertEqual(200, response.status_code)
                self.assertEqual("noindex, follow", response.headers.get("X-Robots-Tag"))
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{canonical_path}" />',
                    html,
                )

    def test_indexable_query_allowlist_is_not_marked_noindex(self):
        client = app.test_client()

        for url in (
            "/birth-year-age-table?year=2010",
            "/college-entry-year-calculator?year=2024",
            "/college-entry-year-calculator?year=2025",
            "/college-entry-year-calculator?year=2026",
        ):
            with self.subTest(url=url):
                response = client.get(url)

                self.assertEqual(200, response.status_code)
                self.assertIsNone(response.headers.get("X-Robots-Tag"))

    def test_nonindexable_year_queries_keep_clean_canonical(self):
        client = app.test_client()
        cases = {
            "/school-grade-calculator?year=2015": "/school-grade-calculator",
            "/school-entry-year-table?year=2015": "/school-entry-year-table",
            "/birth-year-age-table?year=2015": "/birth-year-age-table",
            "/college-entry-year-calculator?year=2021": "/college-entry-year-calculator",
            "/college-entry-year-calculator?year=2022": "/college-entry-year-calculator",
            "/college-entry-year-calculator?year=2020": "/college-entry-year-calculator",
        }

        for url, canonical_path in cases.items():
            with self.subTest(url=url):
                response = client.get(url)
                html = response.get_data(as_text=True)
                self.assertEqual(200, response.status_code)
                self.assertIn('<meta name="robots" content="noindex,follow" />', html)
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{canonical_path}" />',
                    html,
                )

    def test_indexable_query_variants_are_self_canonical_and_specific(self):
        client = app.test_client()
        cases = {
            "/birth-year-age-table?year=2010": ("2010년생", "몇살"),
            "/college-entry-year-calculator?year=2024": ("24학번", "2024학번"),
            "/college-entry-year-calculator?year=2025": ("25학번", "2025학번"),
            "/college-entry-year-calculator?year=2026": ("26학번", "2026학번"),
        }

        for url, phrases in cases.items():
            with self.subTest(url=url):
                response = client.get(url)
                html = response.get_data(as_text=True)
                self.assertEqual(200, response.status_code)
                self.assertNotIn('<meta name="robots" content="noindex,follow" />', html)
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{url.replace("&", "&amp;")}" />',
                    html,
                )
                for phrase in phrases:
                    self.assertIn(phrase, html)

    def test_grade_result_queries_are_noindex_with_clean_canonicals(self):
        client = app.test_client()
        cases = {
            "/grade-age-table?stage=middle&grade=1": "/grade-age-table",
            "/grade-birth-year-table?stage=high&grade=1": "/grade-birth-year-table",
        }

        for url, canonical_path in cases.items():
            with self.subTest(url=url):
                response = client.get(url)
                html = response.get_data(as_text=True)

                self.assertEqual(200, response.status_code)
                self.assertIn('<meta name="robots" content="noindex,follow" />', html)
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{canonical_path}" />',
                    html,
                )

    def test_query_results_have_crawlable_navigation_paths(self):
        client = app.test_client()
        grade_variants = [
            *(f"stage=elementary&amp;grade={grade}" for grade in range(1, 7)),
            *(f"stage=middle&amp;grade={grade}" for grade in range(1, 4)),
            *(f"stage=high&amp;grade={grade}" for grade in range(1, 4)),
        ]

        for base_path in ("/grade-age-table", "/grade-birth-year-table"):
            html = client.get(base_path).get_data(as_text=True)
            for query in grade_variants:
                with self.subTest(base_path=base_path, query=query):
                    self.assertIn(f'href="{base_path}?{query}"', html)

        birth_year_html = client.get("/birth-year-age-table").get_data(as_text=True)
        self.assertIn('href="/birth-year-age-table?year=2010"', birth_year_html)

        college_html = client.get("/college-entry-year-calculator").get_data(as_text=True)
        for year in (2026, 2025, 2024, 2022, 2020):
            with self.subTest(year=year):
                self.assertIn(f'href="/college-entry-year-calculator?year={year}"', college_html)

    def test_priority_pages_use_search_intent_metadata(self):
        client = app.test_client()
        expected = {
            "/grade-birth-year-table": "학년별 출생연도표 | 중1·고1은 몇 년생? | AgeCalc",
            "/grade-age-table": "학년별 나이표 | 중1·중3·고1·고3은 몇 살? | AgeCalc",
            "/school-grade-calculator": "학년 계산기 | 출생연도별 현재 학년 확인 | AgeCalc",
            "/school-entry-year-table": "입학년도 계산기 | 출생연도별 초·중·고 입학년도 | AgeCalc",
            "/birth-year-age-table": "몇년생 몇살? 출생연도별 만나이·연나이 표 | AgeCalc",
            "/age": "만나이 계산기 | 생년월일·음력 생일로 현재 나이 계산 | AgeCalc",
            "/annual-age-calculator": "연나이 계산기 | 출생연도만으로 올해 연나이 확인 | AgeCalc",
            "/100-day-calculator": "100일 계산기 | 시작일 포함 100일째·기념일 날짜 계산 | AgeCalc",
            "/college-entry-year-calculator": "학번 계산기 | 몇 학번·학번 나이·몇년생 확인 | AgeCalc",
        }

        for path, title in expected.items():
            with self.subTest(path=path):
                html = client.get(path).get_data(as_text=True)
                self.assertIn(f"<title>{title}</title>", html)

    def test_age_page_clarifies_man_age_and_lunar_input_intent(self):
        html = app.test_client().get("/age").get_data(as_text=True)

        self.assertIn(
            '<meta name="description" content="양력 또는 평달 기준 음력 생년월일 8자리를 입력해 오늘 기준 만나이를 확인하세요. 생일 전후 계산법과 윤달·2월 29일 예외도 안내합니다." />',
            html,
        )
        self.assertIn("오늘 연도 - 출생연도", html)
        self.assertIn("생일 전이면 1을 뺍니다", html)
        self.assertIn("윤달 선택은 지원하지 않으며 평달로 계산합니다", html)
        self.assertIn("올해 돌아오는 음력 생일의 양력 날짜를 찾는 기능은 아닙니다", html)
        self.assertIn("음력 생일의 만나이 계산 기준", html)
        self.assertNotIn("완벽 지원", html)

        direct_answer = html.index('aria-label="만나이 바로 답변"')
        for affiliate_marker in (
            "info-coupang-promotions",
            "coupang-mobile-banner",
            "home-coupang-rail-left",
        ):
            if affiliate_marker in html:
                self.assertLess(direct_answer, html.index(affiliate_marker))

    def test_age_page_examples_follow_the_rendered_reference_date(self):
        with mock.patch.object(app_module, "_current_local_date", return_value=date(2026, 10, 1)):
            before_birthday = app.test_client().get("/age").get_data(as_text=True)
        with mock.patch.object(app_module, "_current_local_date", return_value=date(2026, 10, 2)):
            on_birthday = app.test_client().get("/age").get_data(as_text=True)

        self.assertIn("2026-10-01 기준 33세", before_birthday)
        self.assertIn("2026년 기준 34세", before_birthday)
        self.assertIn("2026-10-02 기준 34세", on_birthday)
        self.assertIn("2026년 기준 34세", on_birthday)

    def test_school_page_group_keeps_one_owner_for_each_search_direction(self):
        client = app.test_client()

        grade_age_html = client.get(
            "/grade-age-table?stage=middle&grade=1"
        ).get_data(as_text=True)
        self.assertIn(
            "<title>중1 나이 | 연나이·만나이 범위 | AgeCalc</title>",
            grade_age_html,
        )
        self.assertNotIn("<title>중1 나이 | 몇 살·몇 년생?", grade_age_html)

        grade_birth_html = client.get("/grade-birth-year-table").get_data(as_text=True)
        for phrase in ("중1은 보통 2013년생", "고1은 보통 2010년생", "고3은 보통 2008년생"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, grade_birth_html)

        school_grade_html = client.get("/school-grade-calculator").get_data(as_text=True)
        self.assertIn("만 13세라는 정보만으로 현재 학년을 확정할 수 있나요?", school_grade_html)
        self.assertIn("이 계산기는 생년월일이나 현재 나이가 아닌 출생연도를 입력받습니다", school_grade_html)

    def test_school_table_base_pages_render_current_year_snippet_answers(self):
        client = app.test_client()

        with mock.patch.object(
            app_module, "_current_local_date", return_value=date(2026, 8, 13)
        ):
            grade_birth_html = client.get("/grade-birth-year-table").get_data(as_text=True)
            grade_age_html = client.get("/grade-age-table").get_data(as_text=True)

        self.assertIn(
            '<meta name="description" content="2026학년도 중1은 2013년생, 고1은 2010년생, 고3은 2008년생입니다. 학년별 일반 출생연도와 빠른년생·입학유예 예외를 확인하세요." />',
            grade_birth_html,
        )
        self.assertIn(
            "2026학년도 중1은 2013년생, 고1은 2010년생, 고3은 2008년생입니다",
            grade_birth_html,
        )
        self.assertIn(
            '<meta name="description" content="2026학년도 중1 13세, 중3 15세, 고1 16세, 고3 18세의 연나이와 생일 전후 만나이 범위를 확인하는 학년별 나이표입니다." />',
            grade_age_html,
        )
        self.assertIn(
            "2026학년도 중1은 연나이 13세, 중3은 15세, 고1은 16세, 고3은 18세입니다",
            grade_age_html,
        )
        self.assertIn(
            "중1은 만 12~13세, 중3은 만 14~15세, 고1은 만 15~16세, 고3은 만 17~18세",
            grade_age_html,
        )

        self.assertIn(
            "<title>학년별 출생연도표 | 중1·고1은 몇 년생? | AgeCalc</title>",
            grade_birth_html,
        )
        self.assertIn("<h1>학년별 출생연도표</h1>", grade_birth_html)
        self.assertIn(
            "<title>학년별 나이표 | 중1·중3·고1·고3은 몇 살? | AgeCalc</title>",
            grade_age_html,
        )
        self.assertIn("<h1>학년별 나이표</h1>", grade_age_html)

    def test_school_page_group_uses_directional_related_tool_anchors(self):
        client = app.test_client()
        expectations = {
            "/grade-birth-year-table": (
                ('href="/grade-age-table"', "학년을 알 때 나이 범위 확인"),
                ('href="/school-grade-calculator"', "출생연도로 현재 학년 확인"),
                ('href="/school-entry-year-table"', "출생연도로 입학년도 확인"),
            ),
            "/grade-age-table": (
                ('href="/grade-birth-year-table"', "학년을 알 때 출생연도 확인"),
                ('href="/school-grade-calculator"', "출생연도로 현재 학년 확인"),
                ('href="/school-entry-year-table"', "출생연도로 입학년도 확인"),
            ),
            "/school-grade-calculator": (
                ('href="/grade-age-table"', "학년을 알 때 나이 범위 확인"),
                ('href="/grade-birth-year-table"', "학년을 알 때 출생연도 확인"),
                ('href="/school-entry-year-table"', "출생연도로 입학년도 확인"),
            ),
            "/school-entry-year-table": (
                ('href="/school-grade-calculator"', "출생연도로 현재 학년 확인"),
                ('href="/grade-birth-year-table"', "학년을 알 때 출생연도 확인"),
            ),
        }

        for path, links in expectations.items():
            html = client.get(path).get_data(as_text=True)
            for href, label in links:
                with self.subTest(path=path, label=label):
                    self.assertIn(f"{href}>{label}</a>", html)

    def test_sitemap_contains_only_clean_base_urls(self):
        client = app.test_client()
        locations = _sitemap_leaf_locations(client)

        self.assertTrue(locations)
        self.assertTrue(all("?" not in location and "#" not in location for location in locations))
        for path in (
            "/birth-year-age-table",
            "/grade-age-table",
            "/grade-birth-year-table",
            "/college-entry-year-calculator",
        ):
            self.assertIn(f"https://agecalc.cloud{path}", locations)

    def test_unknown_adsense_review_mode_value_fails_closed(self):
        with self.assertWarns(RuntimeWarning):
            parsed = app_module._parse_adsense_review_mode("typo")

        self.assertTrue(parsed)
        self.assertFalse(app_module._parse_adsense_review_mode("off"))

    def test_adsense_review_mode_is_enabled_by_default(self):
        self.assertTrue(getattr(app_module, "ADSENSE_REVIEW_MODE", False))

    def test_adsense_review_mode_overrides_affiliate_and_blog_flags(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True), mock.patch.object(
            app_module,
            "BLOG_PUBLIC_INDEXING_ENABLED",
            True,
        ), mock.patch.object(app_module, "_published_blog_count", return_value=5):
            home_response = client.get("/")
            blog_response = client.get("/blog")

        home_html = home_response.get_data(as_text=True)
        blog_html = blog_response.get_data(as_text=True)
        self.assertNotIn("link.coupang.com", home_html)
        self.assertNotIn("ads-partners.coupang.com", home_html)
        self.assertNotIn('rel="sponsored', home_html)
        self.assertNotIn('href="/blog"', home_html)
        self.assertEqual(blog_response.headers.get("X-Robots-Tag"), "noindex, nofollow")
        self.assertIn('<meta name="robots" content="noindex,nofollow" />', blog_html)
        self.assertNotIn("google-adsense-account", blog_html)
        self.assertIn('"adsense_client": ""', blog_html)

    def test_adsense_review_mode_keeps_hubs_accessible_but_not_indexable(self):
        client = app.test_client()

        for hub in HUB_PAGES:
            with self.subTest(key=hub["key"]):
                response = client.get(hub["path"])
                html = response.get_data(as_text=True)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get("X-Robots-Tag"), "noindex, follow")
                self.assertIn('<meta name="robots" content="noindex,follow" />', html)
                self.assertNotIn("google-adsense-account", html)
                self.assertNotIn("pagead/js/adsbygoogle.js", html)
                self.assertIn('"adsense_client": ""', html)

        home_html = client.get("/").get_data(as_text=True)
        for path in ("/age-tools/", "/family/", "/education/", "/anniversary/"):
            self.assertIn(f'href="{path}"', home_html)

    def test_adsense_review_mode_exposes_only_46_sitemap_urls(self):
        client = app.test_client()
        root_xml = client.get("/sitemap.xml").get_data(as_text=True)
        locations = _sitemap_leaf_locations(client)
        joined_locations = "\n".join(locations)

        self.assertEqual(46, len(locations))
        self.assertEqual(46, len(set(locations)))
        self.assertNotIn("/blog", joined_locations)
        for key in (
            "age",
            "family",
            "education",
            "anniversary",
            "retirement",
            "health",
            "pets",
            "generations",
        ):
            self.assertNotIn(f"https://agecalc.cloud/{key}/", locations)

        for empty_group in ("retirement", "health", "generations"):
            self.assertNotIn(f"/sitemaps/{empty_group}.xml", root_xml)

    def test_adsense_review_mode_removes_coupang_from_csp(self):
        csp = app.test_client().get("/").headers.get("Content-Security-Policy", "")

        self.assertNotIn("coupang.com", csp)
        self.assertNotIn("coupangcdn.com", csp)

    def test_about_page_is_public(self):
        client = app.test_client()
        response = client.get("/about")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("콘텐츠 운영 원칙", html)
        self.assertIn("편집 기준", html)
        self.assertNotIn("Editorial Policy", html)
        for phrase in ["설명형 콘텐츠", "설명형 글만 공개합니다."]:
            self.assertNotIn(phrase, html)

    def test_contact_page_is_public(self):
        client = app.test_client()
        response = client.get("/contact")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("문의 및 운영자 안내", html)
        self.assertIn("AgeCalc 편집팀", html)
        self.assertIn("ldg6153@gmail.com", html)
        self.assertIn("문의 가능한 내용", html)

    def test_references_page_is_public(self):
        client = app.test_client()
        response = client.get("/references")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("계산 기준과 참고 자료", html)
        self.assertIn("만나이 계산기", html)
        self.assertIn("아이 개월 수 계산기", html)
        self.assertIn("강아지 나이 계산기", html)
        self.assertIn("고양이 나이 계산기", html)

    def test_age_page_uses_current_year_in_age_comparison_examples(self):
        client = app.test_client()
        html = client.get("/age").get_data(as_text=True)
        current = _current_local_date()
        current_year = current.year
        man_age = current_year - 1992 - ((current.month, current.day) < (10, 2))

        self.assertIn(f"{current.isoformat()} 기준 {man_age}세", html)
        self.assertIn(f"{current_year}년 기준 {current_year - 1992}세", html)
        self.assertNotIn(f"{current_year}-10-07 기준 33세", html)

    def test_birth_year_age_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/birth-year-age-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("출생년도별 나이표", html)
        self.assertIn("몇년생 몇살", html)
        self.assertIn("출생년도를 선택하세요", html)
        self.assertIn("만나이 범위", html)
        self.assertIn("띠", html)
        self.assertIn("세대명", html)

    def test_birth_year_age_table_highlights_selected_year(self):
        client = app.test_client()
        response = client.get("/birth-year-age-table?year=1990")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("1990년생", html)
        self.assertIn("선택한 연도", html)
        self.assertIn("1990년생 나이 안내", html)

    def test_school_grade_calculator_page_is_public(self):
        client = app.test_client()
        response = client.get("/school-grade-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("학년 계산기", html)
        self.assertIn("출생년도를 선택해 현재 몇 학년인지 계산", html)
        self.assertIn("현재 학년", html)
        self.assertIn("초등학교 입학", html)
        self.assertIn("중학교 입학", html)
        self.assertIn("현재 몇 학년인지", html)
        self.assertIn("입학 시점만 확인하려면 입학년도 계산표를 보세요.", html)

    def test_school_grade_calculator_highlights_selected_year(self):
        client = app.test_client()
        response = client.get("/school-grade-calculator?year=2019")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("2019년생", html)
        self.assertIn("선택한 출생년도", html)
        self.assertIn("학년 안내", html)

    def test_school_grade_calculator_includes_adult_birth_year_options(self):
        client = app.test_client()
        response = client.get("/school-grade-calculator?year=1990")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<option value="1990" selected>1990년생</option>', html)
        self.assertIn("고등학교 졸업 이후", html)

    def test_school_entry_year_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/school-entry-year-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("입학년도 계산표", html)
        self.assertIn("초등학교 입학년도", html)
        self.assertIn("중학교 입학년도", html)
        self.assertIn("고등학교 입학년도", html)
        self.assertIn("입학년도 계산기", html)
        self.assertIn("현재 학년이 아니라 입학 시점을 빠르게 확인할 때 사용합니다.", html)

    def test_school_entry_year_table_leads_with_current_entry_year_answers(self):
        client = app.test_client()
        with mock.patch.object(app_module, "_current_local_date", return_value=date(2026, 8, 13)):
            html = client.get("/school-entry-year-table").get_data(as_text=True)

        self.assertIn("2026학년도 초등학교 입학생은 보통 2019년생", html)
        self.assertIn("중학교는 2013년생", html)
        self.assertIn("고등학교는 2010년생", html)
        self.assertIn("출생연도 + 7·13·16", html)
        self.assertIn("정확한 입학식 날짜는 학교 일정을 확인하세요", html)

        direct_answer = html.index('aria-label="입학년도 바로 답변"')
        for affiliate_marker in (
            "info-coupang-promotions",
            "coupang-mobile-banner",
            "home-coupang-rail-left",
        ):
            if affiliate_marker in html:
                self.assertLess(direct_answer, html.index(affiliate_marker))

    def test_school_entry_year_table_uses_previous_school_year_in_january(self):
        with mock.patch.object(app_module, "_current_local_date", return_value=date(2026, 1, 15)):
            html = app.test_client().get("/school-entry-year-table").get_data(as_text=True)

        self.assertIn("2025학년도 초등학교 입학생은 보통 2018년생", html)
        self.assertIn("중학교는 2012년생", html)
        self.assertIn("고등학교는 2009년생", html)

    def test_school_entry_year_selected_result_is_an_entry_year_answer(self):
        html = app.test_client().get(
            "/school-entry-year-table?year=2018"
        ).get_data(as_text=True)

        self.assertIn(
            "2018년생은 초등학교 2025학년도, 중학교 2031학년도, 고등학교 2034학년도 입학",
            html,
        )
        self.assertIn("현재 학년은 학년 계산기에서 따로 확인하세요", html)

    def test_school_entry_year_faq_matches_visible_copy(self):
        html = app.test_client().get("/school-entry-year-table").get_data(as_text=True)
        schemas, visible_text = _parse_page_markup(html)
        visible_text = re.sub(r"\s+", " ", visible_text)
        faq_pages = [schema for schema in schemas if schema.get("@type") == "FAQPage"]

        self.assertEqual(1, len(faq_pages))
        for question in faq_pages[0]["mainEntity"]:
            self.assertIn(re.sub(r"\s+", " ", question["name"]), visible_text)
            self.assertIn(
                re.sub(r"\s+", " ", question["acceptedAnswer"]["text"]),
                visible_text,
            )

    def test_school_entry_year_table_highlights_selected_year(self):
        client = app.test_client()
        response = client.get("/school-entry-year-table?year=2018")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 출생년도", html)
        self.assertIn("2018년생", html)
        self.assertIn("2025학년도", html)

    def test_school_entry_year_table_includes_adult_birth_year_options(self):
        client = app.test_client()
        response = client.get("/school-entry-year-table?year=1990")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('<option value="1990" selected>1990년생</option>', html)
        self.assertIn("초등학교 입학은 1997학년도", html)

    def test_age_gap_calculator_page_is_public(self):
        client = app.test_client()
        response = client.get("/age-gap-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("나이 차이 계산기", html)
        self.assertIn("두 출생년도를 선택하면", html)
        self.assertIn("연도 차이", html)
        self.assertIn("만나이 차이 범위", html)

    def test_age_gap_calculator_highlights_selected_pair(self):
        client = app.test_client()
        response = client.get("/age-gap-calculator?year_a=1990&year_b=1995")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("1990년생과 1995년생", html)
        self.assertIn("선택한 비교", html)
        self.assertIn("5년 차이", html)

    def test_hundred_day_calculator_page_is_public(self):
        client = app.test_client()
        response = client.get("/100-day-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("100일 계산기", html)
        self.assertIn("시작일을 1일째로 계산", html)
        self.assertIn("100일째 날짜", html)
        self.assertIn("오늘 기준 상태", html)

    def test_hundred_day_calculator_redirects_legacy_date_query(self):
        client = app.test_client()
        response = client.get("/100-day-calculator?year=2026&month=1&day=1")

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.headers["Location"], "/100-day-calculator")

    def test_hundred_day_calculator_leads_with_today_answer_and_distinguishes_after(self):
        with mock.patch.object(app_module, "_current_local_date", return_value=date(2026, 8, 13)):
            html = app.test_client().get("/100-day-calculator").get_data(as_text=True)

        self.assertIn("오늘(2026.08.13)을 1일째로 세면 100일째는 2026.11.20입니다", html)
        self.assertIn("100일째는 시작일 +99일", html)
        self.assertIn("100일 후는 시작일 +100일", html)
        direct_answer = html.index('aria-label="100일 계산 바로 답변"')
        for affiliate_marker in ("info-coupang-promotions", "home-coupang-rail-left"):
            if affiliate_marker in html:
                self.assertLess(direct_answer, html.index(affiliate_marker))

    def test_anniversary_calculator_uses_distinct_metadata_and_rejects_queries(self):
        client = app.test_client()
        response = client.get("/d-day")
        html = response.get_data(as_text=True)

        self.assertEqual(200, response.status_code)
        self.assertIn(
            "<title>기념일 계산기 | D-day·남은 일수 계산 | AgeCalc</title>",
            html,
        )
        self.assertIn(
            "목표 날짜를 입력해 오늘 기준 D-day와 지난 날짜의 경과 일수를 계산합니다.",
            html,
        )
        self.assertIn("<h1>기념일 계산기</h1>", html)
        javascript = Path("static/js/d-day.js").read_text(encoding="utf-8")
        self.assertNotIn("Elapsed Date", javascript)
        self.assertNotIn("Countdown", javascript)
        self.assertIn('"경과 일수"', javascript)
        self.assertIn('"남은 일수"', javascript)
        self.assertEqual(302, client.get("/d-day?year=2026").status_code)
        self.assertEqual("/d-day", client.get("/d-day?year=2026").headers["Location"])

        direct_answer = html.index('aria-label="기념일 D-day 바로 답변"')
        for affiliate_marker in ("info-coupang-promotions", "home-coupang-rail-left"):
            if affiliate_marker in html:
                self.assertLess(direct_answer, html.index(affiliate_marker))

    def test_baby_months_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/baby-months-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("개월수 계산표", html)
        self.assertIn("생후 개월 수", html)
        self.assertIn("월령별 빠른 안내", html)
        self.assertIn("12개월", html)
        self.assertIn("정확한 현재 개월수 계산은 아이 개월수 계산기에서 확인합니다.", html)

    def test_baby_months_table_highlights_selected_months(self):
        client = app.test_client()
        response = client.get("/baby-months-table?months=12")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 월령", html)
        self.assertIn("12개월", html)
        self.assertIn("1년 0개월", html)

    def test_baby_months_page_uses_months_query_variants(self):
        client = app.test_client()
        response = client.get("/baby-months")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("아이 개월수 계산기", html)
        self.assertIn("아이 개월수", html)
        self.assertIn("아기 월령", html)
        self.assertIn("개월수와 월령은 같은 뜻인가요?", html)
        self.assertIn('id="baby-birth-input"', html)
        self.assertIn('maxlength="8"', html)
        self.assertNotIn('id="baby-year"', html)
        self.assertNotIn('id="baby-month"', html)
        self.assertNotIn('id="baby-day"', html)

    def test_baby_months_page_connects_month_day_and_school_intents(self):
        client = app.test_client()
        response = client.get("/baby-months")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("생후 100일과 3개월은 같은 날인가요?", html)
        self.assertIn("아이 개월 수로 현재 학년을 알 수 있나요?", html)
        self.assertIn('href="/baby-months-table"', html)
        self.assertIn('href="/100-day-calculator"', html)
        self.assertIn('href="/school-grade-calculator"', html)
        self.assertIn("개월수를 연·개월 표현으로 확인", html)
        self.assertIn("출생일 포함 100일째 날짜 계산", html)
        self.assertIn("생년월일로 현재 학년 확인", html)

    def test_baby_months_query_urls_redirect_to_clean_canonical(self):
        client = app.test_client()

        for url in (
            "/baby-months?birth=20250101",
            "/baby-months?utm_source=test",
            "/baby-months?birth=20250101&birth=20250202",
        ):
            with self.subTest(url=url):
                response = client.get(url, follow_redirects=False)

                self.assertEqual(response.status_code, 302)
                self.assertEqual("/baby-months", response.headers["Location"])

    def test_college_entry_year_calculator_targets_top_queries(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("26학번 몇년생", html)
        self.assertIn("22학번 나이", html)
        self.assertIn("09학번 몇살", html)
        self.assertIn("26학번 나이", html)

        for cohort in (18, 19, 20, 21, 22, 23, 26, 27):
            with self.subTest(cohort=cohort):
                self.assertIn(f"{cohort}학번 나이·몇년생", html)

    def test_indexable_college_cohorts_render_unique_search_metadata(self):
        client = app.test_client()
        cases = {
            2024: ("24학번", "2005년생", "21세", "만 20~21세"),
            2025: ("25학번", "2006년생", "20세", "만 19~20세"),
            2026: ("26학번", "2007년생", "19세", "만 18~19세"),
        }

        for year, (cohort, birth_year, annual_age, man_age) in cases.items():
            with self.subTest(year=year):
                response = client.get(f"/college-entry-year-calculator?year={year}")
                html = response.get_data(as_text=True)

                self.assertEqual(200, response.status_code)
                self.assertIn(f"<title>{cohort} 나이·몇년생 | 학번 계산기 | AgeCalc</title>", html)
                self.assertIn(f"<h1>{cohort} 나이·몇년생 확인</h1>", html)
                self.assertIn(
                    f"{cohort}은 일반적인 진학 기준으로 {birth_year}이며, 2026년 기준 연나이 {annual_age}·{man_age}입니다.",
                    html,
                )
                self.assertIn(
                    f'<meta name="description" content="{cohort}은 일반적인 진학 기준으로 {birth_year}이며, 2026년 기준 연나이 {annual_age}·{man_age}입니다. 재수·편입·학교별 학번 차이도 안내합니다."',
                    html,
                )

    def test_college_cohort_result_links_to_distinct_followup_intents(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator?year=2026")
        html = response.get_data(as_text=True)

        self.assertEqual(200, response.status_code)
        self.assertIn('href="/school-entry-year-table?year=2007"', html)
        self.assertIn("2007년생 초·중·고 입학연도 확인", html)
        self.assertIn('href="/birth-year-age-table?year=2007"', html)
        self.assertIn("2007년생 현재 나이 확인", html)

    def test_past_college_cohort_does_not_claim_enrollment_year(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator?year=2022")
        html = response.get_data(as_text=True)

        self.assertEqual(200, response.status_code)
        self.assertIn("2022년 입학 기준이며 2026년은 입학연도보다 4년 뒤입니다", html)
        self.assertNotIn("입학 후 4년차", html)

    def test_annual_age_calculator_page_is_public(self):
        client = app.test_client()
        response = client.get("/annual-age-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("연나이 계산기", html)
        self.assertIn("생일과 관계없이", html)
        self.assertIn("올해 연나이", html)
        self.assertIn("만나이와의 차이", html)

    def test_annual_age_calculator_hero_matches_birth_year_only_input(self):
        client = app.test_client()

        with mock.patch.object(
            app_module, "_current_local_date", return_value=date(2026, 8, 13)
        ):
            html = client.get("/annual-age-calculator").get_data(as_text=True)

        hero_html = re.search(r'<section class="hero-band">.*?</section>', html, re.S).group(0)
        self.assertIn("출생연도만 입력하면", hero_html)
        self.assertIn("2026년에서 출생연도를 빼", hero_html)
        self.assertIn(">출생연도 입력</a>", hero_html)
        self.assertNotIn("생년월일을 입력하면", hero_html)
        self.assertEqual(
            ["birth_year"],
            re.findall(r'<(?:input|select)[^>]+name="([^"]+)"', html),
        )

        self.assertIn(
            "<title>연나이 계산기 | 출생연도만으로 올해 연나이 확인 | AgeCalc</title>",
            html,
        )
        self.assertIn("<h1>연나이 계산기</h1>", html)
        self.assertIn(
            '<meta name="description" content="출생연도만 입력해 올해 연나이를 계산하고, 생일에 따라 달라지는 만나이와의 차이를 확인하세요." />',
            html,
        )
        for path in ("/age", "/birth-year-age-table", "/age-comparison-table"):
            self.assertIn(f'href="{path}"', html)

    def test_annual_age_calculator_highlights_selected_birth_year(self):
        client = app.test_client()
        response = client.get("/annual-age-calculator?birth_year=1992")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 출생연도", html)
        self.assertIn("1992년생", html)
        self.assertIn("34세", html)

    def test_annual_age_calculator_redirects_legacy_queries(self):
        client = app.test_client()

        for path in (
            "/annual-age-calculator?birth_date=921002",
            "/annual-age-calculator?year=&month=&day=",
        ):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(response.headers["Location"], "/annual-age-calculator")

    def test_age_comparison_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/age-comparison-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("만나이·연나이 비교표", html)
        self.assertIn("왜 다르게 보이나요?", html)
        self.assertIn("만나이", html)
        self.assertIn("연나이", html)

    def test_age_comparison_table_highlights_selected_year(self):
        client = app.test_client()
        response = client.get("/age-comparison-table?year=1992")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 출생년도", html)
        self.assertIn("1992년생", html)
        self.assertIn("34세", html)
        self.assertIn("만 33~34세", html)

    def test_grade_age_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/grade-age-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("학년 기준 나이표", html)
        self.assertIn("초등학교 1학년", html)
        self.assertIn("중학교 1학년", html)
        self.assertIn("고등학교 1학년", html)

    def test_grade_age_table_highlights_selected_grade(self):
        client = app.test_client()
        response = client.get("/grade-age-table?stage=elementary&grade=1")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 학년", html)
        self.assertIn("초등학교 1학년", html)
        self.assertIn("2019년생", html)
        self.assertIn("만 6~7세", html)

    def test_pet_age_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/pet-age-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("반려동물 나이표", html)
        self.assertIn("강아지 나이표", html)
        self.assertIn("고양이 나이표", html)
        self.assertIn("소형견", html)

    def test_pet_age_table_highlights_selected_pet_age(self):
        client = app.test_client()
        response = client.get("/pet-age-table?pet=dog&years=2&size=small")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 반려동물", html)
        self.assertIn("강아지 2살", html)
        self.assertIn("24세", html)

    def test_korean_age_guide_page_is_public(self):
        client = app.test_client()
        response = client.get("/korean-age-guide")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("한국나이 폐지 이후 기준 정리", html)
        self.assertIn("2023년 6월 28일", html)
        self.assertIn("민법 제158조", html)
        self.assertIn("행정기본법", html)
        self.assertIn("연 나이", html)

    def test_pet_months_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/pet-months-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("반려동물 월령표", html)
        self.assertIn("강아지 월령표", html)
        self.assertIn("고양이 월령표", html)
        self.assertIn("개월 기준", html)

    def test_pet_months_table_highlights_selected_months(self):
        client = app.test_client()
        response = client.get("/pet-months-table?pet=dog&months=6&size=small")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 월령", html)
        self.assertIn("강아지 6개월", html)
        self.assertIn("소형견", html)
        self.assertIn("8세", html)

    def test_grade_birth_year_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/grade-birth-year-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("학년별 출생연도표", html)
        self.assertIn("초1은 몇 년생", html)
        self.assertIn("중1은 몇 년생", html)
        self.assertIn("고1은 몇 년생", html)

    def test_grade_birth_year_table_highlights_selected_grade(self):
        client = app.test_client()
        response = client.get("/grade-birth-year-table?stage=high&grade=3")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 학년", html)
        self.assertIn("고등학교 3학년", html)
        self.assertIn("2008년생", html)

    def test_birth_year_zodiac_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/birth-year-zodiac-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("<title>연도별 띠표 | 출생연도로 무슨 띠인지 확인 | AgeCalc</title>", html)
        self.assertIn('<h1>연도별 띠표</h1>', html)
        self.assertIn("같은 띠의 12년 주기", html)
        self.assertIn("12간지", html)
        self.assertIn("띠", html)
        self.assertIn("말띠", html)
        self.assertIn("1월·2월생은 어느 띠인가요?", html)
        self.assertNotIn('<th scope="col">연나이</th>', html)
        self.assertNotIn('<th scope="col">만나이 범위</th>', html)

    def test_birth_year_zodiac_table_highlights_selected_year(self):
        client = app.test_client()
        response = client.get("/birth-year-zodiac-table?year=1990")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 출생연도", html)
        self.assertIn("1990년생", html)
        self.assertIn("말띠", html)
        self.assertIn("1978년", html)
        self.assertIn("2002년", html)
        self.assertIn("출생연도만으로는 경계일의 띠를 확정할 수 없습니다", html)

    def test_birth_year_age_table_answers_age_to_year_and_selected_year_above_the_form(self):
        client = app.test_client()

        with mock.patch.object(
            app_module, "_current_local_date", return_value=date(2026, 8, 13)
        ):
            base_html = client.get("/birth-year-age-table").get_data(as_text=True)
            selected_html = client.get(
                "/birth-year-age-table?year=2010"
            ).get_data(as_text=True)

        self.assertIn("2026년 20살은 연나이 기준 2006년생입니다", base_html)
        self.assertIn(
            "만 20세는 생일과 기준일에 따라 2005년생 또는 2006년생",
            base_html,
        )
        self.assertIn(
            "2010년생은 2026년 연나이 16세이며, 만나이는 만 15~16세입니다",
            selected_html,
        )
        self.assertLess(
            base_html.index('class="section-shell direct-answer"'),
            base_html.index('id="birth-year-search"'),
        )
        self.assertLess(
            selected_html.index('class="section-shell direct-answer"'),
            selected_html.index('id="birth-year-search"'),
        )

        self.assertIn(
            "<title>몇년생 몇살? 출생연도별 만나이·연나이 표 | AgeCalc</title>",
            base_html,
        )
        self.assertIn("<h1>몇년생 몇살? 출생연도별 나이표</h1>", base_html)
        self.assertIn(
            '<meta name="description" content="몇년생 몇살인지 궁금할 때 출생년도를 선택해 현재 연나이와 만나이 범위, 띠, 세대명을 한눈에 보는 나이표입니다." />',
            base_html,
        )

    def test_college_entry_year_calculator_page_is_public(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("대학 학번 나이 계산기", html)
        self.assertIn("26학번 나이", html)
        self.assertIn("26학번 몇년생", html)
        self.assertIn("학번별 나이표", html)
        self.assertIn("보통 출생연도", html)

    def test_college_entry_year_calculator_answers_class_year_queries(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator?year=2026")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("26학번 몇년생", html)
        self.assertIn("26학번은 보통 2007년생", html)
        self.assertIn("26학번 나이", html)
        self.assertIn("학번은 입학연도와 같은 뜻인가요?", html)
        self.assertIn("22학번 나이는 몇 살인가요?", html)

    def test_college_entry_year_calculator_highlights_selected_entry_year(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator?year=2025")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 학번", html)
        self.assertIn("25학번", html)
        self.assertIn("2006년생", html)
        self.assertIn("만 19~20세", html)

    def test_birthday_dday_calculator_page_is_public(self):
        client = app.test_client()
        response = client.get("/birthday-dday-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("생일 D-day 계산기", html)
        self.assertIn("생일까지 며칠 남았는지", html)
        self.assertIn("다음 생일", html)
        self.assertIn("생일 선택", html)
        self.assertIn("생일 D-day 자주 묻는 질문", html)

    def test_birthday_dday_calculator_highlights_selected_birthday(self):
        client = app.test_client()
        response = client.get("/birthday-dday-calculator?month=5&day=10")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)

        today = _current_local_date()
        candidate_year = today.year
        if (today.month, today.day) > (5, 10):
            candidate_year += 1
        expected_date = datetime(candidate_year, 5, 10).strftime("%Y.%m.%d")

        self.assertIn("선택한 생일", html)
        self.assertIn("5월 10일", html)
        self.assertIn(expected_date, html)
        self.assertIn("다음 생일", html)

    def test_birthday_dday_selected_result_leads_with_direct_answer(self):
        with mock.patch.object(app_module, "_current_local_date", return_value=date(2026, 8, 13)):
            html = app.test_client().get(
                "/birthday-dday-calculator?month=12&day=25"
            ).get_data(as_text=True)

        self.assertIn("12월 25일의 다음 생일은 2026.12.25입니다", html)
        self.assertIn("다음 생일까지 134일 남았습니다", html)
        direct_answer = html.index('aria-label="생일 D-day 바로 답변"')
        for affiliate_marker in ("info-coupang-promotions", "home-coupang-rail-left"):
            if affiliate_marker in html:
                self.assertLess(direct_answer, html.index(affiliate_marker))

    def test_age_page_renders_feedback_widget(self):
        client = app.test_client()
        response = client.get("/age")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("이 페이지가 도움이 됐나요?", html)
        self.assertIn("도움됨", html)
        self.assertIn("아쉬움", html)
        self.assertIn('data-page-feedback="/age"', html)
        self.assertIn("static/js/page-feedback.js", html)
        self.assertLess(html.index("이 페이지가 도움이 됐나요?"), html.index('<footer class="footer">'))

    def test_page_feedback_api_records_age_feedback(self):
        class FakeSession:
            def __init__(self):
                self.added = None
                self.committed = False
                self.closed = False

            def add(self, obj):
                self.added = obj

            def commit(self):
                self.committed = True

            def close(self):
                self.closed = True

        fake_session = FakeSession()

        with mock.patch.object(app_module, "SessionLocal", return_value=fake_session):
            response = app.test_client().post(
                "/page-feedback",
                json={"page_path": "/age", "vote": "helpful"},
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual({"ok": True}, response.get_json())
        self.assertIsInstance(fake_session.added, PageFeedback)
        self.assertEqual("/age", fake_session.added.page_path)
        self.assertEqual("helpful", fake_session.added.vote)
        self.assertTrue(fake_session.committed)
        self.assertTrue(fake_session.closed)

    def test_page_feedback_api_rejects_invalid_payloads(self):
        client = app.test_client()

        for payload in [
            {},
            {"page_path": "/age", "vote": "spam"},
            {"page_path": "/dog", "vote": "helpful"},
        ]:
            with self.subTest(payload=payload):
                response = client.post("/page-feedback", json=payload)
                self.assertEqual(response.status_code, 400)
                self.assertEqual({"ok": False}, response.get_json())

    def test_home_page_removes_minigames_from_primary_navigation(self):
        client = app.test_client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn('href="/minigames"', html)
        self.assertNotIn(">미니게임<", html)
        for phrase in [
            "Hero Command Board",
            "Command Surface",
            "Core Tools",
            "Reading",
            "Signals",
            "Trust Notes",
            "What We Offer",
            "Across Surfaces",
            "When It Helps",
            "Read Before You Use",
            "Life Utility Board",
            "AgeCalc System",
            "삶의 기준을 읽는 도구를 한 보드에 정렬합니다",
            "같은 리듬으로 배치해",
            "설명형 유틸리티 사이트",
        ]:
            self.assertNotIn(phrase, html)

    def test_life_hub_pages_remain_accessible_but_noindex_during_review(self):
        client = app.test_client()
        expected_hubs = {str(hub["path"]): str(hub["title"]) for hub in HUB_PAGES}

        for path, title in expected_hubs.items():
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn(f"<h1>{title}</h1>", html)
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{path}" />',
                    html,
                )
                self.assertIn('name="description"', html)
                self.assertIn("대표 도구", html)
                self.assertIn("더 살펴보기", html)
                self.assertIn("운영 기준", html)
                self.assertNotIn("google-adsense-account", html)
                self.assertIn('name="robots" content="noindex,follow"', html)
                self.assertEqual(response.headers.get("X-Robots-Tag"), "noindex, follow")

    def test_life_hubs_are_excluded_from_review_mode_sitemap(self):
        locations = _sitemap_leaf_locations(app.test_client())
        for hub in HUB_PAGES:
            self.assertNotIn(f"https://agecalc.cloud{hub['path']}", locations)
        self.assertEqual(46, len(locations))

    def test_life_hubs_render_direct_answers_and_contextual_paths(self):
        client = app.test_client()

        for hub in HUB_PAGES:
            with self.subTest(key=hub["key"]):
                html = client.get(hub["path"]).get_data(as_text=True)

                self.assertRegex(html, r'class="[^"]*\bdirect-answer\b[^"]*"')
                self.assertIn('class="related-paths"', html)

    def test_life_hubs_render_unique_usage_guides(self):
        client = app.test_client()
        expected_headings = {
            "age": "나이 기준을 먼저 정하세요",
            "family": "가족의 기준일을 먼저 정하세요",
            "education": "현재 학년과 입학연도를 나눠 확인하세요",
            "anniversary": "기념일의 시작일 포함 여부를 정하세요",
            "retirement": "제도 이름과 기준일을 먼저 확인하세요",
            "health": "공식 조회 전에 나이 기준을 맞추세요",
            "pets": "반려동물의 종과 현재 연령을 확인하세요",
            "generations": "출생연도와 비교 기준을 먼저 정하세요",
        }

        hubs_by_key = {str(hub["key"]): hub for hub in HUB_PAGES}
        for key, heading in expected_headings.items():
            with self.subTest(key=key):
                html = client.get(hubs_by_key[key]["path"]).get_data(as_text=True)

                self.assertIn("life-hub-usage-guide", html)
                self.assertIn("이렇게 시작하세요", html)
                self.assertIn(heading, html)

    def test_public_pages_render_visual_and_schema_breadcrumbs(self):
        client = app.test_client()
        expected_paths = {
            "/age": ("나이 계산", "만나이 계산기"),
            "/family/": ("가족·육아",),
            "/guides/age-calculation-2026": ("나이 계산", "2026년 만나이 계산 기준"),
            "/privacy": ("개인정보처리방침",),
        }

        for path, labels in expected_paths.items():
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn('class="breadcrumbs"', html)
                self.assertIn('aria-label="현재 위치"', html)
                self.assertIn('"@type": "BreadcrumbList"', html)
                self.assertIn('"itemListElement"', html)
                self.assertIn('"https://agecalc.cloud/"', html)
                for label in labels:
                    self.assertIn(label, html)

        home_html = client.get("/").get_data(as_text=True)
        self.assertNotIn('class="breadcrumbs"', home_html)
        self.assertNotIn('"@type": "BreadcrumbList"', home_html)

    def test_every_non_home_sitemap_page_renders_breadcrumb_schema(self):
        client = app.test_client()
        paths = [
            location.removeprefix("https://agecalc.cloud")
            for location in _sitemap_leaf_locations(client)
            if location != "https://agecalc.cloud/"
        ]

        for path in paths:
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn('class="breadcrumbs"', html)
                self.assertIn('"@type": "BreadcrumbList"', html)

    def test_core_pages_render_editorial_metadata(self):
        client = app.test_client()
        core_paths = (
            "/age",
            "/birth-year-age-table",
            "/school-grade-calculator",
            "/school-entry-year-table",
            "/age-gap-calculator",
            "/100-day-calculator",
            "/annual-age-calculator",
            "/age-comparison-table",
            "/grade-age-table",
            "/pet-age-table",
            "/korean-age-guide",
            "/pet-months-table",
            "/grade-birth-year-table",
            "/college-entry-year-calculator",
            "/birthday-dday-calculator",
            "/dog",
            "/cat",
            "/baby-months",
            "/d-day",
            "/parent-child",
        )

        self.assertEqual(20, len(core_paths))
        for path in core_paths:
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn('class="editorial-meta"', html)
                self.assertIn("작성·검수 정보", html)
                self.assertIn("AgeCalc 편집팀", html)
                self.assertIn("기준 확인일", html)
                self.assertIn("최종 수정일", html)
                self.assertIn("참고 출처", html)
                self.assertIn('"@type": "WebPage"', html)
                self.assertIn('"dateModified"', html)
                self.assertIn('"author"', html)
                self.assertIn('"reviewedBy"', html)

    def test_ymyl_pages_require_official_sources(self):
        client = app.test_client()
        ymyl_paths = (
            "/age",
            "/school-grade-calculator",
            "/school-entry-year-table",
            "/grade-age-table",
            "/dog",
            "/cat",
            "/baby-months",
            "/baby-months-table",
        )

        for path in ymyl_paths:
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn('data-official-source="true"', html)
                self.assertRegex(html, r'href="https://[^"]+"')
                self.assertIn("확인일 2026-06-22", html)
                self.assertIn("공식 판단이나 진단을 대신하지 않습니다", html)

    def test_core_age_pages_have_distinct_deep_content_sections(self):
        client = app.test_client()
        expectations = {
            "/age": (
                "생일이 지났는지에 따라 만나이가 한 살 달라집니다",
                "만나이 공식",
                "2월 29일과 음력 생일",
                "계산 결과 다음에 확인할 일",
            ),
            "/birth-year-age-table": (
                "20살은 연나이 기준",
                "나이·띠·세대·학교·기념 나이",
                "출생연도표 해석 예외",
                "표를 본 다음 할 일",
            ),
            "/annual-age-calculator": (
                "연나이는 올해 연도에서 출생연도를 빼서 계산합니다",
                "입력형 연나이 계산",
                "연나이 사용 예외",
                "연나이 결과 다음에 확인할 일",
            ),
            "/age-comparison-table": (
                "비교표는 세 나이 체계의 차이를 개념별로 설명합니다",
                "만나이·연나이·한국식 나이 공식 비교",
                "비교표 해석 예외",
                "비교한 다음 선택할 계산기",
            ),
            "/birthday-dday-calculator": (
                "다음 생일까지 남은 날짜는 올해 생일과 내년 생일을 차례로 비교해 계산합니다",
                "생일 D-day 공식",
                "2월 29일 생일과 기준일 예외",
                "D-day 결과 다음에 할 일",
            ),
        }

        for path, phrases in expectations.items():
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertRegex(html, r'class="[^"]*\bdirect-answer\b[^"]*"')
                self.assertGreaterEqual(html.count("data-example-card"), 3)
                for phrase in phrases:
                    self.assertIn(phrase, html)

    def test_core_education_pages_have_distinct_deep_content_sections(self):
        client = app.test_client()
        expectations = {
            "/school-grade-calculator": (
                "출생연도로 현재 학년과 졸업 예정 학년도를 계산합니다",
                "현재 학년 계산",
                "학년도와 1~2월 기준",
                "조기입학·입학유예·해외 학제",
            ),
            "/school-entry-year-table": (
                "출생연도로 초등학교·중학교·고등학교 입학 학년도를 확인합니다",
                "입학 시점 계산",
                "취학통지서와 실제 입학",
                "조기입학·입학유예·해외 학제",
            ),
            "/grade-age-table": (
                "학년을 선택하면 일반적인 나이 범위가 나옵니다",
                "학년별 나이 해석",
                "같은 학년의 나이가 다른 이유",
                "조기입학·입학유예·해외 학제",
            ),
            "/grade-birth-year-table": (
                "학년을 선택하면 일반적으로 해당하는 출생연도가 나옵니다",
                "학년별 출생연도 해석",
                "빠른년생과 출생연도 예외",
                "조기입학·입학유예·해외 학제",
            ),
            "/college-entry-year-calculator": (
                "학번으로 일반적인 출생연도와 현재 나이 범위를 역산합니다",
                "대학 학번 역산",
                "학번 검색에서 자주 묻는 질문",
                "해외 대학과 학교별 학번 체계",
            ),
        }

        for path, phrases in expectations.items():
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertRegex(html, r'class="[^"]*\bdirect-answer\b[^"]*"')
                self.assertGreaterEqual(html.count("data-example-card"), 3)
                self.assertIn("교육부", html)
                self.assertIn("국가법령정보센터", html)
                self.assertIn("확인일 2026-06-22", html)
                for phrase in phrases:
                    self.assertIn(phrase, html)

    def test_core_family_anniversary_pages_have_distinct_deep_content_sections(self):
        client = app.test_client()
        expectations = {
            "/baby-months": (
                "월령은 출생일에서 기준일까지 완료된 달 수입니다",
                "월령 계산과 발달 판단은 다릅니다",
                "월말 출생일 계산 예외",
                "월령 결과 다음에 확인할 일",
            ),
            "/baby-months-table": (
                "개월수 계산표는 월령을 연·개월 표현으로 바꿔 읽는 표입니다",
                "월령표와 발달 정보의 차이",
                "월령표 해석 예외",
                "표를 본 다음 할 일",
            ),
            "/100-day-calculator": (
                "100일째는 시작일을 1일째로 포함해 시작일에 99일을 더한 날짜입니다",
                "시작일 포함 100일 공식",
                "윤년과 월말을 지나는 100일",
                "100일 결과 다음에 할 일",
            ),
            "/d-day": (
                "D-day는 오늘을 제외하고 목표 날짜까지 남은 날짜 수를 계산합니다",
                "D-day 포함 기준",
                "윤년·월말·시간대 예외",
                "D-day 결과 다음에 할 일",
            ),
            "/parent-child": (
                "부모와 자녀의 생년월일로 출산 당시 만나이와 주요 가족 시점을 계산합니다",
                "부모·자녀 나이 관계 공식",
                "환갑·칠순과 학교 시점",
                "가족 결과 다음에 확인할 일",
            ),
        }

        for path, phrases in expectations.items():
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertRegex(html, r'class="[^"]*\bdirect-answer\b[^"]*"')
                self.assertGreaterEqual(html.count("data-example-card"), 3)
                for phrase in phrases:
                    self.assertIn(phrase, html)

    def test_baby_month_pages_separate_date_calculation_from_medical_judgment(self):
        client = app.test_client()

        for path in ("/baby-months", "/baby-months-table"):
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn("질병관리청", html)
                self.assertIn("국민건강보험공단", html)
                self.assertIn('data-official-source="true"', html)
                self.assertIn("날짜 계산", html)
                self.assertIn("발달 평가나 의료 진단을 대신하지 않습니다", html)

        script = Path("static/js/baby-months.js").read_text(encoding="utf-8")
        self.assertIn("날짜 계산 결과이며 발달 평가나 의료 진단이 아닙니다.", script)
        self.assertNotIn("미국 일정 예시", script)
        self.assertNotIn("발달 단계 참고", script)

    def test_parent_child_results_link_family_and_school_milestones(self):
        script = Path("static/js/parent-child.js").read_text(encoding="utf-8")

        self.assertIn("/guides/sixtieth-seventieth-eightieth-age-guide", script)
        self.assertIn("/school-grade-calculator?year=", script)
        self.assertIn("/school-entry-year-table?year=", script)
        self.assertIn("환갑·칠순 기준 보기", script)
        self.assertIn("자녀 학교 시점 보기", script)

    def test_core_pet_pages_have_distinct_deep_content_sections(self):
        client = app.test_client()
        expectations = {
            "/dog": (
                "강아지 사람 나이 환산값은 체형별 연령표를 적용한 참고 수치입니다",
                "환산 나이와 건강 상태는 다릅니다",
                "체형·품종·생활환경에 따른 한계",
                "환산 결과 다음에 확인할 일",
            ),
            "/cat": (
                "고양이 사람 나이 환산값은 초기 성장 속도를 반영한 참고 수치입니다",
                "환산 나이와 건강 상태는 다릅니다",
                "품종·생활환경·질병 이력에 따른 한계",
                "환산 결과 다음에 확인할 일",
            ),
            "/pet-age-table": (
                "반려동물 나이표는 실제 나이를 사람 나이 기준으로 비교하는 참고표입니다",
                "나이표가 건강 상태를 뜻하지 않는 이유",
                "종·체형·품종별 해석 한계",
                "나이표 다음에 확인할 일",
            ),
            "/pet-months-table": (
                "반려동물 월령표는 생후 24개월까지의 환산 흐름을 보는 참고표입니다",
                "월령 환산과 발달·건강 판단의 차이",
                "어린 반려동물 환산의 한계",
                "월령표 다음에 확인할 일",
            ),
        }

        for path, phrases in expectations.items():
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertRegex(html, r'class="[^"]*\bdirect-answer\b[^"]*"')
                self.assertGreaterEqual(html.count("data-example-card"), 3)
                self.assertIn('data-official-source="true"', html)
                self.assertIn("수의학적 진단을 대신하지 않습니다", html)
                for phrase in phrases:
                    self.assertIn(phrase, html)

    def test_pet_calculator_result_separates_conversion_from_diagnosis(self):
        script = Path("static/js/pet-age.js").read_text(encoding="utf-8")

        self.assertIn("환산 나이는 건강 상태나 기대수명을 판정하지 않습니다.", script)
        self.assertNotIn("건강 관리 방향을 잡기 위한 참고치", script)
        self.assertNotIn("체감 나이", script)

    def test_guide_content_policy_covers_all_twenty_guides(self):
        self.assertTrue(hasattr(guide_pages_module, "GUIDE_CONTENT_POLICY"))
        guide_content_policy = guide_pages_module.GUIDE_CONTENT_POLICY
        self.assertEqual(20, len(guide_content_policy))
        self.assertEqual(set(GUIDE_SLUGS), set(guide_content_policy))

        allowed_actions = {"keep", "strengthen", "merge", "noindex"}
        for page in GUIDE_PAGES:
            with self.subTest(slug=page["slug"]):
                policy = guide_content_policy[page["slug"]]
                self.assertIn(policy["action"], allowed_actions)
                self.assertEqual(policy["action"], page["content_action"])
                self.assertEqual(policy["indexable"], page["indexable"])
                if not policy["indexable"]:
                    self.assertTrue(policy["canonical_path"].startswith("/"))
                    self.assertEqual(policy["canonical_path"], policy["future_redirect"])

    def test_merged_guides_are_preserved_but_noindex_without_ads(self):
        client = app.test_client()
        merged_targets = {
            "dog-age-human-age-guide": "/dog",
            "cat-age-human-age-guide": "/cat",
            "pet-age-table-guide": "/pet-age-table",
            "age-gap-calculation-guide": "/age-gap-calculator",
        }
        sitemap_body = "\n".join(_sitemap_leaf_locations(client))
        guide_html = client.get("/guide").get_data(as_text=True)

        for slug, canonical_path in merged_targets.items():
            with self.subTest(slug=slug):
                response = client.get(f"/guides/{slug}")
                html = response.get_data(as_text=True)

                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get("X-Robots-Tag"), "noindex, follow")
                self.assertIn('<meta name="robots" content="noindex,follow" />', html)
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{canonical_path}" />',
                    html,
                )
                self.assertIn("통합 예정 안내", html)
                self.assertNotIn("google-adsense-account", html)
                self.assertNotIn(f"https://agecalc.cloud/guides/{slug}", sitemap_body)
                self.assertNotIn(f'href="/guides/{slug}"', guide_html)

    def test_retained_guides_add_examples_and_comparison_tables(self):
        client = app.test_client()

        for page in GUIDE_PAGES:
            if not page.get("indexable", True):
                continue
            with self.subTest(slug=page["slug"]):
                response = client.get(f"/guides/{page['slug']}")
                html = response.get_data(as_text=True)

                self.assertEqual(response.status_code, 200)
                self.assertRegex(html, r'class="[^"]*\bdirect-answer\b[^"]*"')
                self.assertGreaterEqual(html.count("data-example-card"), 3)
                self.assertIn('class="guide-comparison-table"', html)
                self.assertIn("content_format", page)
                self.assertIn(f'data-content-format="{page.get("content_format", "")}"', html)
                self.assertIn(f'class="guide-content-{page.get("content_format", "")}"', html)

    def test_education_results_link_to_next_school_milestones(self):
        client = app.test_client()
        cases = {
            "/school-grade-calculator?year=2015": (
                "2028학년도 중학교 입학",
                "2034년 2월 고등학교 졸업 예정",
                'href="/school-entry-year-table?year=2015"',
                'href="/parent-child"',
            ),
            "/school-entry-year-table?year=2019": (
                "2026학년도 초등학교 입학",
                "2038년 2월 고등학교 졸업 예정",
                'href="/school-grade-calculator?year=2019"',
                'href="/parent-child"',
            ),
            "/grade-age-table?stage=middle&grade=1": (
                "중학교 1학년",
                "고등학교 입학 시점 확인",
                'href="/school-entry-year-table',
                'href="/parent-child"',
            ),
            "/grade-birth-year-table?stage=high&grade=1": (
                "고등학교 1학년",
                "대학 학번 흐름 확인",
                'href="/college-entry-year-calculator',
                'href="/parent-child"',
            ),
            "/college-entry-year-calculator?year=2026": (
                "26학번",
                "고등학교 졸업 시점 역산",
                'href="/grade-birth-year-table',
                'href="/parent-child"',
            ),
        }

        for path, phrases in cases.items():
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                for phrase in phrases:
                    self.assertIn(phrase, html)

    def test_core_pages_render_contextual_links(self):
        client = app.test_client()
        core_paths = (
            "/age",
            "/birth-year-age-table",
            "/school-grade-calculator",
            "/school-entry-year-table",
            "/100-day-calculator",
            "/pet-age-table",
            "/birthday-dday-calculator",
            "/dog",
            "/cat",
            "/baby-months",
            "/d-day",
            "/parent-child",
        )

        for path in core_paths:
            with self.subTest(path=path):
                response = client.get(path)

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                match = re.search(
                    r'<nav class="related-paths".*?</nav>',
                    html,
                    re.S,
                )
                self.assertIsNotNone(match)
                related_html = match.group(0)
                self.assertIn('data-link-group="before_calculation"', related_html)
                self.assertIn('data-link-group="after_result"', related_html)
                self.assertIn('data-link-group="adjacent_tools"', related_html)
                self.assertIn('data-link-group="official_sources"', related_html)
                hrefs = re.findall(r'href="([^"]+)"', related_html)
                self.assertGreaterEqual(len(set(hrefs)), 4)
                self.assertNotIn(path, hrefs)

    def test_public_sitemap_pages_render_adsense_approval_code(self):
        client = app.test_client()

        with app.test_request_context("/"):
            paths = [url_for(endpoint) for endpoint in PUBLIC_SITEMAP_ENDPOINTS if endpoint != "blog_list"]

        for path in paths:
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn(
                    '<meta name="google-adsense-account" content="ca-pub-7818333740838556">',
                    html,
                )
                self.assertIn(
                    "https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=ca-pub-7818333740838556",
                    html,
                )
                self.assertIn("google-site-verification", html)
                self.assertIn("tracking-config", html)
                self.assertNotIn("www.googletagmanager.com/gtag/js", html)

    def test_public_sitemap_keeps_only_review_mode_urls(self):
        client = app.test_client()
        locations = _sitemap_leaf_locations(client)
        joined_locations = "\n".join(locations)

        self.assertEqual(46, len(locations))
        self.assertNotIn("/minigames", joined_locations)
        self.assertNotIn("/blog/drafts", joined_locations)
        self.assertNotIn("/blog/review", joined_locations)
        self.assertNotIn("https://agecalc.cloud/blog", locations)
        self.assertNotIn("https://agecalc.cloud/blog/2026-man-age-guide", locations)

    def test_static_guide_pages_are_public_with_adsense_code(self):
        client = app.test_client()
        guide_content_policy = getattr(guide_pages_module, "GUIDE_CONTENT_POLICY", {})

        self.assertEqual(20, len(GUIDE_SLUGS))
        self.assertEqual(len(GUIDE_SLUGS), len(set(GUIDE_SLUGS)))
        self.assertIn("elementary-school-entry-target-2026", GUIDE_SLUGS)
        self.assertIn("sixtieth-seventieth-eightieth-age-guide", GUIDE_SLUGS)
        self.assertTrue({"age", "school", "anniversary", "pet", "family"}.issubset(GUIDE_CATEGORIES))

        for slug in GUIDE_SLUGS:
            with self.subTest(slug=slug):
                response = client.get(f"/guides/{slug}")
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                canonical_path = guide_content_policy.get(slug, {}).get(
                    "canonical_path",
                    f"/guides/{slug}",
                )
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud{canonical_path}" />',
                    html,
                )
                self.assertIn("<h1", html)
                self.assertIn('name="description"', html)
                self.assertIn("guide-category-label", html)
                self.assertIn("관련 계산기", html)
                self.assertIn("자주 묻는 질문", html)
                if guide_content_policy.get(slug, {}).get("indexable", True):
                    self.assertIn("google-adsense-account", html)
                    self.assertNotIn("noindex", html)
                else:
                    self.assertNotIn("google-adsense-account", html)
                    self.assertIn("noindex", html)

    def test_search_keyword_guides_cover_non_duplicate_queries(self):
        client = app.test_client()

        entry_response = client.get("/guides/elementary-school-entry-target-2026")
        self.assertEqual(entry_response.status_code, 200)
        entry_html = entry_response.get_data(as_text=True)
        self.assertIn("2026년 초등학교 입학 대상자", entry_html)
        self.assertIn("2019년생", entry_html)
        self.assertIn("입학통지서", entry_html)

        milestone_response = client.get("/guides/sixtieth-seventieth-eightieth-age-guide")
        self.assertEqual(milestone_response.status_code, 200)
        milestone_html = milestone_response.get_data(as_text=True)
        self.assertIn("환갑", milestone_html)
        self.assertIn("칠순", milestone_html)
        self.assertIn("팔순", milestone_html)

    def test_existing_pages_cover_duplicate_keyword_queries(self):
        client = app.test_client()

        birth_year_response = client.get("/birth-year-age-table")
        self.assertEqual(birth_year_response.status_code, 200)
        self.assertIn("몇년생 몇살", birth_year_response.get_data(as_text=True))

        early_birth_response = client.get("/guides/early-birth-school-grade-guide")
        self.assertEqual(early_birth_response.status_code, 200)
        self.assertIn("빠른년생 학년 계산", early_birth_response.get_data(as_text=True))

        college_response = client.get("/college-entry-year-calculator")
        self.assertEqual(college_response.status_code, 200)
        self.assertIn("26학번 몇년생", college_response.get_data(as_text=True))

    def test_adsense_code_is_not_rendered_on_excluded_pages(self):
        client = app.test_client()

        for path in ["/minigames", "/minigames/guess", "/minigames/snake"]:
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertNotIn("google-adsense-account", html)
                self.assertNotIn("pagead/js/adsbygoogle.js", html)

        post = SimpleNamespace(
            id=1,
            title="검토 글",
            slug="review-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="needs_review",
            sources=[],
        )

        for path, modes in [
            ("/blog/drafts/review-post", {"draft_mode": True, "review_mode": False}),
            ("/blog/review/1", {"draft_mode": False, "review_mode": True, "review_token": "token"}),
        ]:
            with self.subTest(path=path), app.test_request_context(path):
                html = render_template(
                    "blog-detail.html",
                    post=post,
                    author_name="AgeCalc 편집팀",
                    editorial_policy_url="/about",
                    **modes,
                )
                self.assertNotIn("google-adsense-account", html)
                self.assertNotIn("pagead/js/adsbygoogle.js", html)

    def test_blog_detail_renders_author_policy_and_sources(self):
        post = SimpleNamespace(
            title="테스트 글",
            slug="test-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[
                SimpleNamespace(
                    source_name="Example Source",
                    source_url="https://example.com/story",
                    attribution_text="Editorial reference",
                )
            ],
        )

        with app.test_request_context("/blog/test-post"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
            )

        self.assertIn("AgeCalc 편집팀", html)
        self.assertIn("/about", html)
        self.assertIn("Example Source", html)
        self.assertIn("https://example.com/story", html)
        self.assertNotIn("AgeCalc Editorial", html)
        self.assertNotIn("Related Tools", html)

    def test_structured_blog_article_registry_defines_flagship_man_age_post(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS, structured_blog_article_for_slug

        article = structured_blog_article_for_slug("2026-man-age-guide")

        self.assertIn("2026-man-age-guide", BLOG_ARTICLE_BLUEPRINTS)
        self.assertEqual("2026년 만나이 계산 기준 총정리", article["h1"])
        self.assertEqual("/age", article["primary_cta"]["path"])
        self.assertGreaterEqual(len(article["direct_answer_paragraphs"]), 3)
        self.assertGreaterEqual(len(article["example_cards"]), 3)
        self.assertGreaterEqual(len(article["faq_items"]), 3)

    def test_structured_blog_article_registry_defines_four_additional_curated_posts(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS, structured_blog_article_for_slug

        expected = {
            "birth-year-age-interpretation": "/birth-year-age-table",
            "early-birth-school-grade-guide": "/school-grade-calculator",
            "baby-months-calculation-guide": "/baby-months",
            "parent-child-age-gap-guide": "/parent-child",
        }

        for slug, primary_path in expected.items():
            with self.subTest(slug=slug):
                article = structured_blog_article_for_slug(slug)
                self.assertIn(slug, BLOG_ARTICLE_BLUEPRINTS)
                self.assertIsNotNone(article)
                self.assertEqual(slug, article["slug"])
                self.assertEqual(primary_path, article["primary_cta"]["path"])
                self.assertGreaterEqual(len(article["direct_answer_paragraphs"]), 3)
                self.assertGreaterEqual(len(article["example_cards"]), 3)
                self.assertGreaterEqual(len(article["faq_items"]), 3)

    def test_structured_blog_article_registry_exposes_related_tools_and_articles(self):
        from content.blog_articles import structured_blog_article_for_slug

        article = structured_blog_article_for_slug("2026-man-age-guide")

        tool_paths = [tool["path"] for tool in article["related_tools"]]
        article_paths = [item["path"] for item in article["related_articles"]]

        self.assertIn("/age", tool_paths)
        self.assertIn("/age-comparison-table", tool_paths)
        self.assertIn("/birth-year-age-table", tool_paths)
        self.assertIn("/references", tool_paths)
        self.assertIn("/blog/birth-year-age-interpretation", article_paths)
        self.assertIn("/blog/early-birth-school-grade-guide", article_paths)

    def test_structured_blog_article_registry_returns_isolated_deep_copy(self):
        from content.blog_articles import structured_blog_article_for_slug

        article_one = structured_blog_article_for_slug("2026-man-age-guide")
        original_primary_path = article_one["primary_cta"]["path"]
        original_related_tool_path = article_one["related_tools"][0]["path"]
        original_faq_question = article_one["faq_items"][0]["question"]

        article_one["primary_cta"]["path"] = "/mutated-path"
        article_one["related_tools"][0]["path"] = "/mutated-tool"
        article_one["faq_items"][0]["question"] = "mutated-question"

        article_two = structured_blog_article_for_slug("2026-man-age-guide")

        self.assertEqual(original_primary_path, article_two["primary_cta"]["path"])
        self.assertEqual(original_related_tool_path, article_two["related_tools"][0]["path"])
        self.assertEqual(original_faq_question, article_two["faq_items"][0]["question"])
        self.assertNotEqual(article_one["primary_cta"]["path"], article_two["primary_cta"]["path"])
        self.assertNotEqual(article_one["related_tools"][0]["path"], article_two["related_tools"][0]["path"])
        self.assertNotEqual(article_one["faq_items"][0]["question"], article_two["faq_items"][0]["question"])

    def test_structured_blog_article_registry_returns_none_for_missing_slug(self):
        from content.blog_articles import structured_blog_article_for_slug

        self.assertIsNone(structured_blog_article_for_slug("missing-slug"))

    def test_structured_blog_context_returns_article_for_curated_slug(self):
        from content.blog_articles import structured_blog_article_for_slug

        post = SimpleNamespace(
            id=1,
            title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
            slug="2026-man-age-guide",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>레거시 본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        structured_article = app_module._structured_blog_context(post)

        self.assertIsNotNone(structured_article)
        self.assertEqual(
            structured_blog_article_for_slug("2026-man-age-guide"),
            structured_article,
        )
        self.assertEqual("/age", structured_article["primary_cta"]["path"])

    def test_structured_blog_context_returns_none_for_uncurated_slug(self):
        post = SimpleNamespace(slug="uncurated-post")

        self.assertIsNone(app_module._structured_blog_context(post))

    def test_blog_detail_route_passes_structured_article_context_for_curated_slug(self):
        from content.blog.rendering import render_article_content_html

        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def count(self):
                return 1

            def order_by(self, *args, **kwargs):
                return self

            def all(self):
                return [self.post]

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post

            def query(self, model):
                return FakeQuery(self.post)

        article = app_module.structured_blog_article_for_slug("2026-man-age-guide")
        post = SimpleNamespace(
            id=1,
            title=article["title"],
            slug=article["slug"],
            excerpt=article["summary"],
            cover_image_url=article["thumbnail"],
            content_html=render_article_content_html(article),
            published_at=datetime(2026, 7, 22, 12, 0),
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )
        captured = {}

        def fake_render(template_name, **kwargs):
            captured["template_name"] = template_name
            captured["kwargs"] = kwargs
            return "rendered-blog-detail"

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(post)), mock.patch.object(
            app_module, "render_template", side_effect=fake_render
        ), mock.patch.object(app_module, "_is_blog_public_indexable", return_value=True):
            response = app.test_client().get("/blog/2026-man-age-guide")

        self.assertEqual(response.status_code, 200)
        self.assertEqual("blog-detail.html", captured["template_name"])
        self.assertEqual("2026-man-age-guide", captured["kwargs"]["structured_article"]["slug"])
        self.assertEqual("/age", captured["kwargs"]["structured_article"]["primary_cta"]["path"])

    def test_seed_public_blog_posts_upserts_flagship_article(self):
        from scripts.seed_public_blog_posts import build_seed_post_payload

        payload = build_seed_post_payload("2026-man-age-guide")

        self.assertEqual("2026-man-age-guide", payload["slug"])
        self.assertEqual("draft", payload["status"])
        self.assertIsNone(payload["published_at"])
        self.assertEqual("/static/images/blog/2026-man-age-guide.jpg", payload["cover_image_url"])
        self.assertIn("2026년 만나이 계산 기준 총정리", payload["title"])
        self.assertIn("<h2>2026년 만나이 계산은 이렇게 보면 됩니다</h2>", payload["content_html"])

    def test_seed_public_blog_posts_quarantines_unaudited_legacy_public_content(self):
        from scripts import seed_public_blog_posts

        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)

        published_at = datetime(2026, 6, 1, 12, 0)
        setup_session = Session()
        setup_session.add(
            GeneratedPost(
                slug="2026-man-age-guide",
                title="이전 제목",
                excerpt="이전 요약",
                content_html="<p>이전 본문</p>",
                cover_image_url=None,
                status="published",
                published_at=published_at,
            )
        )
        setup_session.commit()
        setup_session.close()

        with mock.patch.object(seed_public_blog_posts, "SessionLocal", Session):
            post = seed_public_blog_posts.upsert_seed_post("2026-man-age-guide")

        self.assertIsNone(post.published_at)

        verify_session = Session()
        stored = verify_session.query(GeneratedPost).filter(GeneratedPost.slug == "2026-man-age-guide").first()
        verify_session.close()

        self.assertIsNotNone(stored)
        self.assertIsNone(stored.published_at)
        self.assertEqual("draft", stored.status)
        self.assertIn("2026년 만나이 계산 기준 총정리", stored.title)
        self.assertIn("<h2>2026년 만나이 계산은 이렇게 보면 됩니다</h2>", stored.content_html)

    def test_seed_public_blog_posts_main_seeds_curated_slugs(self):
        from scripts import seed_public_blog_posts

        with mock.patch.object(seed_public_blog_posts, "upsert_seed_post") as upsert_seed_post:
            seeded = seed_public_blog_posts.main()

        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS

        self.assertEqual(list(BLOG_ARTICLE_BLUEPRINTS), seeded)
        self.assertEqual(len(BLOG_ARTICLE_BLUEPRINTS), upsert_seed_post.call_count)

    def test_blog_detail_renders_structured_related_tools_and_related_articles(self):
        from content.blog_articles import structured_blog_article_for_slug

        post = SimpleNamespace(
            title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
            slug="2026-man-age-guide",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/2026-man-age-guide"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                structured_article=structured_blog_article_for_slug("2026-man-age-guide"),
                eligible_related_slugs={
                    "birth-year-age-interpretation",
                    "early-birth-school-grade-guide",
                },
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
                coupang_partners_enabled=False,
            )

        self.assertIn("AgeCalc에서 바로 확인하는 순서", html)
        self.assertIn("다음에 읽을 글", html)
        self.assertIn('href="/blog/birth-year-age-interpretation"', html)
        self.assertIn('href="/blog/early-birth-school-grade-guide"', html)
        self.assertIn('data-page-feedback="/blog/2026-man-age-guide"', html)

    def test_blog_detail_uses_faqpage_schema_for_structured_articles(self):
        from content.blog_articles import structured_blog_article_for_slug

        post = SimpleNamespace(
            title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
            slug="2026-man-age-guide",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/2026-man-age-guide"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                structured_article=structured_blog_article_for_slug("2026-man-age-guide"),
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
                coupang_partners_enabled=False,
            )

        self.assertIn('"@type":"FAQPage"', html.replace(" ", ""))
        self.assertIn("2026년에도 공적 기준은 만나이인가요?", html)

    def test_blog_list_surfaces_curated_editorial_positioning_copy(self):
        posts = [
            SimpleNamespace(
                slug="2026-man-age-guide",
                title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
                excerpt="2026년 기준 만나이 계산법과 생일 전후 예외를 한 번에 정리합니다.",
                cover_image_url=None,
                published_at=None,
            )
        ]

        with app.test_request_context("/blog"):
            html = render_template(
                "blog-list.html",
                posts=posts,
                total=1,
                page=1,
                total_pages=1,
                blog_indexable=True,
            )

        self.assertIn("계산기 결과를 해석하는 설명형 글", html)
        self.assertIn('href="/blog/2026-man-age-guide"', html)

    def test_blog_list_shows_all_curated_public_slugs(self):
        from content.blog.rendering import render_article_content_html
        class FakeQuery:
            def __init__(self, posts):
                self.posts = posts

            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def all(self):
                return self.posts

        class FakeSession:
            def __init__(self, posts):
                self.posts = posts

            def query(self, model):
                return FakeQuery(self.posts)

            def close(self):
                pass

        posts = []
        for index, slug in enumerate(
            [
                "2026-man-age-guide",
                "birth-year-age-interpretation",
                "early-birth-school-grade-guide",
                "baby-months-calculation-guide",
                "parent-child-age-gap-guide",
            ],
            start=1,
        ):
            article = app_module.BLOG_ARTICLE_BLUEPRINTS[slug]
            posts.append(SimpleNamespace(
                id=index,
                slug=slug,
                title=article["title"],
                excerpt=article["summary"],
                cover_image_url=article["thumbnail"],
                content_html=render_article_content_html(article),
                published_at=datetime(2026, 6, 26, 12, 0),
                created_at=datetime(2026, 6, 26, 12, 0),
                updated_at=datetime(2026, 6, 26, 12, 0),
                status="published",
                sources=[],
            ))

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(posts)), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            response = app.test_client().get("/blog")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for slug in [post.slug for post in posts]:
            with self.subTest(slug=slug):
                self.assertIn(f'href="/blog/{slug}"', html)

    def test_blog_detail_renders_coupang_partners_sidebar_disclosure(self):
        post = SimpleNamespace(
            title="테스트 글",
            slug="test-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/test-post"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                coupang_partners_enabled=True,
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
            )

        self.assertIn('class="coupang-partners-aside"', html)
        self.assertIn('href="https://link.coupang.com/a/eDmOIdCZP2"', html)
        self.assertIn('target="_blank"', html)
        self.assertIn('rel="sponsored nofollow noopener"', html)
        self.assertIn('referrerpolicy="unsafe-url"', html)
        self.assertIn('src="https://image7.coupangcdn.com/image/affiliate/banner/2df432f2970e664540a310403499b76e@2x.jpg"', html)
        self.assertIn('alt="말랑하니 신생아 디데이달력 4칸, 밀크베이지, 1개"', html)
        self.assertIn('width="120"', html)
        self.assertIn('height="240"', html)
        self.assertIn("이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.", html)

    def test_blog_detail_hides_coupang_partners_sidebar_by_default(self):
        post = SimpleNamespace(
            title="테스트 글",
            slug="test-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/test-post"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                coupang_partners_enabled=False,
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
            )

        self.assertNotIn('class="coupang-partners-aside"', html)
        self.assertNotIn("coupa.ng/cnsP92", html)

    def test_coupang_pet_affiliate_blocks_stay_hidden_on_pet_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/cat", "/dog", "/pet-age-table", "/pet-months-table"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-pet", html)
                    self.assertNotIn('class="coupang-ad-aside"', html)

    def test_coupang_baby_promotion_blocks_stay_hidden_on_baby_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True), mock.patch.object(
            app_module, "_current_local_date", return_value=date(2026, 6, 17)
        ):
            for path in ["/baby-months", "/baby-months-table", "/100-day-calculator", "/birthday-dday-calculator"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-baby", html)
                    self.assertNotIn('class="coupang-ad-aside"', html)

    def test_coupang_age_affiliate_blocks_stay_hidden_on_age_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/age", "/annual-age-calculator", "/age-comparison-table", "/birth-year-age-table"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-age", html)
                    self.assertNotIn('class="coupang-ad-aside"', html)

    def test_coupang_anniversary_affiliate_blocks_stay_hidden_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/d-day", "/birthday-dday-calculator"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-anniversary", html)
                    self.assertNotIn('class="coupang-ad-aside"', html)

    def test_coupang_student_affiliate_blocks_stay_hidden_on_school_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/college-entry-year-calculator", "/school-entry-year-table", "/school-grade-calculator"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-student", html)
                    self.assertNotIn('class="coupang-ad-aside"', html)

    def test_coupang_affiliate_disclosure_uses_smaller_text(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.coupang-disclosure\s*\{[^}]*font-size:\s*0\.78rem;")

    def test_global_coupang_ad_aside_styles_are_removed(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertNotIn(".coupang-ad-aside", css)
        self.assertNotIn(".coupang-ad-rail", css)
        self.assertNotIn(".coupang-ad-frame", css)
        self.assertNotIn(".coupang-ad-card", css)

    def test_global_coupang_ad_aside_never_renders_when_affiliates_are_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/", "/age", "/birth-year-age-table", "/blog", "/minigames/2048"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn('class="coupang-ad-aside"', html)
                    self.assertNotIn(
                        "widgets.html?id=997602&template=carousel&trackingCode=AF6844979",
                        html,
                    )

    def test_coupang_ad_aside_does_not_render_on_guide_pages(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            guide_paths = ["/guide", "/faq", "/korean-age-guide", "/references", "/about", "/contact", "/privacy", "/terms"]
            guide_paths.append(f"/guides/{GUIDE_SLUGS[0]}")

            for path in guide_paths:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-ad-aside", html)
                    self.assertNotIn("widgets.html?id=997602&template=carousel&trackingCode=AF6844979", html)

    def test_coupang_ad_aside_hides_when_disabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", False):
            for path in [
                "/",
                "/age",
                "/birth-year-age-table",
                "/school-grade-calculator",
                "/dog",
                "/cat",
                "/baby-months",
                "/d-day",
                "/parent-child",
            ]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-ad-aside", html)
                    self.assertNotIn("home-coupang-rail", html)
                    self.assertNotIn("coupang-mobile-banner", html)
                    self.assertNotIn(
                        "widgets.html?id=997602&template=carousel&trackingCode=AF6844979",
                        html,
                    )

    def test_coupang_page_sections_no_longer_render_affiliate_blocks(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/cat", "/baby-months", "/college-entry-year-calculator", "/age", "/d-day"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block", html)

    def test_coupang_baby_promotion_blocks_hide_after_promotions_expire(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True), mock.patch.object(
            app_module, "_current_local_date", return_value=date(2026, 6, 29)
        ):
            response = client.get("/baby-months")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn("https://link.coupang.com/a/eDoP3hEASq", html)
        self.assertNotIn("https://link.coupang.com/a/eDoUqmShXM", html)
        self.assertNotIn("https://link.coupang.com/a/eDqzcGE02m", html)
        self.assertNotIn('class="coupang-ad-aside"', html)

    def test_blog_detail_hides_internal_generation_attribution(self):
        post = SimpleNamespace(
            title="테스트 글",
            slug="test-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[
                SimpleNamespace(
                    source_name="KR - 시니어 건강",
                    source_url="https://news.google.com/rss/articles/example?oc=5",
                    attribution_text="Generated from RSS (openai)",
                )
            ],
        )

        with app.test_request_context("/blog/test-post"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
            )

        self.assertIn("KR - 시니어 건강", html)
        self.assertNotIn("Generated from RSS", html)

    def test_blog_list_uses_natural_intro_copy(self):
        posts = [
            SimpleNamespace(
                slug="test-post",
                title="테스트 글",
                excerpt="요약",
                cover_image_url=None,
                published_at=None,
            )
        ]

        with app.test_request_context("/blog"):
            html = render_template(
                "blog-list.html",
                posts=posts,
                total=1,
                page=1,
                total_pages=1,
                blog_indexable=True,
            )

        self.assertIn("계산기 결과를 해석하는 설명형 글만 선별해 공개합니다.", html)
        self.assertNotIn("계산기에서 끝나지 않는 배경 설명과 생활 맥락을 읽기 좋은 형식으로 정리합니다.", html)

    def test_blog_detail_uses_natural_fixed_copy(self):
        post = SimpleNamespace(
            title="테스트 글",
            slug="test-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )

        with app.test_request_context("/blog/test-post"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
            )

        self.assertIn("글 목록으로 돌아가기", html)
        self.assertIn("같이 보면 좋은 계산기", html)
        self.assertIn("운영 원칙 보기", html)
        self.assertIn("문의 및 수정 요청", html)
        self.assertIn("/contact", html)
        self.assertNotIn("블로그 목록으로 돌아가기", html)
        self.assertNotIn("함께 보기", html)
        self.assertNotIn("운영 원칙과 편집 기준 보기", html)
        self.assertNotIn("footer-links article-links", html)

    def test_age_page_uses_natural_korean_labels(self):
        client = app.test_client()
        response = client.get("/age")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for phrase in ["Core Utility", "Dual", "Guide", "Policy", "설명형 결과 해석"]:
            self.assertNotIn(phrase, html)

    def test_header_uses_life_hub_navigation(self):
        with app.test_request_context("/"):
            html = render_template("partials/header.html", blog_public_indexable=True)

        for label in ["나이", "가족", "교육", "기념일"]:
            self.assertIn('class="hub-nav-direct"', html)
            self.assertIn(f">{label}</a>", html)
        for hub in HUB_PAGES:
            self.assertIn(f'data-hub-key="{hub["key"]}"', html)
            self.assertIn(f'href="{hub["path"]}"', html)
        self.assertIn("전체 허브", html)
        self.assertIn("블로그", html)
        self.assertIn("메뉴 열기", html)
        self.assertIn("mega-nav", html)
        self.assertIn("mega-menu-panel", html)
        self.assertNotIn(">계산기<", html)
        self.assertNotIn(">표·비교<", html)
        self.assertNotIn('class="nav-links"', html)

    def test_mobile_navigation_lists_eight_hubs_with_three_tools_at_most(self):
        with app.test_request_context("/"):
            html = render_template("partials/header.html", blog_public_indexable=False)

        self.assertEqual(8, html.count('class="mobile-hub-group"'))
        self.assertNotIn("mobile-nav-group-toggle", html)
        self.assertIn("생활 영역 8개", html)
        for key in [
            "age",
            "family",
            "education",
            "anniversary",
            "retirement",
            "health",
            "pets",
            "generations",
        ]:
            block = html.split(f'id="mobile-hub-{key}"', 1)[1].split("</section>", 1)[0]
            self.assertLessEqual(block.count('class="mobile-nav-link"'), 3)

    def test_header_hides_blog_when_public_blog_is_not_indexable(self):
        with app.test_request_context("/"):
            html = render_template("partials/header.html", blog_public_indexable=False)

        self.assertNotIn('href="/blog"', html)
        self.assertNotIn("mobile-nav-blog", html)

    def test_blog_list_is_noindex_when_public_blog_is_not_indexable(self):
        with app.test_request_context("/blog"):
            html = render_template(
                "blog-list.html",
                posts=[],
                total=0,
                page=1,
                total_pages=1,
                blog_indexable=False,
            )

        self.assertIn('<meta name="robots" content="noindex,nofollow" />', html)
        self.assertIn("아직 게시된 글이 없습니다.", html)

    def test_blog_routes_follow_current_public_indexing_policy(self):
        from content.blog.rendering import render_article_content_html

        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post

            def query(self, model):
                return FakeQuery(self.post)

            def close(self):
                pass

        article = app_module.structured_blog_article_for_slug("2026-man-age-guide")
        post = SimpleNamespace(
            id=1,
            title=article["title"],
            slug=article["slug"],
            excerpt=article["summary"],
            cover_image_url=article["thumbnail"],
            content_html=render_article_content_html(article),
            published_at=datetime(2026, 7, 22, 12, 0),
            created_at=None,
            updated_at=None,
            status="published",
            sources=[],
        )
        client = app.test_client()
        expected_public = app_module._is_blog_public_indexable(1)

        list_response = client.get("/blog")
        self.assertEqual(list_response.status_code, 200)
        list_html = list_response.get_data(as_text=True)
        if expected_public:
            self.assertIsNone(list_response.headers.get("X-Robots-Tag"))
            self.assertIn("google-adsense-account", list_html)
        else:
            self.assertEqual(list_response.headers.get("X-Robots-Tag"), "noindex, nofollow")
            self.assertNotIn("google-adsense-account", list_html)

        with (
            mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(post)),
            mock.patch.object(app_module, "_is_blog_public_indexable", return_value=expected_public),
        ):
            detail_response = client.get("/blog/2026-man-age-guide")

        self.assertEqual(detail_response.status_code, 200)
        detail_html = detail_response.get_data(as_text=True)
        self.assertIn('class="breadcrumbs"', detail_html)
        self.assertIn('"@type": "BreadcrumbList"', detail_html)
        if expected_public:
            self.assertIsNone(detail_response.headers.get("X-Robots-Tag"))
            self.assertNotIn('<meta name="robots" content="noindex,nofollow" />', detail_html)
            self.assertIn("google-adsense-account", detail_html)
        else:
            self.assertEqual(detail_response.headers.get("X-Robots-Tag"), "noindex, nofollow")
            self.assertIn('<meta name="robots" content="noindex,nofollow" />', detail_html)
            self.assertNotIn("google-adsense-account", detail_html)

    def test_blog_list_hides_legacy_published_posts_from_public_index(self):
        from content.blog.rendering import render_article_content_html
        class FakeQuery:
            def __init__(self, posts):
                self.posts = posts

            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def count(self):
                return len(self.posts)

            def offset(self, *args, **kwargs):
                return self

            def limit(self, *args, **kwargs):
                return self

            def all(self):
                return self.posts

        class FakeSession:
            def __init__(self, posts):
                self.posts = posts

            def query(self, model):
                return FakeQuery(self.posts)

            def close(self):
                pass

        curated_article = app_module.BLOG_ARTICLE_BLUEPRINTS["2026-man-age-guide"]
        curated_post = SimpleNamespace(
            id=1,
            slug="2026-man-age-guide",
            title=curated_article["title"],
            excerpt=curated_article["summary"],
            cover_image_url=curated_article["thumbnail"],
            content_html=render_article_content_html(curated_article),
            published_at=datetime(2026, 6, 26, 12, 0),
            created_at=datetime(2026, 6, 26, 12, 0),
            updated_at=datetime(2026, 6, 26, 12, 0),
            status="published",
            sources=[],
        )
        legacy_post = SimpleNamespace(
            id=2,
            slug="legacy-general-post",
            title="일반 건강 뉴스 요약",
            excerpt="요약",
            cover_image_url=None,
            published_at=datetime(2026, 6, 20, 12, 0),
            created_at=datetime(2026, 6, 20, 12, 0),
            updated_at=datetime(2026, 6, 20, 12, 0),
            status="published",
            sources=[],
        )

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession([curated_post, legacy_post])), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ):
            response = app.test_client().get("/blog")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/blog/2026-man-age-guide"', html)
        self.assertNotIn('href="/blog/legacy-general-post"', html)

    def test_blog_detail_returns_404_for_unregistered_published_post(self):
        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post

            def query(self, model):
                return FakeQuery(self.post)

            def close(self):
                pass

        legacy_post = SimpleNamespace(
            id=2,
            slug="legacy-general-post",
            title="일반 건강 뉴스 요약",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=datetime(2026, 6, 20, 12, 0),
            created_at=datetime(2026, 6, 20, 12, 0),
            updated_at=datetime(2026, 6, 20, 12, 0),
            status="published",
            sources=[],
        )

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(legacy_post)), mock.patch.object(
            app_module, "_published_blog_count", return_value=0
        ):
            response = app.test_client().get("/blog/legacy-general-post")

        self.assertEqual(response.status_code, 404)

    def test_guides_sitemap_excludes_legacy_published_blog_posts(self):
        from content.blog.rendering import render_article_content_html
        class FakeQuery:
            def __init__(self, posts):
                self.posts = posts

            def filter(self, *args, **kwargs):
                return self

            def order_by(self, *args, **kwargs):
                return self

            def all(self):
                return self.posts

        class FakeSession:
            def __init__(self, posts):
                self.posts = posts

            def query(self, model):
                return FakeQuery(self.posts)

            def close(self):
                pass

        curated_article = app_module.BLOG_ARTICLE_BLUEPRINTS["2026-man-age-guide"]
        curated_post = SimpleNamespace(
            id=1,
            slug="2026-man-age-guide",
            title=curated_article["title"],
            excerpt=curated_article["summary"],
            cover_image_url=curated_article["thumbnail"],
            content_html=render_article_content_html(curated_article),
            published_at=datetime(2026, 6, 26, 12, 0),
            created_at=datetime(2026, 6, 26, 12, 0),
            updated_at=datetime(2026, 6, 26, 12, 0),
            status="published",
        )
        legacy_post = SimpleNamespace(
            id=2,
            slug="legacy-general-post",
            title="legacy",
            excerpt="legacy",
            cover_image_url=None,
            content_html="<p>legacy</p>",
            published_at=datetime(2026, 6, 20, 12, 0),
            created_at=datetime(2026, 6, 20, 12, 0),
            updated_at=datetime(2026, 6, 20, 12, 0),
            status="published",
        )

        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True
        ), mock.patch.object(
            app_module, "_is_blog_public_indexable", return_value=True
        ), mock.patch.object(app_module, "SessionLocal", return_value=FakeSession([curated_post, legacy_post])):
            response = app.test_client().get("/sitemaps/guides.xml")

        self.assertEqual(response.status_code, 200)
        xml = response.get_data(as_text=True)
        self.assertIn("https://agecalc.cloud/blog/2026-man-age-guide", xml)
        self.assertNotIn("https://agecalc.cloud/blog/legacy-general-post", xml)

    def test_blog_review_approval_blocks_posts_that_fail_adsense_audit(self):
        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post
                self.committed = False

            def query(self, model):
                return FakeQuery(self.post)

            def commit(self):
                self.committed = True

        post = SimpleNamespace(
            id=1,
            title="검토 글",
            slug="review-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<h2>짧은 글</h2><p>AgeCalc 계산기와 연결합니다.</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="needs_review",
            sources=[
                SimpleNamespace(
                    source_name="RSS",
                    source_url="https://news.google.com/rss/articles/example?oc=5",
                    attribution_text="Generated from RSS (openai)",
                )
            ],
        )
        fake_session = FakeSession(post)

        with mock.patch.object(app_module, "_review_token_is_valid", return_value=True), mock.patch.object(
            app_module, "SessionLocal", return_value=fake_session
        ), mock.patch.object(app_module, "_published_blog_count", return_value=0):
            client = app.test_client()
            with client.session_transaction() as flask_session:
                flask_session[app_module.BLOG_CSRF_SESSION_KEY] = "csrf-test"
            response = client.post(
                "/blog/review/1/approve",
                data={"review_token": "test", "csrf_token": "csrf-test"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual("needs_review", post.status)
        self.assertFalse(fake_session.committed)
        self.assertIn("공개할 수 없습니다", response.get_data(as_text=True))

    def test_blog_review_approval_get_link_is_read_only(self):
        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post
                self.committed = False

            def query(self, model):
                return FakeQuery(self.post)

            def commit(self):
                self.committed = True

        content_html = (
            "<h2>핵심 요약</h2><p>AgeCalc 계산기와 생활 기준을 함께 살펴보는 설명형 글입니다.</p>"
            "<h2>배경과 맥락</h2><p>한국 독자가 이해하기 쉽도록 원문 내용을 다시 구성했습니다.</p>"
            "<h2>한국 독자가 확인할 점</h2><p>생활 일정과 가족 기록에 맞춰 읽을 수 있습니다.</p>"
            "<h2>AgeCalc 활용 포인트</h2>"
            '<p><a href="/age">만 나이 계산기</a>로 날짜 기준을 먼저 확인하세요.</p>'
            "<h2>주의할 점과 한계</h2><p>개별 상황에 따라 해석이 달라질 수 있으므로 참고용으로 활용해야 합니다.</p>"
            "<h2>참고 링크</h2><p><a href=\"https://example.com/story\">원문 보기</a></p>"
        ) * 24
        post = SimpleNamespace(
            id=305,
            title="검토 글",
            slug="review-post",
            excerpt="요약",
            cover_image_url="/static/generated/review-post-cover.png",
            content_html=content_html,
            published_at=None,
            created_at=None,
            updated_at=None,
            status="needs_review",
            sources=[
                SimpleNamespace(
                    source_name="Example",
                    source_url="https://example.com/story",
                    attribution_text=None,
                )
            ],
        )
        fake_session = FakeSession(post)

        with mock.patch.object(app_module, "_review_token_is_valid", return_value=True), mock.patch.object(
            app_module, "SessionLocal", return_value=fake_session
        ), mock.patch.object(app_module, "_published_blog_count", return_value=0):
            response = app.test_client().get("/blog/review/305/approve?token=test")

        self.assertEqual(response.status_code, 405)
        self.assertEqual("needs_review", post.status)
        self.assertIsNone(post.published_at)
        self.assertFalse(fake_session.committed)

    def test_blog_draft_detail_renders_publish_button_for_draft(self):
        post = SimpleNamespace(
            id=1,
            title="초안 글",
            slug="draft-post",
            excerpt="요약",
            cover_image_url=None,
            content_html="<p>본문</p>",
            published_at=None,
            created_at=None,
            updated_at=None,
            status="draft",
            sources=[],
        )

        with app.test_request_context("/blog/drafts/draft-post"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=True,
                review_mode=False,
                author_name="AgeCalc 편집팀",
                editorial_policy_url="/about",
            )

        self.assertIn("이 글 공개하기", html)
        self.assertIn("/blog/drafts/draft-post/publish", html)

    def test_blog_draft_publish_marks_audited_draft_as_published(self):
        from content.blog.rendering import render_article_content_html
        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post
                self.committed = False

            def query(self, model):
                return FakeQuery(self.post)

            def commit(self):
                self.committed = True

        article = app_module.BLOG_ARTICLE_BLUEPRINTS["2026-man-age-guide"]
        content_html = render_article_content_html(article)
        post = SimpleNamespace(
            id=1,
            title=article["title"],
            slug="2026-man-age-guide",
            excerpt=article["summary"],
            cover_image_url=article["thumbnail"],
            content_html=content_html,
            published_at=None,
            created_at=None,
            updated_at=None,
            status="draft",
            sources=[],
        )
        fake_session = FakeSession(post)
        client = app.test_client()
        with client.session_transaction() as flask_session:
            flask_session[app_module.BLOG_DRAFT_ACCESS_SESSION_KEY] = True
            flask_session[app_module.BLOG_CSRF_SESSION_KEY] = "csrf-test"

        with mock.patch.object(app_module, "SessionLocal", return_value=fake_session), mock.patch.object(
            app_module, "_published_blog_count", return_value=0
        ):
            response = client.post(
                "/blog/drafts/2026-man-age-guide/publish",
                data={"csrf_token": "csrf-test"},
            )

        self.assertEqual(response.status_code, 302)
        self.assertEqual("published", post.status)
        self.assertIsNotNone(post.published_at)
        self.assertTrue(fake_session.committed)
        self.assertIn("/blog/2026-man-age-guide", response.headers["Location"])

    def test_blog_draft_publish_blocks_missing_cover_image(self):
        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post
                self.committed = False

            def query(self, model):
                return FakeQuery(self.post)

            def commit(self):
                self.committed = True

        content_html = (
            "<h2>핵심 요약</h2><p>AgeCalc 계산기와 생활 기준을 함께 살펴보는 설명형 글입니다.</p>"
            "<h2>배경과 맥락</h2><p>한국 독자가 이해하기 쉽도록 원문 내용을 다시 구성했습니다.</p>"
            "<h2>한국 독자가 확인할 점</h2><p>생활 일정과 가족 기록에 맞춰 읽을 수 있습니다.</p>"
            "<h2>AgeCalc 활용 포인트</h2>"
            '<p><a href="/age">만 나이 계산기</a>로 날짜 기준을 먼저 확인하세요.</p>'
            "<h2>주의할 점과 한계</h2><p>개별 상황에 따라 해석이 달라질 수 있으므로 참고용으로 활용해야 합니다.</p>"
            "<h2>참고 링크</h2><p><a href=\"https://example.com/story\">원문 보기</a></p>"
        ) * 24
        post = SimpleNamespace(
            id=1,
            title="초안 글",
            slug="draft-post",
            excerpt="요약",
            cover_image_url=None,
            content_html=content_html,
            published_at=None,
            created_at=None,
            updated_at=None,
            status="draft",
            sources=[
                SimpleNamespace(
                    source_name="Example",
                    source_url="https://example.com/story",
                    attribution_text=None,
                )
            ],
        )
        fake_session = FakeSession(post)
        client = app.test_client()
        with client.session_transaction() as flask_session:
            flask_session[app_module.BLOG_DRAFT_ACCESS_SESSION_KEY] = True
            flask_session[app_module.BLOG_CSRF_SESSION_KEY] = "csrf-test"

        with mock.patch.object(app_module, "SessionLocal", return_value=fake_session), mock.patch.object(
            app_module, "_published_blog_count", return_value=0
        ):
            response = client.post(
                "/blog/drafts/draft-post/publish",
                data={"csrf_token": "csrf-test"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual("draft", post.status)
        self.assertFalse(fake_session.committed)
        self.assertIn("대표 이미지가 없습니다", response.get_data(as_text=True))

    def test_blog_detail_returns_404_for_unregistered_review_post(self):
        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post

            def query(self, model):
                return FakeQuery(self.post)

        post = SimpleNamespace(
            id=305,
            title="일반 검토 글",
            slug="review-post",
            excerpt="요약",
            cover_image_url="/static/generated/review-post-cover.png",
            content_html="<h2>본문</h2><p>AgeCalc 계산기와 연결한 공개 글입니다.</p>",
            published_at=datetime(2026, 7, 4, 12, 0),
            created_at=datetime(2026, 7, 4, 12, 0),
            updated_at=datetime(2026, 7, 4, 12, 0),
            status="published",
            sources=[],
        )

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(post)), mock.patch.object(
            app_module, "_published_blog_count", return_value=0
        ):
            response = app.test_client().get("/blog/review-post")

        self.assertEqual(response.status_code, 404)

    def test_blog_detail_returns_404_when_registered_post_is_not_published(self):
        from content.blog.rendering import render_article_content_html

        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post

            def query(self, model):
                return FakeQuery(self.post)

            def close(self):
                pass

        article = app_module.structured_blog_article_for_slug("2026-man-age-guide")
        post = SimpleNamespace(
            id=306,
            title=article["title"],
            slug=article["slug"],
            excerpt=article["hero_summary"],
            cover_image_url=article["thumbnail"],
            content_html=render_article_content_html(article),
            published_at=None,
            created_at=datetime(2026, 7, 4, 12, 0),
            updated_at=datetime(2026, 7, 4, 12, 0),
            status="draft",
            sources=[],
        )

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(post)):
            response = app.test_client().get(f"/blog/{article['slug']}")

        self.assertEqual(response.status_code, 404)

    def test_home_page_links_all_life_hubs(self):
        client = app.test_client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("8개의 생활 영역", html)
        self.assertEqual(8, html.count('class="home-life-hub-card'))
        for hub in HUB_PAGES:
            self.assertIn(f'href="{hub["path"]}"', html)
        self.assertNotIn("표·비교 모음", html)

    def test_home_page_renders_coupang_side_rails_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "COUPANG_PARTNERS_ENABLED", True
        ):
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertEqual(2, html.count('class="home-coupang-rail'))
        self.assertEqual(10, html.count('class="home-coupang-banner"'))
        self.assertEqual(1, html.count('class="coupang-mobile-banner"'))
        self.assertIn('href="https://link.coupang.com/a/ffBvZNWzEi"', html)
        self.assertIn("banners/1002561?trackingCode=AF6844979", html)
        for url in [
            "https://link.coupang.com/a/ffu5nazk5Y",
            "https://link.coupang.com/a/ffvasJKyY0",
            "https://link.coupang.com/a/ffvcORZcqa",
            "https://link.coupang.com/a/ffvdyD0ufk",
            "https://link.coupang.com/a/ffvedsU0Zg",
            "https://link.coupang.com/a/ffve5qgzEO",
            "https://link.coupang.com/a/ffvf0tCcQ8",
            "https://link.coupang.com/a/ffvgxQMD5U",
            "https://link.coupang.com/a/ffvhsWlA5I",
            "https://link.coupang.com/a/ffvjmC9bKS",
        ]:
            self.assertIn(f'href="{url}"', html)
        self.assertIn("쿠팡 파트너스 활동으로 일정액의 수수료를 제공받습니다.", html)
        self.assertLess(html.index('class="hero-band'), html.index('<footer class="footer">'))

    def test_calculator_pages_render_coupang_side_rails_when_enabled(self):
        client = app.test_client()
        calculator_paths = [
            "/age",
            "/birth-year-age-table",
            "/school-grade-calculator",
            "/school-entry-year-table",
            "/age-gap-calculator",
            "/100-day-calculator",
            "/baby-months-table",
            "/annual-age-calculator",
            "/age-comparison-table",
            "/grade-age-table",
            "/pet-age-table",
            "/pet-months-table",
            "/grade-birth-year-table",
            "/birth-year-zodiac-table",
            "/college-entry-year-calculator",
            "/birthday-dday-calculator",
            "/dog",
            "/cat",
            "/baby-months",
            "/d-day",
            "/parent-child",
        ]

        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "COUPANG_PARTNERS_ENABLED", True
        ):
            for path in calculator_paths:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertEqual(2, html.count('class="home-coupang-rail'))
                    self.assertEqual(10, html.count('class="home-coupang-banner"'))
                    self.assertIn("coupang-side-rail-left", html)
                    self.assertIn("coupang-side-rail-right", html)
                    self.assertEqual(1, html.count('class="coupang-mobile-banner"'))

    def test_age_page_renders_info_coupang_promotions_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "COUPANG_PARTNERS_ENABLED", True
        ):
            response = client.get("/age")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('class="info-coupang-promotions"', html)
        self.assertEqual(3, html.count('class="info-coupang-promo"'))
        for href in [
            "https://link.coupang.com/a/fhcWUfwBBQ",
            "https://link.coupang.com/a/fhcYeZ1ti8",
            "https://link.coupang.com/a/fhcYPGOPIa",
        ]:
            self.assertIn(f'href="{href}"', html)
        self.assertNotIn("data-event-promo-mobile-slot", html)
        self.assertNotIn("coupang-event-promotions.js", html)
        self.assertLess(html.index('class="hero-band utility-hero"'), html.index('class="info-coupang-promotions"'))
        self.assertLess(html.index('class="info-coupang-promotions"'), html.index('class="coupang-mobile-banner"'))

    def test_other_pages_render_event_promotions_after_hero_band(self):
        client = app.test_client()

        for path in ["/annual-age-calculator"]:
            with self.subTest(path=path), mock.patch.object(
                app_module, "ADSENSE_REVIEW_MODE", False
            ), mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
                response = client.get(path)

            self.assertEqual(response.status_code, 200)
            html = response.get_data(as_text=True)
            self.assertIn('class="info-coupang-promotions"', html)
            self.assertEqual(3, html.count('class="info-coupang-promo"'))
            self.assertNotIn("data-event-promo-mobile-slot", html)
            self.assertNotIn("coupang-event-promotions.js", html)
            self.assertLess(html.index('class="hero-band'), html.index('class="info-coupang-promotions"'))
            if 'class="coupang-mobile-banner"' in html and path != "/blog":
                self.assertLess(html.index('class="info-coupang-promotions"'), html.index('class="coupang-mobile-banner"'))

    def test_event_promotions_are_loaded_from_editable_data_file(self):
        promotions = app_module._active_coupang_event_promotions()

        self.assertEqual(3, len(promotions))
        self.assertEqual("https://link.coupang.com/a/fhcWUfwBBQ", promotions[0]["url"])
        self.assertEqual(
            "https://img3c.coupangcdn.com/image/affiliate/event/promotion/2026/07/09/b309e489be3a00f20124db161debbeda.png",
            promotions[0]["image_url"],
        )

    def test_mobile_coupang_banner_uses_hub_specific_links(self):
        client = app.test_client()
        expected_by_path = {
            "/baby-months": ("https://link.coupang.com/a/ffBqbNUILI", "banners/997624?trackingCode=AF6844979"),
            "/baby-months-table": ("https://link.coupang.com/a/ffBqbNUILI", "banners/997624?trackingCode=AF6844979"),
            "/parent-child": ("https://link.coupang.com/a/ffBqbNUILI", "banners/997624?trackingCode=AF6844979"),
            "/age-gap-calculator": ("https://link.coupang.com/a/ffBqbNUILI", "banners/997624?trackingCode=AF6844979"),
            "/dog": ("https://link.coupang.com/a/ffBtTssmtg", "banners/997607?trackingCode=AF6844979"),
            "/cat": ("https://link.coupang.com/a/ffBtTssmtg", "banners/997607?trackingCode=AF6844979"),
            "/pet-age-table": ("https://link.coupang.com/a/ffBtTssmtg", "banners/997607?trackingCode=AF6844979"),
            "/pet-months-table": ("https://link.coupang.com/a/ffBtTssmtg", "banners/997607?trackingCode=AF6844979"),
            "/age": ("https://link.coupang.com/a/ffBvZNWzEi", "banners/1002561?trackingCode=AF6844979"),
            "/school-grade-calculator": ("https://link.coupang.com/a/ffBvZNWzEi", "banners/1002561?trackingCode=AF6844979"),
            "/d-day": ("https://link.coupang.com/a/ffBvZNWzEi", "banners/1002561?trackingCode=AF6844979"),
        }

        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "COUPANG_PARTNERS_ENABLED", True
        ):
            for path, (href, banner_src) in expected_by_path.items():
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertIn('class="coupang-mobile-banner"', html)
                    self.assertIn(f'href="{href}"', html)
                    self.assertIn(banner_src, html)

    def test_mobile_coupang_banner_css_is_mobile_sized(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")
        mobile_css = re.search(r"@media\s*\(max-width:\s*760px\)\s*\{(?P<body>.*)\n\}", css, re.DOTALL)

        self.assertRegex(css, r"\.coupang-mobile-banner\s*\{[^}]*display:\s*none;")
        self.assertIsNotNone(mobile_css)
        body = mobile_css.group("body")
        self.assertRegex(body, r"\.coupang-mobile-banner\s*\{[^}]*display:\s*grid;")
        self.assertRegex(body, r"\.coupang-mobile-banner\s*\{[^}]*width:\s*min\(100%,\s*300px\);")
        self.assertRegex(body, r"\.coupang-mobile-banner-link,\s*\.coupang-mobile-banner-link img\s*\{[^}]*width:\s*min\(100%,\s*300px\);")

    def test_home_coupang_rails_are_positioned_in_side_columns(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")
        rail_rule = re.search(r"body:not\(\.snake-page\)\s+\.coupang-side-rail\s*\{(?P<body>[^}]*)\}", css)

        self.assertIsNotNone(rail_rule)
        self.assertNotIn("overflow-y", rail_rule.group("body"))
        self.assertNotIn("max-height", rail_rule.group("body"))
        self.assertNotIn("position: sticky", rail_rule.group("body"))
        self.assertRegex(css, r"body:not\(\.snake-page\)\s+\.container\s*>\s*\.coupang-side-rail-left\s*\{[^}]*grid-column:\s*1;")
        self.assertRegex(css, r"body:not\(\.snake-page\)\s+\.container\s*>\s*\.coupang-side-rail-right\s*\{[^}]*grid-column:\s*3;")

    def test_header_excludes_global_coupang_ad_aside(self):
        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True), app.test_request_context("/"):
            html = render_template("partials/header.html")

        self.assertNotIn('class="coupang-ad-aside"', html)
        self.assertNotIn("widgets.html?id=997602&template=carousel&trackingCode=AF6844979", html)
        self.assertNotIn("https://link.coupang.com/a/eDtbnycaRg", html)
        self.assertNotIn("https://link.coupang.com/a/eDtcE5ScoK", html)

    def test_coupang_ad_aside_does_not_precede_main_content_on_mobile_flow(self):
        client = app.test_client()

        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False), mock.patch.object(
            app_module, "COUPANG_PARTNERS_ENABLED", True
        ):
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn('class="coupang-ad-aside"', html)
        self.assertLess(html.index('class="hero-band'), html.index('class="home-coupang-rail'))
        self.assertIn('class="hero-band', html)

    def test_footer_is_trimmed_to_policy_links(self):
        with app.test_request_context("/"):
            html = render_template("partials/footer.html")
        footer_html = re.search(r'<footer class="footer".*?</footer>', html, re.S).group(0)

        self.assertNotIn("All rights reserved.", footer_html)
        self.assertNotIn("coupang-ad-aside", footer_html)
        self.assertIn('href="/contact"', footer_html)
        self.assertIn('href="/references"', footer_html)
        self.assertIn('href="/about"', footer_html)
        self.assertIn('href="/privacy"', footer_html)
        self.assertIn('href="/terms"', footer_html)
        self.assertNotIn('href="/birth-year-age-table"', footer_html)
        self.assertNotIn('href="/school-grade-calculator"', footer_html)
        self.assertNotIn('href="/school-entry-year-table"', footer_html)
        self.assertNotIn('href="/age-gap-calculator"', footer_html)
        self.assertNotIn('href="/100-day-calculator"', footer_html)
        self.assertNotIn('href="/baby-months-table"', footer_html)
        self.assertNotIn('href="/annual-age-calculator"', footer_html)
        self.assertNotIn('href="/age-comparison-table"', footer_html)
        self.assertNotIn('href="/grade-age-table"', footer_html)
        self.assertNotIn('href="/pet-age-table"', footer_html)
        self.assertNotIn('href="/korean-age-guide"', footer_html)
        self.assertNotIn('href="/pet-months-table"', footer_html)
        self.assertNotIn('href="/grade-birth-year-table"', footer_html)
        self.assertNotIn('href="/birth-year-zodiac-table"', footer_html)
        self.assertNotIn('href="/college-entry-year-calculator"', footer_html)
        self.assertNotIn('href="/birthday-dday-calculator"', footer_html)

    def test_about_links_to_contact_page(self):
        client = app.test_client()
        response = client.get("/about")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('href="/contact"', html)

    def test_guide_page_uses_natural_intro_copy(self):
        client = app.test_client()
        response = client.get("/guide")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("헷갈리기 쉬운 만나이, 연나이, 한국식 나이의 차이를 차근차근 정리했습니다.", html)
        self.assertNotIn("정의와 계산 방식을 한눈에 정리했습니다.", html)

    def test_faq_page_uses_plain_korean_heading(self):
        client = app.test_client()
        response = client.get("/faq")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("<h1>자주 묻는 질문</h1>", html)
        self.assertNotIn("자주 묻는 질문(FAQ)", html)

    def test_privacy_page_uses_standard_korean_spacing(self):
        client = app.test_client()
        response = client.get("/privacy")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("<h1>개인정보처리방침</h1>", html)
        self.assertNotIn("개인정보 처리 방침", html)

    def test_privacy_page_discloses_page_feedback_storage(self):
        client = app.test_client()
        response = client.get("/privacy")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("페이지 품질 개선", html)
        self.assertIn("페이지 경로", html)
        self.assertIn("선택한 피드백", html)
        self.assertIn("브라우저 저장소", html)

    def test_terms_page_uses_clearer_intro_copy(self):
        client = app.test_client()
        response = client.get("/terms")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("서비스를 이용할 때 알아두셔야 할 기준과 책임 범위를 안내합니다.", html)
        self.assertNotIn("서비스 제공자와 이용자 간의 권리, 의무 및 책임사항을 규정합니다.", html)

    def test_dog_page_uses_natural_intro_copy(self):
        client = app.test_client()
        response = client.get("/dog")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("반려견의 실제 나이를 사람 나이로 환산해 보여드립니다.", html)
        self.assertNotIn("반려견 나이를 사람 나이로 환산해 보세요", html)

    def test_dog_page_uses_distinct_size_icons(self):
        client = app.test_client()
        response = client.get("/dog")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for size in ("small", "medium", "large", "giant"):
            self.assertIn(f"dog-size-icon dog-size-icon-{size}", html)

    def test_cat_page_uses_natural_intro_copy(self):
        client = app.test_client()
        response = client.get("/cat")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("반려묘의 실제 나이를 사람 나이로 환산해 보여드립니다.", html)
        self.assertNotIn("반려묘 나이를 사람 나이로 환산해 보세요", html)

    def test_baby_months_page_uses_clearer_intro_copy(self):
        client = app.test_client()
        response = client.get("/baby-months")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("출생일을 입력하면 현재 아이 개월 수와 아기 월령이 바로 나옵니다.", html)
        self.assertNotIn("“우리 아이는 몇 개월?”", html)

    def test_d_day_page_removes_english_labels(self):
        client = app.test_client()
        response = client.get("/d-day")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        for phrase in ["Date Counter", "Today", "How It Works", "Use Cases"]:
            self.assertNotIn(phrase, html)
        self.assertIn("날짜 계산 안내", html)
        self.assertIn("오늘인 일정도 바로 확인", html)

    def test_parent_child_page_uses_natural_intro_copy(self):
        client = app.test_client()
        response = client.get("/parent-child")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("부모와 자녀의 나이 차이와 주요 시점을 함께 살펴볼 수 있습니다.", html)
        self.assertNotIn("부모(부/모)와 자녀의 나이 관계를 계산합니다", html)

    def test_minigames_are_marked_noindex(self):
        client = app.test_client()

        for path in ["/minigames", "/minigames/guess", "/minigames/snake"]:
            response = client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers.get("X-Robots-Tag"), "noindex, nofollow")

    def test_core_pages_are_not_marked_noindex(self):
        client = app.test_client()
        response = client.get("/age")

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.headers.get("X-Robots-Tag"))

    def test_dynamic_sitemap_excludes_minigames(self):
        client = app.test_client()
        body = "\n".join(_sitemap_leaf_locations(client))
        self.assertIn("https://agecalc.cloud/age", body)
        self.assertIn("https://agecalc.cloud/contact", body)
        self.assertIn("https://agecalc.cloud/references", body)
        self.assertIn("https://agecalc.cloud/birth-year-age-table", body)
        self.assertIn("https://agecalc.cloud/school-grade-calculator", body)
        self.assertIn("https://agecalc.cloud/school-entry-year-table", body)
        self.assertIn("https://agecalc.cloud/age-gap-calculator", body)
        self.assertIn("https://agecalc.cloud/100-day-calculator", body)
        self.assertIn("https://agecalc.cloud/baby-months-table", body)
        self.assertIn("https://agecalc.cloud/annual-age-calculator", body)
        self.assertIn("https://agecalc.cloud/age-comparison-table", body)
        self.assertIn("https://agecalc.cloud/grade-age-table", body)
        self.assertIn("https://agecalc.cloud/pet-age-table", body)
        self.assertIn("https://agecalc.cloud/korean-age-guide", body)
        self.assertIn("https://agecalc.cloud/pet-months-table", body)
        self.assertIn("https://agecalc.cloud/grade-birth-year-table", body)
        self.assertIn("https://agecalc.cloud/birth-year-zodiac-table", body)
        self.assertIn("https://agecalc.cloud/college-entry-year-calculator", body)
        self.assertIn("https://agecalc.cloud/birthday-dday-calculator", body)
        self.assertNotIn("/minigames", body)

    def test_sitemap_index_groups_public_pages(self):
        client = app.test_client()
        index_response = client.get("/sitemap.xml")

        self.assertEqual(index_response.status_code, 200)
        index_xml = index_response.get_data(as_text=True)
        self.assertIn("<sitemapindex", index_xml)
        child_locations = re.findall(r"<loc>(.*?)</loc>", index_xml)
        expected_children = {
            "https://agecalc.cloud/sitemaps/core.xml",
            "https://agecalc.cloud/sitemaps/age.xml",
            "https://agecalc.cloud/sitemaps/family.xml",
            "https://agecalc.cloud/sitemaps/education.xml",
            "https://agecalc.cloud/sitemaps/anniversary.xml",
            "https://agecalc.cloud/sitemaps/pets.xml",
            "https://agecalc.cloud/sitemaps/guides.xml",
        }
        self.assertEqual(expected_children, set(child_locations))

        public_locations = []
        for location in child_locations:
            path = location.removeprefix("https://agecalc.cloud")
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 200)
                xml = response.get_data(as_text=True)
                self.assertIn("<urlset", xml)
                self.assertEqual(xml.count("<loc>"), xml.count("<lastmod>"))
                public_locations.extend(re.findall(r"<loc>(.*?)</loc>", xml))

        self.assertEqual(46, len(public_locations))
        self.assertEqual(46, len(set(public_locations)))
        for forbidden in ("?", "#", "/minigames", "/blog/drafts", "/blog/review"):
            self.assertNotIn(forbidden, "\n".join(public_locations))

    def test_dynamic_sitemap_includes_static_guides_and_excludes_blog_by_default(self):
        client = app.test_client()
        guide_content_policy = getattr(guide_pages_module, "GUIDE_CONTENT_POLICY", {})
        body = "\n".join(_sitemap_leaf_locations(client))
        for slug in GUIDE_SLUGS:
            guide_url = f"https://agecalc.cloud/guides/{slug}"
            if guide_content_policy.get(slug, {}).get("indexable", True):
                self.assertIn(guide_url, body)
            else:
                self.assertNotIn(guide_url, body)
        self.assertNotIn("https://agecalc.cloud/blog", body)
        self.assertNotIn("https://agecalc.cloud/blog/2026-man-age-guide", body)

    def test_dynamic_sitemap_excludes_blog_when_public_blog_is_not_indexable(self):
        client = app.test_client()

        with mock.patch.object(app_module, "_is_blog_public_indexable", return_value=False):
            body = "\n".join(_sitemap_leaf_locations(client))

        self.assertNotIn("https://agecalc.cloud/blog", body)

    def test_sitemap_is_served_only_from_dynamic_route(self):
        self.assertFalse(Path("static/sitemap.xml").exists())
        self.assertFalse(Path("generate_sitemap.py").exists())

    def test_default_og_image_asset_exists(self):
        self.assertTrue(Path("static/images/og-image.png").exists())

    def test_navigation_css_promotes_header_above_sections(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertIn(".site-header {", css)
        self.assertIn("position: relative;", css)
        self.assertIn("z-index: 80;", css)
        self.assertIn(".mega-menu-panel {", css)
        self.assertIn("z-index: 90;", css)

    def test_desktop_navigation_does_not_expand_document_width(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertRegex(
            css,
            r"\.life-hub-mega-panel\s*\{[^}]*left:\s*auto;[^}]*right:\s*0;[^}]*transform:\s*translateY\(8px\);",
        )
        self.assertRegex(
            css,
            r"\.mega-nav-item:hover\s+\.life-hub-mega-panel,[^{]*\{[^}]*transform:\s*translateY\(0\);",
        )
        self.assertRegex(
            css,
            r"\.breadcrumbs\s*\{[^}]*width:\s*min\(100%,\s*1280px\);",
        )
        self.assertRegex(
            css,
            r"\.site-header,\s*\.home-page\s+\.site-header\s*\{[^}]*"
            r"width:\s*100%;[^}]*margin-left:\s*0;[^}]*margin-right:\s*0;",
        )

    def test_home_hub_typography_has_explicit_scale_rules(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertIn(".section-heading h2 {", css)
        self.assertIn(".hub-card strong {", css)
        self.assertIn(".hub-more-label {", css)
        self.assertRegex(css, r"\.age-hub-copy\s+h1\s*\{[^}]*font-size:\s*clamp\(3\.2rem,\s*4\.4vw,\s*5\.9rem\);")

    def test_mobile_hero_metrics_do_not_force_horizontal_overflow(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")
        mobile_css = re.search(r"@media\s*\(max-width:\s*760px\)\s*\{(?P<body>.*)\n\}", css, re.DOTALL)

        self.assertIsNotNone(mobile_css)
        body = mobile_css.group("body")
        self.assertRegex(
            body,
            r"body:not\(\.home-page\)\s+\.hero-metrics\s*\{[^}]*grid-template-columns:\s*minmax\(0,\s*1fr\);",
        )
        self.assertRegex(
            body,
            r"body:not\(\.home-page\)\s+\.hero-metrics\s*\{[^}]*width:\s*min\(100%,\s*180px\);",
        )
        self.assertRegex(
            body,
            r"body:not\(\.home-page\)\s+\.hero-metrics\s*\{[^}]*justify-self:\s*end;",
        )
        self.assertRegex(
            body,
            r"body:not\(\.home-page\)\s+\.metric-value,\s*body:not\(\.home-page\)\s+\.metric-label\s*\{[^}]*white-space:\s*normal;",
        )
        self.assertRegex(
            body,
            r"body:not\(\.home-page\)\s+\.metric-value,\s*body:not\(\.home-page\)\s+\.metric-label\s*\{[^}]*overflow-wrap:\s*anywhere;",
        )

    def test_footer_link_styles_are_scoped_to_footer_only(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertIn(".footer .footer-links a {", css)
        self.assertIn(".article-links a {", css)

    def test_robots_txt_allows_adsense_crawlers(self):
        body = Path("static/robots.txt").read_text(encoding="utf-8")

        self.assertIn("User-agent: Mediapartners-Google", body)
        self.assertIn("User-agent: Google-Display-Ads-Bot", body)
        self.assertIn("Allow: /ads.txt", body)
        self.assertIn("Sitemap: https://agecalc.cloud/sitemap.xml", body)

    def test_tracking_loader_does_not_insert_second_adsense_script(self):
        body = Path("static/js/analytics.js").read_text(encoding="utf-8")

        self.assertNotIn("pagead/js/adsbygoogle.js", body)
        self.assertNotIn("ADSENSE_SCRIPT_ID", body)

    def test_nginx_redirects_www_to_canonical_domain(self):
        conf = Path("nginx/agecalc.conf").read_text(encoding="utf-8")

        self.assertIn("server_name www.agecalc.cloud;", conf)
        self.assertIn("return 301 https://agecalc.cloud$uri;", conf)
        self.assertIn("limit_req zone=agecalc_blog_login", conf)

    def test_content_security_policy_allows_coupang_affiliate_assets(self):
        client = app.test_client()
        with mock.patch.object(app_module, "ADSENSE_REVIEW_MODE", False):
            response = client.get("/dog")

        self.assertEqual(response.status_code, 200)
        csp = response.headers.get("Content-Security-Policy", "")
        self.assertIn("https://ads-partners.coupang.com", csp)
        self.assertIn("https://*.coupangcdn.com", csp)
        self.assertIn("frame-src", csp)
        self.assertIn("https://ep2.adtrafficquality.google", csp)


if __name__ == "__main__":
    unittest.main()
