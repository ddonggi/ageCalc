import unittest
from datetime import date, datetime
from types import SimpleNamespace
from pathlib import Path
from unittest import mock

from flask import render_template, url_for

import app as app_module
from app import PUBLIC_SITEMAP_ENDPOINTS, app, _current_local_date
from content.guide_pages import GUIDE_CATEGORIES, GUIDE_SLUGS
from models.blog_models import PageFeedback


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

    def test_baby_months_table_highlights_selected_months(self):
        client = app.test_client()
        response = client.get("/baby-months-table?months=12")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("선택한 월령", html)
        self.assertIn("12개월", html)
        self.assertIn("1년 0개월", html)

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
        self.assertIn("대학교 입학년도 계산", html)
        self.assertIn("25학번은 보통 몇 년생", html)
        self.assertIn("학번별 나이표", html)
        self.assertIn("보통 출생연도", html)

    def test_college_entry_year_calculator_answers_class_year_queries(self):
        client = app.test_client()
        response = client.get("/college-entry-year-calculator?year=2026")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("26학번 몇년생", html)
        self.assertIn("26학번은 보통 2007년생", html)
        self.assertIn("2026학번 나이", html)
        self.assertIn("학번은 입학연도와 같은 뜻인가요?", html)
        self.assertIn("재수하면 학번과 출생연도가 달라지나요?", html)

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

    def test_public_sitemap_has_fifty_indexable_urls_at_adsense_baseline(self):
        client = app.test_client()
        response = client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        xml = response.get_data(as_text=True)
        self.assertEqual(50, xml.count("<loc>"))
        self.assertNotIn("/minigames", xml)
        self.assertNotIn("/blog/drafts", xml)
        self.assertNotIn("/blog/review", xml)
        self.assertNotIn("<loc>https://agecalc.cloud/blog</loc>", xml)

    def test_static_guide_pages_are_public_with_adsense_code(self):
        client = app.test_client()

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
                self.assertIn(f'<link rel="canonical" href="https://agecalc.cloud/guides/{slug}" />', html)
                self.assertIn("<h1", html)
                self.assertIn('name="description"', html)
                self.assertIn("guide-category-label", html)
                self.assertIn("관련 계산기", html)
                self.assertIn("자주 묻는 질문", html)
                self.assertIn("google-adsense-account", html)
                self.assertNotIn("noindex", html)

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
        self.assertIn("대학교 입학년도 계산", college_response.get_data(as_text=True))

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

    def test_coupang_pet_affiliate_blocks_render_on_pet_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/cat", "/dog", "/pet-age-table", "/pet-months-table"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-pet", html)
                    self.assertIn('class="coupang-ad-aside"', html)

    def test_coupang_baby_promotion_blocks_render_on_baby_pages_when_enabled(self):
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
                    self.assertIn('class="coupang-ad-aside"', html)

    def test_coupang_age_affiliate_blocks_render_on_age_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/age", "/annual-age-calculator", "/age-comparison-table", "/birth-year-age-table"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-age", html)
                    self.assertIn('class="coupang-ad-aside"', html)

    def test_coupang_anniversary_affiliate_blocks_render_on_anniversary_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/d-day", "/birthday-dday-calculator"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-anniversary", html)
                    self.assertIn('class="coupang-ad-aside"', html)

    def test_coupang_student_affiliate_blocks_render_on_school_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/college-entry-year-calculator", "/school-entry-year-table", "/school-grade-calculator"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertNotIn("coupang-affiliate-block coupang-affiliate-student", html)
                    self.assertIn('class="coupang-ad-aside"', html)

    def test_coupang_affiliate_disclosure_uses_smaller_text(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertRegex(css, r"\.coupang-disclosure\s*\{[^}]*font-size:\s*0\.78rem;")

    def test_coupang_ad_aside_is_fixed_on_desktop_and_stacks_on_mobile(self):
        css = Path("static/css/style.css").read_text(encoding="utf-8")

        self.assertIn(".coupang-ad-rail {", css)
        self.assertIn("grid-template-columns: repeat(3, minmax(0, 200px));", css)
        self.assertIn("@media (min-width: 1180px)", css)
        self.assertIn("position: fixed;", css)
        self.assertIn("right: 18px;", css)
        self.assertIn("max-height: calc(100vh - 116px);", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertIn("grid-template-columns: 1fr;", css)
        self.assertIn("width: min(100%, 200px);", css)

    def test_coupang_ad_aside_renders_by_default_on_non_guide_pages_when_enabled(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            for path in ["/", "/age", "/birth-year-age-table", "/blog", "/minigames/2048"]:
                with self.subTest(path=path):
                    response = client.get(path)

                    self.assertEqual(response.status_code, 200)
                    html = response.get_data(as_text=True)
                    self.assertIn('class="coupang-ad-aside"', html)
                    self.assertIn(
                        'https://ads-partners.coupang.com/widgets.html?id=997602&template=carousel&trackingCode=AF6844979&subId=&width=140&height=640&tsource=',
                        html,
                    )
                    self.assertIn('width="200"', html)
                    self.assertIn('height="640"', html)
                    self.assertIn('frameborder="0"', html)
                    self.assertIn('scrolling="no"', html)
                    self.assertIn('referrerpolicy="unsafe-url"', html)
                    self.assertIn("browsingtopics", html)
                    self.assertIn("https://link.coupang.com/a/eDtbnycaRg", html)
                    self.assertIn("https://link.coupang.com/a/eDtcE5ScoK", html)

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
        self.assertIn('class="coupang-ad-aside"', html)

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

        self.assertIn("계산 결과를 이해하는 데 도움이 되는 배경 설명과 생활 정보를 글로 정리합니다.", html)
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

    def test_header_uses_category_navigation(self):
        with app.test_request_context("/"):
            html = render_template("partials/header.html", blog_public_indexable=True)

        self.assertIn("계산기", html)
        self.assertIn("표·비교", html)
        self.assertIn("안내", html)
        self.assertIn("블로그", html)
        self.assertIn("메뉴 열기", html)
        self.assertIn("mega-nav", html)
        self.assertIn("mega-menu-panel", html)
        self.assertNotIn('class="nav-links"', html)

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

    def test_blog_routes_are_noindex_and_without_adsense_by_default(self):
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
            slug="hidden-post",
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

        list_response = client.get("/blog")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.headers.get("X-Robots-Tag"), "noindex, nofollow")
        self.assertNotIn("google-adsense-account", list_response.get_data(as_text=True))

        with mock.patch.object(app_module, "SessionLocal", return_value=FakeSession(post)):
            detail_response = client.get("/blog/hidden-post")

        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(detail_response.headers.get("X-Robots-Tag"), "noindex, nofollow")
        detail_html = detail_response.get_data(as_text=True)
        self.assertIn('<meta name="robots" content="noindex,nofollow" />', detail_html)
        self.assertNotIn("google-adsense-account", detail_html)

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

    def test_home_page_uses_category_hub_sections(self):
        client = app.test_client()
        response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn("대표 계산기", html)
        self.assertIn("표·비교 모음", html)
        self.assertIn("기준과 안내", html)
        self.assertIn("카테고리별로 바로 이동", html)
        self.assertNotIn("빠른 시작", html)
        self.assertNotIn("정보 구성", html)

    def test_header_includes_coupang_ad_aside(self):
        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True), app.test_request_context("/"):
            html = render_template("partials/header.html")

        self.assertIn('class="coupang-ad-aside"', html)
        self.assertIn("widgets.html?id=997602&template=carousel&trackingCode=AF6844979", html)
        self.assertIn("https://link.coupang.com/a/eDtbnycaRg", html)
        self.assertIn("https://link.coupang.com/a/eDtcE5ScoK", html)
        self.assertIn('src="https://ads-partners.coupang.com/banners/997623?subId=&traceId=V0-301-5f4982b43e2b4522-I997623&w=200&h=200"', html)
        self.assertIn('src="https://ads-partners.coupang.com/banners/997606?subId=&traceId=V0-301-7e6e8eb8ddfa1bfb-I997606&w=200&h=200"', html)
        self.assertIn('alt=""', html)
        self.assertIn("이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.", html)

    def test_coupang_ad_aside_renders_before_main_content_on_mobile_flow(self):
        client = app.test_client()

        with mock.patch.object(app_module, "COUPANG_PARTNERS_ENABLED", True):
            response = client.get("/")

        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertLess(html.index('class="coupang-ad-aside"'), html.index('class="hero-band'))

    def test_footer_is_trimmed_to_policy_links(self):
        with app.test_request_context("/"):
            html = render_template("partials/footer.html")

        self.assertNotIn("All rights reserved.", html)
        self.assertNotIn("coupang-ad-aside", html)
        self.assertIn('href="/contact"', html)
        self.assertIn('href="/references"', html)
        self.assertIn('href="/about"', html)
        self.assertIn('href="/privacy"', html)
        self.assertIn('href="/terms"', html)
        self.assertNotIn('href="/birth-year-age-table"', html)
        self.assertNotIn('href="/school-grade-calculator"', html)
        self.assertNotIn('href="/school-entry-year-table"', html)
        self.assertNotIn('href="/age-gap-calculator"', html)
        self.assertNotIn('href="/100-day-calculator"', html)
        self.assertNotIn('href="/baby-months-table"', html)
        self.assertNotIn('href="/annual-age-calculator"', html)
        self.assertNotIn('href="/age-comparison-table"', html)
        self.assertNotIn('href="/grade-age-table"', html)
        self.assertNotIn('href="/pet-age-table"', html)
        self.assertNotIn('href="/korean-age-guide"', html)
        self.assertNotIn('href="/pet-months-table"', html)
        self.assertNotIn('href="/grade-birth-year-table"', html)
        self.assertNotIn('href="/birth-year-zodiac-table"', html)
        self.assertNotIn('href="/college-entry-year-calculator"', html)
        self.assertNotIn('href="/birthday-dday-calculator"', html)

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
        self.assertIn("출생일만 입력하면 현재 개월 수를 바로 확인할 수 있습니다.", html)
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
        response = client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
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

    def test_dynamic_sitemap_includes_static_guides_and_excludes_blog_by_default(self):
        client = app.test_client()
        response = client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
        for slug in GUIDE_SLUGS:
            self.assertIn(f"https://agecalc.cloud/guides/{slug}", body)
        self.assertNotIn("https://agecalc.cloud/blog", body)

    def test_dynamic_sitemap_excludes_blog_when_public_blog_is_not_indexable(self):
        client = app.test_client()

        with mock.patch.object(app_module, "_is_blog_public_indexable", return_value=False):
            response = client.get("/sitemap.xml")

        self.assertEqual(response.status_code, 200)
        body = response.get_data(as_text=True)
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
