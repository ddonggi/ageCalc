from __future__ import annotations

import json
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db import Base
from models.blog_models import FeedItem, FeedSource, GeneratedPost, PostSource


class PublishCuratedBlogTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:", future=True)
        Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)
        self.session = Session()

        feed_source = FeedSource(name="테스트", rss_url="https://example.com/feed.xml")
        self.session.add(feed_source)
        self.session.flush()
        feed_item = FeedItem(
            source_id=feed_source.id,
            original_title="원문",
            original_url="https://example.com/article",
            status="used",
        )
        self.session.add(feed_item)
        self.session.flush()
        legacy_post = GeneratedPost(
            slug="legacy-unregistered-post",
            title="삭제 전 백업할 글",
            excerpt="기존 요약",
            content_html="<p>기존 본문</p>",
            cover_image_url=None,
            status="published",
            published_at=datetime(2026, 7, 1, 9, 0),
        )
        self.session.add(legacy_post)
        self.session.flush()
        self.session.add(
            PostSource(
                generated_post_id=legacy_post.id,
                feed_item_id=feed_item.id,
                source_name="테스트 출처",
                source_url=feed_item.original_url,
                attribution_text="복구되어야 하는 연결",
            )
        )
        self.session.commit()

    def tearDown(self):
        self.session.close()

    def test_dry_run_reports_exact_scope_without_writing(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS
        from scripts.publish_curated_blog import plan_release

        report = plan_release(self.session)

        self.assertEqual(1, report["delete_posts"])
        self.assertEqual(1, report["delete_post_sources"])
        self.assertEqual(len(BLOG_ARTICLE_BLUEPRINTS), report["create_posts"])
        self.assertEqual(1, self.session.query(GeneratedPost).count())
        self.assertEqual(1, self.session.query(PostSource).count())
        self.assertEqual(1, self.session.query(FeedItem).count())
        self.assertEqual(1, self.session.query(FeedSource).count())

    def test_apply_backs_up_deletes_only_unregistered_rows_and_publishes_all_curated_posts(self):
        from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS
        from scripts.adsense_blog_review import audit_post
        from scripts.publish_curated_blog import apply_release, verify_backup

        with tempfile.TemporaryDirectory() as directory:
            report = apply_release(
                self.session,
                backup_dir=Path(directory),
                published_at=datetime(2026, 7, 22, 10, 30),
            )

            backup_path = Path(report["backup_path"])
            backup = verify_backup(backup_path)

        self.assertEqual(1, len(backup["generated_posts"]))
        self.assertEqual(1, len(backup["post_sources"]))
        self.assertEqual(0, self.session.query(PostSource).count())
        self.assertEqual(1, self.session.query(FeedItem).count())
        self.assertEqual(1, self.session.query(FeedSource).count())
        posts = self.session.query(GeneratedPost).all()
        self.assertEqual(set(BLOG_ARTICLE_BLUEPRINTS), {post.slug for post in posts})
        self.assertTrue(all(post.status == "published" for post in posts))
        self.assertTrue(all(post.published_at == datetime(2026, 7, 22, 10, 30) for post in posts))
        for post in posts:
            with self.subTest(slug=post.slug):
                self.assertTrue(audit_post(post, require_cover_image=True).keep)

    def test_apply_rolls_back_every_database_change_when_audit_fails(self):
        from scripts.publish_curated_blog import ReleaseError, apply_release

        def reject_every_post(post):
            return False, "forced audit failure"

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ReleaseError, "forced audit failure"):
                apply_release(
                    self.session,
                    backup_dir=Path(directory),
                    published_at=datetime(2026, 7, 22, 10, 30),
                    audit_callback=reject_every_post,
                )

        self.assertEqual(["legacy-unregistered-post"], [post.slug for post in self.session.query(GeneratedPost).all()])
        self.assertEqual(1, self.session.query(PostSource).count())

    def test_apply_uses_naive_utc_for_default_publication_time(self):
        from scripts.publish_curated_blog import apply_release

        before = datetime.now(UTC).replace(tzinfo=None)
        with tempfile.TemporaryDirectory() as directory:
            apply_release(self.session, backup_dir=Path(directory))
        after = datetime.now(UTC).replace(tzinfo=None)

        published_times = {
            post.published_at
            for post in self.session.query(GeneratedPost).filter_by(status="published").all()
        }
        self.assertEqual(1, len(published_times))
        published_at = published_times.pop()
        self.assertGreaterEqual(published_at, before)
        self.assertLessEqual(published_at, after)

    def test_restore_rejects_tampering_and_recovers_rows_and_timestamps(self):
        from scripts.publish_curated_blog import (
            BackupIntegrityError,
            apply_release,
            restore_backup,
            verify_backup,
        )

        with tempfile.TemporaryDirectory() as directory:
            original_post = self.session.query(GeneratedPost).one()
            original_created_at = original_post.created_at
            report = apply_release(
                self.session,
                backup_dir=Path(directory),
                published_at=datetime(2026, 7, 22, 10, 30),
            )
            backup_path = Path(report["backup_path"])

            restored = restore_backup(self.session, backup_path)
            recovered = self.session.query(GeneratedPost).filter_by(slug="legacy-unregistered-post").one()
            self.assertEqual(1, restored["restored_posts"])
            self.assertEqual(original_created_at, recovered.created_at)
            recovered_source = self.session.query(PostSource).one()
            self.assertEqual(recovered.id, recovered_source.generated_post_id)

            payload = verify_backup(backup_path)
            payload["generated_posts"][0]["title"] = "변조"
            backup_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            with self.assertRaises(BackupIntegrityError):
                verify_backup(backup_path)

    def test_restore_remaps_colliding_ids_without_claiming_another_backed_up_id(self):
        from scripts.publish_curated_blog import apply_release, restore_backup

        self.session.add(
            GeneratedPost(
                id=13,
                slug="legacy-id-thirteen",
                title="아이디 충돌 복구 글",
                excerpt=None,
                content_html="<p>복구 본문</p>",
                cover_image_url=None,
                status="draft",
                published_at=None,
            )
        )
        self.session.commit()

        with tempfile.TemporaryDirectory() as directory:
            report = apply_release(
                self.session,
                backup_dir=Path(directory),
                published_at=datetime(2026, 7, 22, 10, 30),
            )
            restored = restore_backup(self.session, Path(report["backup_path"]))

        recovered = self.session.query(GeneratedPost).filter(
            GeneratedPost.slug.in_(("legacy-unregistered-post", "legacy-id-thirteen"))
        ).all()
        self.assertEqual(2, restored["restored_posts"])
        self.assertEqual(2, len(recovered))
        self.assertEqual(2, len({post.id for post in recovered}))


if __name__ == "__main__":
    unittest.main()
