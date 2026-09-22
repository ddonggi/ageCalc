import tempfile
import unittest
from pathlib import Path
from unittest import mock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app as module
from db import Base
from models.blog_models import GeneratedPost
from scripts.publish_curated_blog import create_backup, restore_backup, ReleaseError
from tests.test_blog_feed import FakeSession, post_for


class BlogRestorationTests(unittest.TestCase):
    def test_restore_only_previously_published_rows_and_reject_second_restore(self):
        engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(engine)
        with sessionmaker(bind=engine)() as session, tempfile.TemporaryDirectory() as directory:
            for status in ('published', 'draft', 'needs_review'):
                session.add(GeneratedPost(slug=status, title=status, content_html='<p>Original</p>', status=status))
            session.commit()
            backup = create_backup(session, Path(directory), posts=session.query(GeneratedPost).all(), sources=[])
            session.query(GeneratedPost).delete()
            session.commit()
            result = restore_backup(session, backup, published_only=True)
            self.assertEqual(1, result['restored_posts'])
            self.assertEqual(['published'], [p.slug for p in session.query(GeneratedPost).all()])
            with self.assertRaises(ReleaseError):
                restore_backup(session, backup, published_only=True)
            self.assertEqual(1, session.query(GeneratedPost).count())

    def test_legacy_article_is_public_but_draft_stays_private(self):
        module.app.config['TESTING'] = True
        post = post_for('restored-legacy', 1)
        with mock.patch.object(module, 'SessionLocal', return_value=FakeSession([post])), mock.patch.object(module, '_is_blog_public_indexable', return_value=True):
            response = module.app.test_client().get('/blog/restored-legacy')
            self.assertEqual(200, response.status_code)
            html = response.get_data(as_text=True)
            self.assertIn('전체 본문', html)
            self.assertIn('https://agecalc.cloud/blog/restored-legacy', html)
            self.assertIn('BlogPosting', html)
            self.assertNotIn('noindex', html)
            post.status = 'draft'
            self.assertEqual(404, module.app.test_client().get('/blog/restored-legacy').status_code)
            self.assertEqual([], module._published_eligible_blog_posts(FakeSession([post])))
