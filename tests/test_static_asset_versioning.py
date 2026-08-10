import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import app as app_module
from flask import render_template


class StaticAssetVersioningTests(unittest.TestCase):
    def test_content_hash_uses_first_twelve_sha256_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.css"
            path.write_bytes(b"body { color: red; }")

            self.assertEqual(
                hashlib.sha256(b"body { color: red; }").hexdigest()[:12],
                app_module._content_hash(path),
            )

    def test_versioned_static_renders_content_hash_and_missing_file_falls_back(self):
        expected = hashlib.sha256(
            (app_module.PROJECT_ROOT / "static/css/style.css").read_bytes()
        ).hexdigest()[:12]

        with app_module.app.test_request_context("/"):
            self.assertEqual(
                f"/static/css/style.css?v={expected}",
                app_module.versioned_static("css/style.css"),
            )
            self.assertEqual(
                "/static/css/missing.css",
                app_module.versioned_static("css/missing.css"),
            )

    def test_static_asset_version_rejects_parent_path(self):
        self.assertIsNone(app_module._static_asset_version("../app.py"))

    def test_public_pages_render_hashed_local_stylesheets(self):
        expected = hashlib.sha256(
            (app_module.PROJECT_ROOT / "static/css/style.css").read_bytes()
        ).hexdigest()[:12]
        client = app_module.app.test_client()

        for path in ("/", "/blog", "/guides/age-calculation-2026"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                self.assertIn(f"/static/css/style.css?v={expected}", html)
                self.assertNotIn("home-h1-20260710a", html)
                self.assertNotIn("reading-progress-20260810a", html)

        post = SimpleNamespace(
            id=1,
            slug="test-post",
            title="테스트 글",
            excerpt="요약",
            content_html="<p>본문</p>",
            cover_image_url=None,
            status="published",
            published_at=None,
            created_at=None,
            updated_at=None,
            sources=[],
        )
        with app_module.app.test_request_context("/blog/test-post"):
            html = render_template(
                "blog-detail.html",
                post=post,
                draft_mode=False,
                review_mode=False,
                blog_indexable=True,
                structured_article=app_module._structured_blog_context(post),
            )
        self.assertIn(f"/static/css/style.css?v={expected}", html)


if __name__ == "__main__":
    unittest.main()
