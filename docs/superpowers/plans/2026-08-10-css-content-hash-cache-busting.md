# CSS Content Hash Cache Busting Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 모든 로컬 CSS URL에 파일 내용 기반 SHA-256 버전을 자동으로 붙여 배포 직후 최신 스타일이 사용자에게 전달되게 한다.

**Architecture:** `app.py`에 순수 파일 해시 함수와 파일명별 캐시 함수, Jinja용 `versioned_static(filename)`을 추가한다. 모든 템플릿의 로컬 CSS 링크는 이 함수로 전환하며 Nginx의 기존 30일 캐시는 유지한다.

**Tech Stack:** Python 3.12, Flask/Jinja2, SHA-256, unittest, CSS/Nginx 정적 파일 캐시

## Global Constraints

- 해시는 CSS 파일 내용에만 의존하고 SHA-256 앞 12자를 사용한다.
- 정적 경로 밖 파일은 읽지 않는다.
- 파일 누락이나 읽기 실패는 일반 정적 URL로 폴백한다.
- 모든 로컬 CSS에 적용하고 외부 CSS에는 적용하지 않는다.
- JavaScript, 이미지, manifest URL과 Nginx 캐시 설정은 변경하지 않는다.

---

### Task 1: 콘텐츠 해시 URL 생성기

**Files:**
- Modify: `app.py:1-15,190-290`
- Create: `tests/test_static_asset_versioning.py`

**Interfaces:**
- Produces: `_content_hash(path: Path) -> str`
- Produces: `_static_asset_version(filename: str) -> str | None`
- Produces: `versioned_static(filename: str) -> str`

- [ ] **Step 1: 실패 테스트 작성**

```python
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
```

- [ ] **Step 2: 테스트 실패 확인**

Run:

```bash
ADSENSE_REVIEW_MODE=true /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_static_asset_versioning
```

Expected: `_content_hash`가 없어 FAIL 또는 ERROR.

- [ ] **Step 3: 최소 구현 추가**

`app.py` import에 `hashlib`, `functools.lru_cache`를 추가하고 다음 함수를 `PROJECT_ROOT` 선언 뒤에 둔다.

```python
STATIC_ROOT = (PROJECT_ROOT / "static").resolve()


def _content_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


@lru_cache(maxsize=None)
def _static_asset_version(filename: str) -> str | None:
    try:
        path = (STATIC_ROOT / filename).resolve()
        path.relative_to(STATIC_ROOT)
        if not path.is_file():
            return None
        return _content_hash(path)
    except (OSError, ValueError):
        return None


def versioned_static(filename: str) -> str:
    static_url = url_for("static", filename=filename)
    version = _static_asset_version(filename)
    return f"{static_url}?v={version}" if version else static_url
```

- [ ] **Step 4: Jinja 전역 등록**

`inject_csp_nonce()` 반환 사전에 다음 항목을 추가한다.

```python
"versioned_static": versioned_static,
```

- [ ] **Step 5: 단위 테스트 통과 확인**

Run:

```bash
ADSENSE_REVIEW_MODE=true /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_static_asset_versioning
```

Expected: 3 tests, OK.

- [ ] **Step 6: 커밋**

```bash
git add app.py tests/test_static_asset_versioning.py
git commit -m "feat: add content-hashed static CSS URLs"
```

---

### Task 2: 모든 로컬 CSS 템플릿 전환

**Files:**
- Modify: `templates/*.html`
- Modify: `tests/test_static_asset_versioning.py`

**Interfaces:**
- Consumes: `versioned_static(filename: str) -> str`
- Produces: 모든 로컬 CSS `<link>`가 콘텐츠 해시 URL을 렌더링하는 템플릿 집합

- [ ] **Step 1: 공개 페이지 렌더링 실패 테스트 추가**

```python
    def test_public_pages_render_hashed_local_stylesheets(self):
        expected = hashlib.sha256(
            (app_module.PROJECT_ROOT / "static/css/style.css").read_bytes()
        ).hexdigest()[:12]
        client = app_module.app.test_client()

        for path in ("/", "/blog/dog-age-calculation-guide", "/guides/age-calculation-2026"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(200, response.status_code)
                html = response.get_data(as_text=True)
                self.assertIn(f'/static/css/style.css?v={expected}', html)
                self.assertNotIn("home-h1-20260710a", html)
                self.assertNotIn("reading-progress-20260810a", html)
```

- [ ] **Step 2: 테스트 실패 확인**

Run:

```bash
ADSENSE_REVIEW_MODE=true /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_static_asset_versioning.StaticAssetVersioningTests.test_public_pages_render_hashed_local_stylesheets
```

Expected: 기존 수동 버전 문자열 때문에 FAIL.

- [ ] **Step 3: 템플릿 CSS 링크 기계적 전환**

각 로컬 CSS 링크를 다음 형태로 바꾼다.

```jinja2
<link rel="stylesheet" href="{{ versioned_static('css/style.css') }}" />
<link rel="stylesheet" href="{{ versioned_static('css/memory.css') }}" />
```

전환 후 다음 검색 결과가 0인지 확인한다.

```bash
rg -n "url_for\('static', filename='css/" templates
rg -n "style\.css.*\?v=" templates
```

- [ ] **Step 4: 렌더링 테스트 통과 확인**

Run:

```bash
ADSENSE_REVIEW_MODE=true /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest tests.test_static_asset_versioning
```

Expected: 4 tests, OK.

- [ ] **Step 5: 전체 테스트와 변경 범위 검증**

Run:

```bash
ADSENSE_REVIEW_MODE=true /srv/apps/agecalc/.micromamba/envs/agecalc/bin/python -m unittest discover -s tests
git diff --check
git status --short
```

Expected: 전체 테스트 OK, `.codex` 외 예상 파일만 변경됨.

- [ ] **Step 6: 커밋**

```bash
git add templates tests/test_static_asset_versioning.py
git commit -m "refactor: version all local CSS assets automatically"
```
