import unittest
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base
from models.blog_models import FeedItem, FeedSource, GeneratedPost, PostSource
from scripts import rewrite_blog_posts as rewriter


def _rich_rewritten_html():
    return (
        "<h2>핵심 요약</h2>"
        "<p>AgeCalc 계산기와 생활 기준을 함께 살펴보는 설명형 글입니다.</p>"
        "<h2>배경과 맥락</h2>"
        "<p>한국 독자가 이해하기 쉽도록 원문 내용을 다시 구성했습니다.</p>"
        "<h2>한국 독자가 확인할 점</h2>"
        "<p>생활 일정, 가족 기록, 상담 준비처럼 실제 상황에 맞춰 읽을 수 있습니다.</p>"
        "<h2>AgeCalc 활용 포인트</h2>"
        '<p><a href="/age">만 나이 계산기</a>로 날짜 기준을 먼저 확인하세요.</p>'
        "<h2>주의할 점과 한계</h2>"
        "<p>개별 상황에 따라 해석이 달라질 수 있으므로 참고용으로 활용해야 합니다.</p>"
        "<h2>참고 링크</h2>"
        '<p><a href="https://example.com/story">원문 보기</a></p>'
    ) * 12


class BlogRewriteTests(unittest.TestCase):
    def _make_session(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)
        return Session()

    def test_build_rewrite_prompt_requires_adsense_safe_structure(self):
        post = GeneratedPost(
            slug="old-post",
            title="Can humans live to 150?",
            excerpt="Short summary",
            content_html="<p>Short copied content.</p>",
            status="needs_review",
        )

        prompt = rewriter.build_rewrite_prompt(post, "https://example.com/story")

        self.assertIn("1,800~2,400자", prompt)
        self.assertIn("최소 5개", prompt)
        self.assertIn("AgeCalc 내부 계산기 링크", prompt)
        self.assertIn("번역이나 요약이 아니라", prompt)

    def test_rewrite_needs_review_post_updates_to_draft_only_after_validation(self):
        session = self._make_session()
        source = FeedSource(name="RSS", rss_url="https://example.com/rss")
        session.add(source)
        session.flush()
        item = FeedItem(
            source_id=source.id,
            original_title="Can humans live to 150?",
            original_url="https://news.google.com/rss/articles/example?oc=5",
            summary="Short summary",
            content="Short content",
            status="used",
        )
        session.add(item)
        session.flush()
        post = GeneratedPost(
            slug="old-post",
            title="Can humans live to 150?",
            excerpt="Short summary",
            content_html="<h2>짧은 글</h2><p>Generated from RSS (openai)</p>",
            status="needs_review",
            published_at=datetime(2026, 1, 1),
        )
        session.add(post)
        session.flush()
        session.add(
            PostSource(
                generated_post_id=post.id,
                feed_item_id=item.id,
                source_name="RSS",
                source_url="https://news.google.com/rss/articles/example?oc=5",
                attribution_text="Generated from RSS (openai)",
            )
        )
        session.commit()

        changed = rewriter.rewrite_needs_review_posts(
            session=session,
            limit=1,
            post_id=None,
            apply=True,
            model="gpt-4.1-mini",
            source_resolver=lambda url: "https://example.com/story",
            generator=lambda prompt, model: (
                "나이 기준을 생활 일정과 함께 보는 방법",
                "나이 계산 결과를 생활 일정과 함께 해석하는 방법입니다.",
                _rich_rewritten_html(),
            ),
        )

        session.refresh(post)
        self.assertEqual(1, changed)
        self.assertEqual("draft", post.status)
        self.assertIsNone(post.published_at)
        self.assertEqual("https://example.com/story", post.sources[0].source_url)
        self.assertIsNone(post.sources[0].attribution_text)
        self.assertNotIn("Generated from RSS", post.content_html)

    def test_rewrite_keeps_post_in_review_when_source_url_cannot_be_resolved(self):
        session = self._make_session()
        source = FeedSource(name="RSS", rss_url="https://example.com/rss")
        session.add(source)
        session.flush()
        item = FeedItem(
            source_id=source.id,
            original_title="Can humans live to 150?",
            original_url="https://news.google.com/rss/articles/example?oc=5",
            summary="Short summary",
            content="Short content",
            status="used",
        )
        session.add(item)
        session.flush()
        post = GeneratedPost(
            slug="old-post",
            title="Can humans live to 150?",
            excerpt="Short summary",
            content_html="<h2>짧은 글</h2><p>Generated from RSS (openai)</p>",
            status="needs_review",
        )
        session.add(post)
        session.flush()
        session.add(
            PostSource(
                generated_post_id=post.id,
                feed_item_id=item.id,
                source_name="RSS",
                source_url="https://news.google.com/rss/articles/example?oc=5",
                attribution_text="Generated from RSS (openai)",
            )
        )
        session.commit()

        changed = rewriter.rewrite_needs_review_posts(
            session=session,
            limit=1,
            post_id=None,
            apply=True,
            model="gpt-4.1-mini",
            source_resolver=lambda url: None,
            generator=lambda prompt, model: (
                "나이 기준을 생활 일정과 함께 보는 방법",
                "나이 계산 결과를 생활 일정과 함께 해석하는 방법입니다.",
                _rich_rewritten_html(),
            ),
        )

        session.refresh(post)
        self.assertEqual(0, changed)
        self.assertEqual("needs_review", post.status)


if __name__ == "__main__":
    unittest.main()
