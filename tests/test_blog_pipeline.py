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


if __name__ == "__main__":
    unittest.main()
