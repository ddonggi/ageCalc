import re
import unittest
from datetime import date, datetime
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

from flask import render_template, url_for
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app as app_module
import content.guide_pages as guide_pages_module
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


class PublicPageTests(unittest.TestCase):
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

    def test_birth_year_age_table_page_is_public(self):
        client = app.test_client()
        response = client.get("/birth-year-age-table")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("출생년도별 나이표", html)
        self.assertIn("몇년생 몇살", html)
        self.assertIn("출생년도만 선택하면", html)
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
        self.assertIn("출생년도만 선택하면", html)
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

    def test_hundred_day_calculator_highlights_selected_date(self):
        client = app.test_client()
        response = client.get("/100-day-calculator?year=2026&month=1&day=1")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("2026.01.01", html)
        self.assertIn("2026.04.10", html)
        self.assertIn("선택한 시작일", html)

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

    def test_college_entry_year_calculator_targets_top_queries(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("26학번 몇년생", html)
        self.assertIn("22학번 나이", html)
        self.assertIn("09학번 몇살", html)
        self.assertIn("26학번 나이", html)

    def test_annual_age_calculator_page_is_public(self):
        client = app.test_client()
        response = client.get("/annual-age-calculator")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("연나이 계산기", html)
        self.assertIn("생일과 관계없이", html)
        self.assertIn("올해 연나이", html)
        self.assertIn("만나이와의 차이", html)

    def test_annual_age_calculator_highlights_selected_date(self):
        client = app.test_client()
        response = client.get("/annual-age-calculator?year=1992&month=10&day=2")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 생년월일", html)
        self.assertIn("1992.10.02", html)
        self.assertIn("34세", html)

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
        self.assertIn("출생연도별 띠표", html)
        self.assertIn("12간지", html)
        self.assertIn("띠", html)
        self.assertIn("말띠", html)

    def test_birth_year_zodiac_table_highlights_selected_year(self):
        client = app.test_client()
        response = client.get("/birth-year-zodiac-table?year=1990")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 출생연도", html)
        self.assertIn("1990년생", html)
        self.assertIn("말띠", html)

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

    def test_life_hub_pages_are_public(self):
        client = app.test_client()
        expected_hubs = {
            "age": "나이 계산",
            "family": "가족·육아",
            "education": "학교·교육",
            "anniversary": "생일·기념일",
            "retirement": "은퇴·노후",
            "health": "건강·검진",
            "pets": "반려동물",
            "generations": "세대·추억",
        }

        for key, title in expected_hubs.items():
            with self.subTest(key=key):
                response = client.get(f"/{key}/")

                self.assertEqual(response.status_code, 200)
                html = response.get_data(as_text=True)
                self.assertIn(f"<h1>{title}</h1>", html)
                self.assertIn(
                    f'<link rel="canonical" href="https://agecalc.cloud/{key}/" />',
                    html,
                )
                self.assertIn('name="description"', html)
                self.assertIn("대표 도구", html)
                self.assertIn("더 살펴보기", html)
                self.assertIn("운영 기준", html)
                self.assertIn("google-adsense-account", html)
                self.assertNotIn("noindex", html)

    def test_life_hubs_are_added_to_the_public_sitemap(self):
        locations = _sitemap_leaf_locations(app.test_client())
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
            self.assertIn(f"https://agecalc.cloud/{key}/", locations)
        self.assertEqual(56, len(locations))

    def test_life_hubs_render_direct_answers_and_contextual_paths(self):
        client = app.test_client()

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
            with self.subTest(key=key):
                html = client.get(f"/{key}/").get_data(as_text=True)

                self.assertRegex(html, r'class="[^"]*\bdirect-answer\b[^"]*"')
                self.assertIn('class="related-paths"', html)

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
                "출생연도만 알면 연나이와 만나이 범위를 빠르게 확인할 수 있습니다",
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
                "학년을 선택하면 그 학년의 일반적인 나이 범위를 확인할 수 있습니다",
                "학년별 나이 해석",
                "같은 학년의 나이가 다른 이유",
                "조기입학·입학유예·해외 학제",
            ),
            "/grade-birth-year-table": (
                "학년을 선택하면 일반적으로 해당하는 출생연도를 확인할 수 있습니다",
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

    def test_public_sitemap_keeps_baseline_urls_and_adds_life_hubs(self):
        client = app.test_client()
        locations = _sitemap_leaf_locations(client)
        joined_locations = "\n".join(locations)

        self.assertEqual(56, len(locations))
        self.assertNotIn("/minigames", joined_locations)
        self.assertNotIn("/blog/drafts", joined_locations)
        self.assertNotIn("/blog/review", joined_locations)
        self.assertIn("https://agecalc.cloud/blog", locations)
        self.assertIn("https://agecalc.cloud/blog/2026-man-age-guide", locations)

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
        class FakeQuery:
            def __init__(self, post):
                self.post = post

            def filter(self, *args, **kwargs):
                return self

            def count(self):
                return 1

            def first(self):
                return self.post

        class FakeSession:
            def __init__(self, post):
                self.post = post

            def query(self, model):
                return FakeQuery(self.post)

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
        self.assertEqual("published", payload["status"])
        self.assertIn("2026년 만나이 계산 기준 총정리", payload["title"])
        self.assertIn("<h2>만나이는 무엇을 기준으로 계산하나</h2>", payload["content_html"])

    def test_seed_public_blog_posts_upsert_preserves_existing_published_at(self):
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

        self.assertEqual(published_at, post.published_at)

        verify_session = Session()
        stored = verify_session.query(GeneratedPost).filter(GeneratedPost.slug == "2026-man-age-guide").first()
        verify_session.close()

        self.assertIsNotNone(stored)
        self.assertEqual(published_at, stored.published_at)
        self.assertIn("2026년 만나이 계산 기준 총정리", stored.title)

    def test_seed_public_blog_posts_main_seeds_curated_slugs(self):
        from scripts import seed_public_blog_posts

        with mock.patch.object(seed_public_blog_posts, "upsert_seed_post") as upsert_seed_post:
            seeded = seed_public_blog_posts.main()

        self.assertEqual(
            [
                "2026-man-age-guide",
                "birth-year-age-interpretation",
                "early-birth-school-grade-guide",
                "baby-months-calculation-guide",
                "parent-child-age-gap-guide",
            ],
            seeded,
        )
        self.assertEqual(5, upsert_seed_post.call_count)

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

        posts = [
            SimpleNamespace(
                id=index,
                slug=slug,
                title=slug,
                excerpt="요약",
                cover_image_url=None,
                published_at=datetime(2026, 6, 26, 12, 0),
                created_at=datetime(2026, 6, 26, 12, 0),
                updated_at=datetime(2026, 6, 26, 12, 0),
                status="published",
                sources=[],
            )
            for index, slug in enumerate(
                [
                    "2026-man-age-guide",
                    "birth-year-age-interpretation",
                    "early-birth-school-grade-guide",
                    "baby-months-calculation-guide",
                    "parent-child-age-gap-guide",
                ],
                start=1,
            )
        ]

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
            self.assertIn(f'data-hub-key="{key}"', html)
            self.assertIn(f'href="/{key}/"', html)
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

        post = SimpleNamespace(
            id=1,
            title="승인 전 숨김 글",
            slug="2026-man-age-guide",
            excerpt="요약입니다.",
            cover_image_url=None,
            content_html="<h2>본문</h2><p>AgeCalc 계산기 안내입니다.</p>",
            published_at=None,
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

        curated_post = SimpleNamespace(
            id=1,
            slug="2026-man-age-guide",
            title="2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
            excerpt="요약",
            cover_image_url=None,
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

    def test_blog_detail_returns_404_for_legacy_published_post_outside_curated_set(self):
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

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(legacy_post)):
            response = app.test_client().get("/blog/legacy-general-post")

        self.assertEqual(response.status_code, 404)

    def test_guides_sitemap_excludes_legacy_published_blog_posts(self):
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

        curated_post = SimpleNamespace(
            slug="2026-man-age-guide",
            published_at=datetime(2026, 6, 26, 12, 0),
            created_at=datetime(2026, 6, 26, 12, 0),
            updated_at=datetime(2026, 6, 26, 12, 0),
            status="published",
        )
        legacy_post = SimpleNamespace(
            slug="legacy-general-post",
            published_at=datetime(2026, 6, 20, 12, 0),
            created_at=datetime(2026, 6, 20, 12, 0),
            updated_at=datetime(2026, 6, 20, 12, 0),
            status="published",
        )

        with mock.patch.object(app_module, "BLOG_PUBLIC_INDEXING_ENABLED", True), mock.patch.object(
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
            response = app.test_client().post("/blog/review/1/approve?token=test")

        self.assertEqual(response.status_code, 400)
        self.assertEqual("needs_review", post.status)
        self.assertFalse(fake_session.committed)
        self.assertIn("공개할 수 없습니다", response.get_data(as_text=True))

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
            cover_image_url="/static/generated/draft-post-cover.png",
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

        with mock.patch.object(app_module, "SessionLocal", return_value=fake_session), mock.patch.object(
            app_module, "_published_blog_count", return_value=0
        ):
            response = client.post("/blog/drafts/draft-post/publish")

        self.assertEqual(response.status_code, 302)
        self.assertEqual("published", post.status)
        self.assertIsNotNone(post.published_at)
        self.assertTrue(fake_session.committed)
        self.assertIn("/blog/draft-post", response.headers["Location"])

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

        with mock.patch.object(app_module, "SessionLocal", return_value=fake_session), mock.patch.object(
            app_module, "_published_blog_count", return_value=0
        ):
            response = client.post("/blog/drafts/draft-post/publish")

        self.assertEqual(response.status_code, 400)
        self.assertEqual("draft", post.status)
        self.assertFalse(fake_session.committed)
        self.assertIn("대표 이미지가 없습니다", response.get_data(as_text=True))

    def test_home_page_links_all_life_hubs(self):
        client = app.test_client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("8개의 생활 영역", html)
        self.assertEqual(8, html.count('class="home-life-hub-card'))
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
            self.assertIn(f'href="/{key}/"', html)
        self.assertNotIn("표·비교 모음", html)

    def test_header_excludes_global_coupang_ad_aside(self):
        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True), app.test_request_context("/"):
            html = render_template("partials/header.html")

        self.assertNotIn('class="coupang-ad-aside"', html)
        self.assertNotIn("widgets.html?id=997602&template=carousel&trackingCode=AF6844979", html)
        self.assertNotIn("https://link.coupang.com/a/eDtbnycaRg", html)
        self.assertNotIn("https://link.coupang.com/a/eDtcE5ScoK", html)

    def test_coupang_ad_aside_does_not_precede_main_content_on_mobile_flow(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertNotIn('class="coupang-ad-aside"', html)
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
        self.assertIn("반려견 나이를 사람 기준으로 얼마나 되는지 쉽게 확인할 수 있습니다.", html)
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
        self.assertIn("반려묘 나이를 사람 기준으로 어느 정도인지 바로 확인할 수 있습니다.", html)
        self.assertNotIn("반려묘 나이를 사람 나이로 환산해 보세요", html)

    def test_baby_months_page_uses_clearer_intro_copy(self):
        client = app.test_client()
        response = client.get("/baby-months")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("출생일만 입력하면 아이 개월수와 아기 월령을 바로 확인할 수 있습니다.", html)
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
            "https://agecalc.cloud/sitemaps/retirement.xml",
            "https://agecalc.cloud/sitemaps/health.xml",
            "https://agecalc.cloud/sitemaps/pets.xml",
            "https://agecalc.cloud/sitemaps/generations.xml",
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

        self.assertEqual(56, len(public_locations))
        self.assertEqual(56, len(set(public_locations)))
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
        self.assertIn("https://agecalc.cloud/blog", body)
        self.assertIn("https://agecalc.cloud/blog/2026-man-age-guide", body)

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

    def test_home_hub_typography_has_explicit_scale_rules(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertIn(".section-heading h2 {", css)
        self.assertIn(".hub-card strong {", css)
        self.assertIn(".hub-more-label {", css)

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
        self.assertIn("return 301 https://agecalc.cloud$request_uri;", conf)

    def test_content_security_policy_allows_coupang_affiliate_assets(self):
        client = app.test_client()
        response = client.get("/dog")

        self.assertEqual(response.status_code, 200)
        csp = response.headers.get("Content-Security-Policy", "")
        self.assertIn("https://ads-partners.coupang.com", csp)
        self.assertIn("https://image15.coupangcdn.com", csp)
        self.assertIn("https://image8.coupangcdn.com", csp)
        self.assertIn("https://image9.coupangcdn.com", csp)
        self.assertIn("https://img1c.coupangcdn.com", csp)
        self.assertIn("https://image11.coupangcdn.com", csp)
        self.assertIn("https://image7.coupangcdn.com", csp)
        self.assertIn("https://image14.coupangcdn.com", csp)
        self.assertIn("https://image2.coupangcdn.com", csp)
        self.assertIn("https://img4c.coupangcdn.com", csp)
        self.assertIn("frame-src", csp)
        self.assertIn("https://ep2.adtrafficquality.google", csp)


if __name__ == "__main__":
    unittest.main()
