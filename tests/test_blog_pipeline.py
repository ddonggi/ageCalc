import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base
from models.blog_models import FeedItem, FeedSource, GeneratedPost
from scripts import rss_blog_scheduler as scheduler


class BlogPipelineTests(unittest.TestCase):
    def _make_feed_item(self, **overrides):
        defaults = {
            "original_title": "Can humans live to 150? New anti-aging research sparks global debate",
            "original_url": "https://example.com/story",
            "summary": "Researchers are discussing whether lifespan extension can realistically reach 150 years.",
            "content": "Scientists, biotech founders, and clinicians are debating how far longevity science can go.",
        }
        defaults.update(overrides)
        return SimpleNamespace(**defaults)

    def test_build_generation_prompt_for_english_source_requires_korean_recreation(self):
        prompt = scheduler._build_generation_prompt(self._make_feed_item())

        self.assertIn("한국어 독자를 위한 설명형 블로그 글", prompt)
        self.assertIn("직역하지 말고", prompt)
        self.assertIn("한국 독자", prompt)
        self.assertIn("계산기", prompt)
        self.assertIn("2,700~3,500자", prompt)
        self.assertIn("최소 2,500자 이상", prompt)
        self.assertIn("한글 기준 2,700자 이상", prompt)
        self.assertIn("최소 5개", prompt)
        self.assertIn("/age", prompt)

    def test_build_generation_prompt_includes_retry_feedback(self):
        prompt = scheduler._build_generation_prompt(
            self._make_feed_item(),
            feedback="이전 생성 결과가 1,200자로 너무 짧았습니다.",
        )

        self.assertIn("이전 생성 결과가 1,200자로 너무 짧았습니다.", prompt)
        self.assertIn("같은 문제가 반복되지 않게", prompt)

    def test_quality_gate_rejects_low_value_english_copy(self):
        ok, reason = scheduler._evaluate_generated_post(
            self._make_feed_item(),
            title="Can humans live to 150? New anti-aging research sparks global debate - India Today",
            excerpt="Can humans live to 150? New anti-aging research sparks global debate.",
            content_html=(
                "<h2>Can humans live to 150? New anti-aging research sparks global debate</h2>"
                "<p>Can humans live to 150? New anti-aging research sparks global debate.</p>"
                "<h3>참고 링크</h3>"
                '<p><a href="https://example.com/story">원문 보기</a></p>'
            ),
        )

        self.assertFalse(ok)
        self.assertIn("재창작", reason)

    def test_quality_gate_rejects_missing_internal_calculator_link(self):
        body = (
            "<h2>핵심 요약</h2><p>AgeCalc 계산기와 생활 기준을 함께 살펴볼 수 있는 글입니다.</p>"
            "<h2>배경 설명</h2><p>한국 독자에게 필요한 맥락을 충분히 다시 설명합니다.</p>"
            "<h2>한국 독자가 확인할 점</h2><p>생활 일정과 나이 기준을 연결해 읽을 수 있습니다.</p>"
            "<h2>활용 포인트</h2><p>계산 결과를 해석할 때 도움이 되는 기준을 정리합니다.</p>"
            "<h2>주의할 점</h2><p>개별 상황에 따라 결과 해석이 달라질 수 있습니다.</p>"
            "<h2>참고 링크</h2><p><a href=\"https://example.com/story\">원문 보기</a></p>"
        ) * 24

        ok, reason = scheduler._evaluate_generated_post(
            self._make_feed_item(original_title="아이 개월 수 계산과 생활 기준"),
            title="아이 개월 수 계산과 생활 기준을 함께 보는 방법",
            excerpt="아이 개월 수 계산 결과를 생활 기준과 함께 해석하는 방법입니다.",
            content_html=body,
        )

        self.assertFalse(ok)
        self.assertIn("내부 계산기", reason)

    def test_quality_gate_rejects_google_news_redirect_source(self):
        body = (
            "<h2>핵심 요약</h2><p>AgeCalc 계산기와 생활 기준을 함께 살펴볼 수 있는 글입니다.</p>"
            "<h2>배경 설명</h2><p>한국 독자에게 필요한 맥락을 충분히 다시 설명합니다.</p>"
            "<h2>한국 독자가 확인할 점</h2><p>생활 일정과 나이 기준을 연결해 읽을 수 있습니다.</p>"
            "<h2>활용 포인트</h2><p><a href=\"/age\">만 나이 계산기</a>로 확인할 수 있습니다.</p>"
            "<h2>주의할 점</h2><p>개별 상황에 따라 결과 해석이 달라질 수 있습니다.</p>"
            "<h2>참고 링크</h2><p><a href=\"https://example.com/story\">원문 보기</a></p>"
        ) * 24

        ok, reason = scheduler._evaluate_generated_post(
            self._make_feed_item(original_url="https://news.google.com/rss/articles/example?oc=5"),
            title="나이 기준을 생활 일정과 함께 보는 방법",
            excerpt="나이 계산 결과를 생활 일정과 함께 해석하는 방법입니다.",
            content_html=body,
        )

        self.assertFalse(ok)
        self.assertIn("원문 URL", reason)

    def test_google_news_batchexecute_response_is_decoded(self):
        response_text = (
            ")]}'\n\n"
            '[[["wrb.fr","Fbv4je","[\\"garturlres\\",\\"https://example.com/story?x=1&y=2\\",1]",null,null,null,"generic"]]]'
        )

        decoded = scheduler._decode_google_news_batchexecute_response(response_text)

        self.assertEqual("https://example.com/story?x=1&y=2", decoded)

    def test_google_news_article_id_is_extracted_from_rss_url(self):
        article_id = scheduler._google_news_article_id(
            "https://news.google.com/rss/articles/CBMiabc123?oc=5"
        )

        self.assertEqual("CBMiabc123", article_id)

    def test_create_posts_marks_generation_failures_as_needs_review(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)

        session = Session()
        source = FeedSource(name="EN Feed", rss_url="https://example.com/rss", site_url="https://example.com")
        session.add(source)
        session.flush()
        session.add(
            FeedItem(
                source_id=source.id,
                original_title="Can humans live to 150? New anti-aging research sparks global debate",
                original_url="https://example.com/story",
                summary="Researchers are debating extreme lifespan extension.",
                content="Scientists are debating how realistic 150-year lifespans are.",
                status="new",
            )
        )
        session.commit()

        with mock.patch.object(
            scheduler,
            "_generate_with_openai",
            side_effect=RuntimeError("generation failed"),
        ), mock.patch.object(
            scheduler,
            "_send_review_email",
        ) as send_review_email:
            created = scheduler.create_posts(
                session=session,
                limit=1,
                status="draft",
                provider="openai",
                model="gpt-4.1-mini",
                ollama_url="http://127.0.0.1:11434",
                dry_run=False,
            )

        self.assertEqual(created, 1)
        post = session.query(GeneratedPost).one()
        self.assertEqual(post.status, "needs_review")
        self.assertIn("자동 초안 생성 품질 검토 필요", post.content_html)
        send_review_email.assert_not_called()

    def test_create_posts_retries_short_openai_generation_before_review(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)

        session = Session()
        source = FeedSource(name="KR Feed", rss_url="https://example.com/rss", site_url="https://example.com")
        session.add(source)
        session.flush()
        session.add(
            FeedItem(
                source_id=source.id,
                original_title="아이 개월 수 계산과 발달 기준을 함께 보는 방법",
                original_url="https://example.com/story",
                summary="아이 개월 수와 생활 기준을 함께 정리합니다.",
                content="아이 개월 수와 생활 기준을 함께 정리합니다.",
                status="new",
            )
        )
        session.commit()

        short_html = (
            "<h2>핵심 요약</h2>"
            '<p><a href="/baby-months">아이 개월 수 계산기</a>와 생활 기준을 함께 보는 짧은 글입니다.</p>'
            "<h2>참고 링크</h2>"
            '<p><a href="https://example.com/story">원문 보기</a></p>'
        )
        long_html = (
            "<h2>아이 개월 수를 보는 기준</h2>"
            "<p>AgeCalc 아이 개월 수 계산기는 생활 기준을 이해하는 데 도움이 됩니다.</p>"
            "<h2>가정에서 확인할 점</h2>"
            "<p>개월 수와 발달 기록을 함께 살펴보면 진료 상담 전에 상황을 정리할 수 있습니다.</p>"
            "<h2>계산기 활용 포인트</h2>"
            '<p><a href="/baby-months">아이 개월 수 계산기</a>로 날짜 기준을 먼저 확인하세요.</p>'
            "<h2>한국 독자가 볼 점</h2>"
            "<p>예방접종, 어린이집 상담, 가족 기록처럼 생활 속 일정과 함께 보면 좋습니다.</p>"
            "<h2>주의할 점</h2>"
            "<p>의학적 판단은 전문가 상담이 우선이며 계산 결과는 참고용입니다.</p>"
            "<h3>참고 링크</h3>"
            '<p><a href="https://example.com/story">원문 보기</a></p>'
        ) * 24

        with mock.patch.object(
            scheduler,
            "_generate_with_openai",
            side_effect=[
                ("짧은 초안", "요약", short_html),
                ("아이 개월 수 계산과 발달 기준", "요약", long_html),
            ],
        ) as generate, mock.patch.object(
            scheduler,
            "_generate_cover_with_openai",
            return_value=[],
        ), mock.patch.object(
            scheduler,
            "_send_review_email",
        ):
            created = scheduler.create_posts(
                session=session,
                limit=1,
                status="draft",
                provider="openai",
                model="gpt-4.1-mini",
                ollama_url="http://127.0.0.1:11434",
                dry_run=False,
            )

        self.assertEqual(created, 1)
        self.assertEqual(2, generate.call_count)
        self.assertTrue(generate.call_args_list[1].kwargs["feedback"])
        post = session.query(GeneratedPost).one()
        self.assertEqual("draft", post.status)
        self.assertEqual("아이 개월 수 계산과 발달 기준", post.title)

    def test_create_posts_preserves_failed_generated_candidate_for_review(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)

        session = Session()
        source = FeedSource(name="KR Feed", rss_url="https://example.com/rss", site_url="https://example.com")
        session.add(source)
        session.flush()
        session.add(
            FeedItem(
                source_id=source.id,
                original_title="시니어 운동 교실과 생활 기준",
                original_url="https://example.com/story",
                summary="시니어 운동 교실 소식입니다.",
                content="시니어 운동 교실 소식입니다.",
                status="new",
            )
        )
        session.commit()

        short_html = (
            "<h2>핵심 요약</h2>"
            '<p><a href="/age">만 나이 계산기</a>와 생활 기준을 함께 보는 짧은 글입니다.</p>'
            "<h2>참고 링크</h2>"
            '<p><a href="https://example.com/story">원문 보기</a></p>'
        )

        with mock.patch.object(
            scheduler,
            "_generate_with_openai",
            return_value=("시니어 운동 교실을 생활 기준과 함께 보는 방법", "요약", short_html),
        ), mock.patch.object(
            scheduler,
            "_send_review_email",
        ):
            created = scheduler.create_posts(
                session=session,
                limit=1,
                status="draft",
                provider="openai",
                model="gpt-4.1-mini",
                ollama_url="http://127.0.0.1:11434",
                dry_run=False,
            )

        self.assertEqual(created, 1)
        post = session.query(GeneratedPost).one()
        self.assertEqual("needs_review", post.status)
        self.assertIn("생성된 후보 본문", post.content_html)
        self.assertIn("시니어 운동 교실을 생활 기준과 함께 보는 방법", post.content_html)
        self.assertIn("만 나이 계산기", post.content_html)

    def test_create_posts_uses_public_safe_source_attribution(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)

        session = Session()
        source = FeedSource(name="KR Feed", rss_url="https://example.com/rss", site_url="https://example.com")
        session.add(source)
        session.flush()
        session.add(
            FeedItem(
                source_id=source.id,
                original_title="아이 개월 수 계산과 발달 기준을 함께 보는 방법",
                original_url="https://example.com/story",
                summary="아이 개월 수와 생활 기준을 함께 정리합니다.",
                content="아이 개월 수와 생활 기준을 함께 정리합니다.",
                status="new",
            )
        )
        session.commit()

        generated_html = (
            "<h2>아이 개월 수를 보는 기준</h2>"
            "<p>AgeCalc 아이 개월 수 계산기는 생활 기준을 이해하는 데 도움이 됩니다.</p>"
            "<h2>가정에서 확인할 점</h2>"
            "<p>개월 수와 발달 기록을 함께 살펴보면 진료 상담 전에 상황을 정리할 수 있습니다.</p>"
            "<h2>계산기 활용 포인트</h2>"
            '<p><a href="/baby-months">아이 개월 수 계산기</a>로 날짜 기준을 먼저 확인하세요.</p>'
            "<h2>한국 독자가 볼 점</h2>"
            "<p>예방접종, 어린이집 상담, 가족 기록처럼 생활 속 일정과 함께 보면 좋습니다.</p>"
            "<h2>주의할 점</h2>"
            "<p>의학적 판단은 전문가 상담이 우선이며 계산 결과는 참고용입니다.</p>"
            "<h3>참고 링크</h3>"
            '<p><a href="https://example.com/story">원문 보기</a></p>'
        ) * 24

        with mock.patch.object(
            scheduler,
            "_generate_with_openai",
            return_value=("아이 개월 수 계산과 발달 기준", "요약", generated_html),
        ), mock.patch.object(
            scheduler,
            "_generate_cover_with_openai",
            return_value=[],
        ), mock.patch.object(
            scheduler,
            "_send_review_email",
        ):
            created = scheduler.create_posts(
                session=session,
                limit=1,
                status="draft",
                provider="openai",
                model="gpt-4.1-mini",
                ollama_url="http://127.0.0.1:11434",
                dry_run=False,
            )

        self.assertEqual(created, 1)
        post = session.query(GeneratedPost).one()
        self.assertEqual("draft", post.status)
        self.assertEqual(1, len(post.sources))
        self.assertNotIn("Generated from RSS", post.sources[0].attribution_text or "")


if __name__ == "__main__":
    unittest.main()
