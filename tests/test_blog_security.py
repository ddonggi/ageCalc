from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest import mock

import app as app_module


app = app_module.app


class BlogSecurityTests(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True)
        app_module.BLOG_DRAFT_LOGIN_FAILURES.clear()

    def test_session_cookie_uses_secure_browser_defaults(self):
        self.assertTrue(app.config["SESSION_COOKIE_SECURE"])
        self.assertTrue(app.config["SESSION_COOKIE_HTTPONLY"])
        self.assertEqual("Lax", app.config["SESSION_COOKIE_SAMESITE"])

    def test_production_requires_stable_flask_secret_key(self):
        with self.assertRaisesRegex(RuntimeError, "FLASK_SECRET_KEY"):
            app_module._resolve_flask_secret_key(None, environment="production")

        self.assertEqual(
            "configured-secret",
            app_module._resolve_flask_secret_key("configured-secret", environment="production"),
        )

        with self.assertRaisesRegex(RuntimeError, "FLASK_SECRET_KEY"):
            app_module._resolve_flask_secret_key(
                None,
                environment=None,
                database_url="mysql+pymysql://agecalc@127.0.0.1/agecalc",
            )

    def test_review_response_is_private_and_does_not_forward_token(self):
        post = SimpleNamespace(
            id=7,
            slug="2026-man-age-guide",
            title="검토 글",
            excerpt="요약",
            content_html="<p>본문</p>",
            cover_image_url=None,
            status="draft",
            published_at=None,
            created_at=None,
            updated_at=None,
            sources=[],
        )

        class FakeQuery:
            def filter(self, *args, **kwargs):
                return self

            def first(self):
                return post

        fake_session = SimpleNamespace(query=lambda model: FakeQuery())
        with mock.patch.object(app_module, "_review_token_is_valid", return_value=True), mock.patch.object(
            app_module, "SessionLocal", return_value=fake_session
        ):
            response = app.test_client().get("/blog/review/7?token=secret-token")

        self.assertEqual("no-store", response.headers.get("Cache-Control"))
        self.assertEqual("no-referrer", response.headers.get("Referrer-Policy"))

    def test_csrf_token_is_stable_in_session_and_rejects_mismatch(self):
        with app.test_request_context("/blog/drafts"):
            token = app_module._get_or_create_csrf_token()

            self.assertEqual(token, app_module._get_or_create_csrf_token())
            self.assertTrue(app_module._csrf_token_is_valid(token))
            self.assertFalse(app_module._csrf_token_is_valid("different"))

    def test_get_review_approval_is_read_only_and_not_routed(self):
        with mock.patch.object(app_module, "SessionLocal") as session_local:
            response = app.test_client().get("/blog/review/7/approve?token=test")

        self.assertEqual(405, response.status_code)
        session_local.assert_not_called()

    def test_review_approval_rejects_missing_csrf_before_database_write(self):
        with mock.patch.object(app_module, "_review_token_is_valid", return_value=True), mock.patch.object(
            app_module, "SessionLocal"
        ) as session_local:
            response = app.test_client().post(
                "/blog/review/7/approve",
                data={"review_token": "test"},
            )

        self.assertEqual(400, response.status_code)
        session_local.assert_not_called()

    def test_review_approval_publishes_after_token_csrf_and_audit(self):
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

        post = SimpleNamespace(id=7, slug="2026-man-age-guide", status="draft", published_at=None)
        fake_session = FakeSession(post)
        client = app.test_client()
        with client.session_transaction() as flask_session:
            flask_session[app_module.BLOG_CSRF_SESSION_KEY] = "csrf-test"

        with mock.patch.object(app_module, "_review_token_is_valid", return_value=True), mock.patch.object(
            app_module, "SessionLocal", return_value=fake_session
        ), mock.patch.object(app_module, "audit_post", return_value=SimpleNamespace(keep=True, issues=[])):
            response = client.post(
                "/blog/review/7/approve",
                data={"review_token": "test", "csrf_token": "csrf-test"},
            )

        self.assertEqual(302, response.status_code)
        self.assertEqual("published", post.status)
        self.assertIsNotNone(post.published_at)
        self.assertTrue(fake_session.committed)

    def test_review_and_draft_templates_do_not_load_tracking_or_expose_referrers(self):
        from flask import render_template

        post = SimpleNamespace(
            id=7,
            slug="2026-man-age-guide",
            title="검토 글",
            excerpt="요약",
            content_html="<p>본문</p>",
            cover_image_url=None,
            status="draft",
            published_at=None,
            created_at=None,
            updated_at=None,
            sources=[],
        )
        with app.test_request_context("/blog/review/7?token=secret-token"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=True,
                review_token="secret-token",
                review_errors=[],
                structured_article=app_module._structured_blog_context(post),
                coupang_partners_enabled=True,
            )

        self.assertIn('<meta name="referrer" content="no-referrer"', html)
        self.assertIn("window.history.replaceState", html)
        self.assertNotIn("js/analytics.js", html)
        self.assertNotIn("js/clarity-init.js", html)
        self.assertNotIn("link.coupang.com", html)
        self.assertIn('href="/blog/birth-year-age-interpretation"', html)

    def test_five_recent_password_failures_trigger_rate_limit(self):
        now = datetime(2026, 7, 21, 12, 0, tzinfo=timezone.utc)
        for offset in range(app_module.BLOG_DRAFT_LOGIN_MAX_FAILURES):
            app_module._record_draft_login_failure("203.0.113.7", now=now + timedelta(seconds=offset))

        self.assertTrue(app_module._draft_login_is_limited("203.0.113.7", now=now + timedelta(minutes=1)))
        self.assertFalse(
            app_module._draft_login_is_limited(
                "203.0.113.7",
                now=now + app_module.BLOG_DRAFT_LOGIN_WINDOW + timedelta(seconds=1),
            )
        )

    def test_login_rate_limit_uses_client_ip_from_single_trusted_proxy(self):
        clients = (("198.51.100.10", app.test_client()), ("203.0.113.20", app.test_client()))
        for client_ip, client in clients:
            with client.session_transaction() as flask_session:
                flask_session[app_module.BLOG_CSRF_SESSION_KEY] = "csrf-test"
            client.post(
                "/blog/drafts",
                data={"password": "wrong", "csrf_token": "csrf-test"},
                headers={"X-Forwarded-For": client_ip},
            )

        self.assertIn("198.51.100.10", app_module.BLOG_DRAFT_LOGIN_FAILURES)
        self.assertIn("203.0.113.20", app_module.BLOG_DRAFT_LOGIN_FAILURES)


if __name__ == "__main__":
    unittest.main()
