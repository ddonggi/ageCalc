import hashlib
import tempfile
import unittest
from pathlib import Path

import app as app_module


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


if __name__ == "__main__":
    unittest.main()
