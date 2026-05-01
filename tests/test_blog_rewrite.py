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
    ) * 24


class BlogRewriteTests(unittest.TestCase):
    def _make_session(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        Base.metadata.create_all(bind=engine)
        return Session()

    def _add_post(
        self,
        session,
        *,
        title: str,
        status: str,
        content_html: str = "<h2>짧은 글</h2><p>Generated from RSS (openai)</p>",
        source_url: str | None = None,
        cover_image_url: str | None = None,
    ):
        source = FeedSource(name=f"RSS {title}", rss_url=f"https://example.com/{title}/rss")
        session.add(source)
        session.flush()
        effective_source_url = source_url or f"https://example.com/{title}/source"
        item = FeedItem(
            source_id=source.id,
            original_title=title,
            original_url=effective_source_url,
            summary="Short summary",
            content="Short content",
            status="used",
        )
        session.add(item)
        session.flush()
        post = GeneratedPost(
            slug=title.lower().replace(" ", "-"),
            title=title,
            excerpt="Short summary",
            content_html=content_html,
            cover_image_url=cover_image_url,
            status=status,
            published_at=datetime(2026, 1, 1) if status == "published" else None,
        )
        session.add(post)
        session.flush()
        session.add(
            PostSource(
                generated_post_id=post.id,
                feed_item_id=item.id,
                source_name="RSS",
                source_url=effective_source_url,
                attribution_text="Generated from RSS (openai)",
            )
        )
        session.commit()
        return post

    def test_build_rewrite_prompt_requires_adsense_safe_structure(self):
        post = GeneratedPost(
            slug="old-post",
            title="Can humans live to 150?",
            excerpt="Short summary",
            content_html="<p>Short copied content.</p>",
            status="needs_review",
        )

        prompt = rewriter.build_rewrite_prompt(post, "https://example.com/story")

        self.assertIn("2,700~3,500자", prompt)
        self.assertIn("최소 2,500자", prompt)
        self.assertIn("한글 기준 2,700자", prompt)
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
            cover_generator=lambda title, excerpt, content_html, slug: [
                f"/static/generated/{slug}-cover.png"
            ],
        )

        session.refresh(post)
        self.assertEqual(1, changed)
        self.assertEqual("draft", post.status)
        self.assertIsNone(post.published_at)
        self.assertEqual("https://example.com/story", post.sources[0].source_url)
        self.assertIsNone(post.sources[0].attribution_text)
        self.assertTrue(post.cover_image_url.endswith("-cover.png"))
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

    def test_rewrite_all_statuses_can_publish_valid_rewrites(self):
        session = self._make_session()
        needs_review = self._add_post(session, title="Needs Review Story", status="needs_review")
        draft = self._add_post(session, title="Draft Story", status="draft")
        published = self._add_post(
            session,
            title="Published Story",
            status="published",
            content_html=_rich_rewritten_html(),
            cover_image_url="/static/generated/existing-cover.png",
        )

        changed = rewriter.rewrite_posts(
            session=session,
            limit=10,
            post_id=None,
            statuses=("needs_review", "draft", "published"),
            apply=True,
            model="gpt-4.1-mini",
            publish_on_pass=True,
            demote_failed_published=True,
            attempts=1,
            source_resolver=lambda url: "https://example.com/story",
            generator=lambda prompt, model: (
                "나이 기준을 생활 일정과 함께 보는 방법",
                "나이 계산 결과를 생활 일정과 함께 해석하는 방법입니다.",
                _rich_rewritten_html(),
            ),
            cover_generator=lambda title, excerpt, content_html, slug: [
                f"/static/generated/{slug}-cover.png"
            ],
        )

        self.assertEqual(3, changed)
        for post in (needs_review, draft, published):
            session.refresh(post)
            self.assertEqual("published", post.status)
            self.assertIsNotNone(post.published_at)
            self.assertTrue(post.cover_image_url)
            self.assertNotIn("Generated from RSS", post.content_html)

    def test_rewrite_demotes_published_post_when_rewrite_fails(self):
        session = self._make_session()
        post = self._add_post(
            session,
            title="Published Thin Story",
            status="published",
            content_html="<h2>짧은 글</h2><p>너무 짧은 공개 글입니다.</p>",
            cover_image_url="/static/generated/existing-cover.png",
        )

        changed = rewriter.rewrite_posts(
            session=session,
            limit=10,
            post_id=None,
            statuses=("published",),
            apply=True,
            model="gpt-4.1-mini",
            publish_on_pass=True,
            demote_failed_published=True,
            attempts=1,
            source_resolver=lambda url: "https://example.com/story",
            generator=lambda prompt, model: (
                "짧은 후보",
                "짧은 요약",
                "<h2>짧은 후보</h2><p>본문이 부족합니다.</p>",
            ),
        )

        session.refresh(post)
        self.assertEqual(1, changed)
        self.assertEqual("needs_review", post.status)
        self.assertIsNone(post.published_at)
        self.assertIn("생성된 후보 본문", post.content_html)
        self.assertIn("재창작 본문 길이가 짧아", post.content_html)

    def test_rewrite_retries_with_feedback_before_persisting(self):
        session = self._make_session()
        post = self._add_post(session, title="Retry Story", status="needs_review")
        prompts = []

        def generator(prompt, model):
            prompts.append(prompt)
            if len(prompts) == 1:
                return "짧은 후보", "짧은 요약", "<h2>짧은 후보</h2><p>본문이 부족합니다.</p>"
            return (
                "나이 기준을 생활 일정과 함께 보는 방법",
                "나이 계산 결과를 생활 일정과 함께 해석하는 방법입니다.",
                _rich_rewritten_html(),
            )

        changed = rewriter.rewrite_posts(
            session=session,
            limit=1,
            post_id=None,
            statuses=("needs_review",),
            apply=True,
            model="gpt-4.1-mini",
            publish_on_pass=False,
            demote_failed_published=False,
            attempts=2,
            source_resolver=lambda url: "https://example.com/story",
            generator=generator,
            cover_generator=lambda title, excerpt, content_html, slug: [
                f"/static/generated/{slug}-cover.png"
            ],
        )

        session.refresh(post)
        self.assertEqual(1, changed)
        self.assertEqual("draft", post.status)
        self.assertEqual(2, len(prompts))
        self.assertIn("이전 재작성 결과 검수 실패", prompts[1])
        self.assertIn("재창작 본문 길이가 짧아", prompts[1])


if __name__ == "__main__":
    unittest.main()
