import unittest
from types import SimpleNamespace

from scripts.adsense_blog_review import audit_post, audit_posts


def _source(url="https://example.com/story", attribution_text=None):
    return SimpleNamespace(
        source_name="Example",
        source_url=url,
        attribution_text=attribution_text,
    )


def _post(**overrides):
    defaults = {
        "id": 1,
        "slug": "test-post",
        "title": "아이 개월 수 계산과 발달 기준을 함께 보는 방법",
        "excerpt": "요약",
        "cover_image_url": "/static/generated/test-cover.png",
        "content_html": (
            "<h2>아이 개월 수를 보는 기준</h2>"
            "<p>AgeCalc 아이 개월 수 계산기는 생활 기준을 이해하는 데 도움이 됩니다.</p>"
            "<h2>가정에서 확인할 점</h2>"
            "<p>개월 수와 발달 기록을 함께 살펴보면 진료 상담 전에 상황을 정리할 수 있습니다.</p>"
            "<h2>계산기 활용 포인트</h2>"
            '<p><a href="/baby-months">아이 개월 수 계산기</a>로 날짜 기준을 먼저 확인합니다.</p>'
            "<h2>한국 독자가 볼 점</h2>"
            "<p>예방접종, 상담, 가족 기록처럼 생활 속 일정과 연결해 볼 수 있습니다.</p>"
            "<h2>주의할 점</h2>"
            "<p>의학적 판단은 전문가 상담이 우선이며 계산 결과는 참고용입니다.</p>"
            "<h3>참고 링크</h3>"
            '<p><a href="https://example.com/story">원문 보기</a></p>'
        )
        * 16,
        "sources": [_source()],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class AdsenseBlogReviewTests(unittest.TestCase):
    def test_audit_keeps_rich_related_article(self):
        result = audit_post(_post())

        self.assertTrue(result.keep)
        self.assertEqual([], result.critical_issue_codes)

    def test_audit_flags_generated_rss_and_short_article(self):
        result = audit_post(
            _post(
                content_html=(
                    "<h2>노인 맞춤형 운동 교실</h2>"
                    "<p>AgeCalc 계산기와 연결해 볼 수 있습니다.</p>"
                    "<h3>참고 링크</h3>"
                    '<p><a href="https://news.google.com/rss/articles/example?oc=5">원문</a></p>'
                ),
                sources=[_source("https://news.google.com/rss/articles/example?oc=5", "Generated from RSS (openai)")],
            )
        )

        self.assertFalse(result.keep)
        self.assertIn("generated_rss_marker", result.critical_issue_codes)
        self.assertIn("thin_body", result.issue_codes)
        self.assertIn("google_news_redirect_source", result.critical_issue_codes)

    def test_audit_flags_missing_internal_calculator_link(self):
        result = audit_post(
            _post(
                content_html=(
                    "<h2>아이 개월 수를 보는 기준</h2>"
                    "<p>AgeCalc 계산기와 생활 기준을 함께 설명하는 글입니다.</p>"
                    "<h2>가정에서 확인할 점</h2>"
                    "<p>개월 수와 발달 기록을 함께 살펴볼 수 있습니다.</p>"
                    "<h2>계산기 활용 포인트</h2>"
                    "<p>날짜 기준을 먼저 확인하면 생활 일정을 정리하기 쉽습니다.</p>"
                    "<h2>한국 독자가 볼 점</h2>"
                    "<p>예방접종, 상담, 가족 기록처럼 생활 속 일정과 연결해 볼 수 있습니다.</p>"
                    "<h2>주의할 점</h2>"
                    "<p>의학적 판단은 전문가 상담이 우선이며 계산 결과는 참고용입니다.</p>"
                    "<h3>참고 링크</h3>"
                    '<p><a href="https://example.com/story">원문 보기</a></p>'
                )
                * 20,
            )
        )

        self.assertFalse(result.keep)
        self.assertIn("missing_internal_link", result.critical_issue_codes)

    def test_audit_flags_body_under_minimum_chars(self):
        result = audit_post(
            _post(
                content_html=(
                    "<h2>아이 개월 수를 보는 기준</h2>"
                    "<p>AgeCalc 아이 개월 수 계산기는 생활 기준을 이해하는 데 도움이 됩니다.</p>"
                    "<h2>가정에서 확인할 점</h2>"
                    "<p>개월 수와 발달 기록을 함께 살펴보면 진료 상담 전에 상황을 정리할 수 있습니다.</p>"
                    "<h2>계산기 활용 포인트</h2>"
                    '<p><a href="/baby-months">아이 개월 수 계산기</a>로 날짜 기준을 먼저 확인합니다.</p>'
                    "<h2>한국 독자가 볼 점</h2>"
                    "<p>예방접종, 상담, 가족 기록처럼 생활 속 일정과 연결해 볼 수 있습니다.</p>"
                    "<h2>주의할 점</h2>"
                    "<p>의학적 판단은 전문가 상담이 우선이며 계산 결과는 참고용입니다.</p>"
                    "<h3>참고 링크</h3>"
                    '<p><a href="https://example.com/story">원문 보기</a></p>'
                )
                * 8,
            )
        )

        self.assertFalse(result.keep)
        self.assertIn("thin_body", result.critical_issue_codes)

    def test_audit_flags_missing_cover_when_required(self):
        result = audit_post(_post(cover_image_url=None), require_cover_image=True)

        self.assertFalse(result.keep)
        self.assertIn("missing_cover_image", result.critical_issue_codes)

    def test_audit_posts_flags_similar_title_cluster(self):
        posts = [
            _post(id=1, slug="a", title="부천시 튼튼 시니어 운동 교실의 의미와 활용법"),
            _post(id=2, slug="b", title="활기찬 노년을 위한 부천시 튼튼 시니어 운동 교실 이야기"),
        ]

        results = audit_posts(posts)

        self.assertEqual(2, len(results))
        self.assertTrue(all("similar_title_cluster" in result.issue_codes for result in results))


if __name__ == "__main__":
    unittest.main()
