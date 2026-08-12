import math
import hashlib
from flask import Flask, Response, render_template, request, jsonify, g, send_from_directory, abort, redirect, session, url_for, make_response
import json
import os
import threading
from functools import lru_cache
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import secrets
import warnings
from time import monotonic
from email.utils import format_datetime
from zoneinfo import ZoneInfo
from werkzeug.middleware.proxy_fix import ProxyFix
from controllers.age_controller import AgeController
from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS, structured_blog_article_for_slug
from content.blog.schema import BLOG_CATEGORIES, CATEGORY_PAGE_EDITORIAL_CONTENT
from content.blog.rendering import render_article_content_html
from content.editorial_metadata import editorial_metadata_for
from content.guide_pages import (
    GUIDE_PAGE_BY_SLUG,
    INDEXABLE_GUIDE_PAGES,
    NON_INDEXABLE_GUIDE_PATHS,
)
from content.hub_pages import HUB_PAGE_BY_KEY, HUB_PAGE_BY_SLUG, HUB_PAGES
from content.page_registry import (
    PUBLIC_PAGE_REGISTRY,
    PUBLIC_SITEMAP_ENDPOINTS,
    SITEMAP_GROUPS,
    contextual_links_for,
    find_page,
    indexable_pages_for_sitemap,
)
from db import SessionLocal, close_db_session, init_db
from models.blog_models import GeneratedPost, PageFeedback
from scripts.adsense_blog_review import audit_post

PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_ROOT = (PROJECT_ROOT / "static").resolve()
ENV_FILE = PROJECT_ROOT / ".env.rss"


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


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if not key or key in os.environ:
            continue

        os.environ[key] = value.strip().strip('"').strip("'")


_load_env_file(ENV_FILE)


def _load_blog_timezone():
    tz_name = (os.getenv("BLOG_TIMEZONE", "Asia/Seoul") or "Asia/Seoul").strip()
    try:
        return ZoneInfo(tz_name)
    except Exception:
        return timezone(timedelta(hours=9), name="KST")


BLOG_TIMEZONE = _load_blog_timezone()


def _resolve_flask_secret_key(
    value: str | None,
    *,
    environment: str | None = None,
    database_url: str | None = None,
) -> str:
    configured = (value or "").strip()
    if configured:
        return configured
    runtime_environment = (environment or "development").strip().lower()
    production_database = (database_url or "").strip().lower().startswith(("mysql", "postgresql"))
    if runtime_environment not in {"development", "dev", "test", "testing", "local", "production", "prod"}:
        raise RuntimeError("AGECALC_ENV must be development, test, or production")
    if runtime_environment in {"production", "prod"} or production_database:
        raise RuntimeError("FLASK_SECRET_KEY must be configured in production")
    warnings.warn(
        "FLASK_SECRET_KEY is not configured; using the stable development-only key.",
        RuntimeWarning,
        stacklevel=2,
    )
    return "agecalc-development-only-secret-key"


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.secret_key = _resolve_flask_secret_key(
    os.getenv("FLASK_SECRET_KEY"),
    environment=os.getenv("AGECALC_ENV"),
    database_url=os.getenv("DATABASE_URL"),
)
app.config.update(
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
_score_lock = threading.Lock()
_score_file = os.path.join(app.root_path, "data", "snake_scores.json")
os.makedirs(os.path.dirname(_score_file), exist_ok=True)
init_db()

BLOG_DRAFT_ACCESS_SESSION_KEY = "blog_draft_access"
BLOG_CSRF_SESSION_KEY = "blog_csrf_token"
BLOG_DRAFT_LOGIN_MAX_FAILURES = 5
BLOG_DRAFT_LOGIN_WINDOW = timedelta(minutes=15)
BLOG_DRAFT_LOGIN_FAILURES: dict[str, list[datetime]] = {}
_blog_draft_login_lock = threading.Lock()
SITE_BASE_URL = (os.getenv("BLOG_BASE_URL", "https://agecalc.cloud") or "https://agecalc.cloud").rstrip("/")
SITE_AUTHOR_NAME = os.getenv("SITE_AUTHOR_NAME", "AgeCalc 편집팀").strip() or "AgeCalc 편집팀"
SITE_CONTACT_EMAIL = os.getenv("SITE_CONTACT_EMAIL", "ldg6153@gmail.com").strip() or "ldg6153@gmail.com"
# Search-index allowlist: update only after reviewing exact URL performance data.
INDEXABLE_COLLEGE_ENTRY_YEARS = (2026, 2025, 2024)
COLLEGE_ENTRY_EXAMPLE_YEARS = (2027, 2026, 2023, 2022, 2021, 2020, 2019, 2018, 2009)
ADSENSE_CLIENT_ID = os.getenv("ADSENSE_CLIENT_ID", "ca-pub-7818333740838556").strip()
GOOGLE_SITE_VERIFICATION = os.getenv(
    "GOOGLE_SITE_VERIFICATION",
    "q0nvIaon9IVWNZZEQzTRCycYka7jIHuzYu-PwxxoKu8",
).strip()
def _parse_adsense_review_mode(value: str | None) -> bool:
    normalized = (value or "true").strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    warnings.warn(
        f"Unknown ADSENSE_REVIEW_MODE={value!r}; keeping review mode enabled.",
        RuntimeWarning,
        stacklevel=2,
    )
    return True


ADSENSE_REVIEW_MODE = _parse_adsense_review_mode(os.getenv("ADSENSE_REVIEW_MODE", "true"))
BLOG_INDEX_MIN_POSTS = int(os.getenv("BLOG_INDEX_MIN_POSTS", "3").strip() or "3")
BLOG_CATEGORY_INDEX_MIN_POSTS = 3
BLOG_PUBLIC_INDEXING_ENABLED = (os.getenv("BLOG_PUBLIC_INDEXING_ENABLED", "false") or "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
COUPANG_PARTNERS_ENABLED = (os.getenv("COUPANG_PARTNERS_ENABLED", "false") or "false").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
ADSENSE_REVIEW_HUB_PATHS = frozenset(str(hub["path"]) for hub in HUB_PAGES)
COUPANG_EVENT_PROMOTIONS_FILE = PROJECT_ROOT / "content" / "coupang_event_promotions.json"
COUPANG_BABY_PROMOTIONS = [
    {
        "title": "썸머 준비 육아템",
        "category": "출산/유아동",
        "url": "https://link.coupang.com/a/eDoP3hEASq",
        "image_url": "https://img1c.coupangcdn.com/image/affiliate/event/promotion/2026/06/15/1bb95dbd7f98002701a8fc22bbf631aa.png",
        "width": 800,
        "height": 800,
        "end_date": datetime(2026, 6, 21).date(),
        "end_label": "2026.06.21",
    },
    {
        "title": "풀캉스 COOL SALE",
        "category": "출산/유아동",
        "url": "https://link.coupang.com/a/eDoUqmShXM",
        "image_url": "https://image11.coupangcdn.com/image/affiliate/event/promotion/2026/06/15/10b97ebd229800b901a80422bcf7b22c.png",
        "width": 800,
        "height": 800,
        "end_date": datetime(2026, 6, 28).date(),
        "end_label": "2026.06.28",
    },
]
KOREAN_ZODIAC = ["원숭이", "닭", "개", "돼지", "쥐", "소", "호랑이", "토끼", "용", "뱀", "말", "양"]
GENERATION_LABELS = [
    ((1946, 1964), "베이비붐 세대"),
    ((1965, 1980), "X세대"),
    ((1981, 1996), "밀레니얼 세대"),
    ((1997, 2012), "Z세대"),
    ((2013, 2030), "알파 세대"),
]
DOG_HUMAN_AGE_TABLE = {
    "small": [15, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80],
    "medium": [15, 24, 28, 32, 36, 42, 47, 51, 56, 60, 65, 69, 74, 78, 83, 87],
    "large": [15, 24, 28, 32, 36, 45, 50, 55, 61, 66, 72, 77, 82, 88, 93, 99],
    "giant": [12, 22, 31, 38, 45, 49, 56, 64, 71, 79, 86, 93, 100, 107, 114, 121],
}
FOOTER_POLICY_LINKS = [
    {"endpoint": "about", "label": "운영 원칙"},
    {"endpoint": "references", "label": "계산 기준"},
    {"endpoint": "contact", "label": "문의"},
    {"endpoint": "privacy", "label": "개인정보처리방침"},
    {"endpoint": "terms", "label": "이용약관"},
]
@app.before_request
def set_csp_nonce():
    g.csp_nonce = secrets.token_urlsafe(16)


def _redirect_with_query(target: str, code: int = 301):
    if request.query_string:
        target = f"{target}?{request.query_string.decode('latin-1')}"
    return redirect(target, code=code)


LEGACY_HUB_REDIRECTS = {
    "/age/": "/age-tools/",
    "/health/": "/health-tools/",
}
TRAILING_SLASH_REDIRECTS = {
    f"{page['path']}/": str(page["path"])
    for page in PUBLIC_PAGE_REGISTRY
    if page["path"] != "/" and not str(page["path"]).endswith("/")
}


@app.before_request
def normalize_public_page_url():
    if request.method not in {"GET", "HEAD"}:
        return None
    target = LEGACY_HUB_REDIRECTS.get(request.path)
    if target is None:
        target = TRAILING_SLASH_REDIRECTS.get(request.path)
    if target is None:
        return None
    return _redirect_with_query(target)

@app.context_processor
def inject_csp_nonce():
    editorial_policy_url = "#"
    try:
        editorial_policy_url = url_for("about")
    except RuntimeError:
        pass

    blog_public_count = (
        _cached_published_blog_count()
        if BLOG_PUBLIC_INDEXING_ENABLED and not ADSENSE_REVIEW_MODE
        else 0
    )
    blog_public_indexable = _is_blog_public_indexable(blog_public_count)
    current_page = find_page(request.endpoint, request.view_args)
    page_canonical_url = getattr(g, "page_canonical_url", None)
    if page_canonical_url is None and current_page:
        page_canonical_url = f"{SITE_BASE_URL}{current_page['path']}"
    current_hub_key = (
        str(current_page["hub"])
        if current_page and current_page["hub"] in HUB_PAGE_BY_KEY
        else None
    )
    breadcrumbs = []
    breadcrumb_schema = None
    if current_page and current_page["endpoint"] != "index":
        breadcrumbs.append({"label": "홈", "url": f"{SITE_BASE_URL}/", "current": False})
        if current_hub_key and not str(current_page["key"]).startswith("hub:"):
            hub = HUB_PAGE_BY_KEY[current_hub_key]
            breadcrumbs.append(
                {
                    "label": hub["title"],
                    "url": f"{SITE_BASE_URL}{hub['path']}",
                    "current": False,
                }
            )
        breadcrumbs.append(
            {
                "label": current_page["title"],
                "url": page_canonical_url,
                "current": True,
            }
        )
        breadcrumb_schema = {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": position,
                    "name": item["label"],
                    "item": item["url"],
                }
                for position, item in enumerate(breadcrumbs, start=1)
            ],
        }

    return {
        "csp_nonce": getattr(g, "csp_nonce", ""),
        "versioned_static": versioned_static,
        "csrf_token": _get_or_create_csrf_token,
        "author_name": SITE_AUTHOR_NAME,
        "contact_email": SITE_CONTACT_EMAIL,
        "editorial_policy_url": editorial_policy_url,
        "adsense_enabled": _adsense_is_enabled_for_path(
            request.path,
            blog_public_indexable=blog_public_indexable,
        ),
        "adsense_client_id": ADSENSE_CLIENT_ID,
        "adsense_review_mode": ADSENSE_REVIEW_MODE,
        "google_site_verification": GOOGLE_SITE_VERIFICATION,
        "blog_public_indexable": blog_public_indexable,
        "blog_public_count": blog_public_count,
        "article_by_slug": BLOG_ARTICLE_BLUEPRINTS,
        "coupang_partners_enabled": _coupang_partners_is_enabled(),
        "coupang_active_baby_promotions": _active_coupang_baby_promotions(),
        "coupang_event_promotions": _active_coupang_event_promotions(),
        "life_hubs": HUB_PAGES,
        "primary_life_hubs": HUB_PAGES[:4],
        "current_hub_key": current_hub_key,
        "current_page": current_page,
        "page_canonical_url": page_canonical_url,
        "site_base_url": SITE_BASE_URL,
        "editorial_metadata": editorial_metadata_for(current_page),
        "related_paths": contextual_links_for(
            current_page,
            recommended_endpoints=tuple(getattr(g, "recommended_endpoints", ())),
        ),
        "breadcrumbs": breadcrumbs,
        "breadcrumb_schema": breadcrumb_schema,
        "footer_policy_links": FOOTER_POLICY_LINKS,
        "static_guide_pages": INDEXABLE_GUIDE_PAGES,
    }


@app.teardown_appcontext
def cleanup_session(exception=None):
    close_db_session(exception)

@app.after_request
def add_security_headers(response):
    if request.path == "/health":
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    elif request.path == "/minigames" or request.path.startswith("/minigames/"):
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    elif getattr(g, "result_query_noindex", False):
        response.headers["X-Robots-Tag"] = "noindex, follow"
    elif ADSENSE_REVIEW_MODE and request.path in ADSENSE_REVIEW_HUB_PATHS:
        response.headers["X-Robots-Tag"] = "noindex, follow"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    nonce = getattr(g, "csp_nonce", "")
    coupang_image_sources = ""
    coupang_frame_sources = ""
    if not ADSENSE_REVIEW_MODE:
        coupang_image_sources = " https://ads-partners.coupang.com https://*.coupangcdn.com"
        coupang_frame_sources = " https://ads-partners.coupang.com"
    csp = (
        "default-src 'self'; "
        "img-src 'self' data: https://c.clarity.ms https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net"
        f"{coupang_image_sources}; "
        "font-src 'self' https://fonts.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        f"script-src 'self' 'nonce-{nonce}' https://www.googletagmanager.com https://www.clarity.ms https://scripts.clarity.ms https://pagead2.googlesyndication.com https://ep2.adtrafficquality.google; "
        "connect-src 'self' https://www.google-analytics.com https://www.clarity.ms https://c.clarity.ms https://i.clarity.ms https://ep1.adtrafficquality.google https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net; "
        "frame-src https://googleads.g.doubleclick.net https://pagead2.googlesyndication.com"
        f"{coupang_frame_sources} https://ep2.adtrafficquality.google https://www.google.com; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    return response


def _ensure_score_file():
    os.makedirs(os.path.dirname(_score_file), exist_ok=True)
    if not os.path.exists(_score_file):
        with open(_score_file, "w", encoding="utf-8") as f:
            json.dump({"scores": []}, f)


def _load_scores():
    _ensure_score_file()
    with open(_score_file, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {"scores": []}
    return data.get("scores", [])


def _save_scores(scores):
    _ensure_score_file()
    with open(_score_file, "w", encoding="utf-8") as f:
        json.dump({"scores": scores}, f, ensure_ascii=False)


def _date_key(ts):
    return ts.strftime("%Y-%m-%d")


def _month_key(ts):
    return ts.strftime("%Y-%m")



@app.get("/health") 
def health(): 
    return {"ok": True}, 200


@app.get("/favicon.ico")
def favicon():
    return send_from_directory(app.root_path, "favicon.ico")


@app.get("/llms.txt")
def llms_txt():
    return send_from_directory(STATIC_ROOT, "llms.txt", mimetype="text/plain")


def _review_token_is_valid(token: str) -> bool:
    expected = (os.getenv("BLOG_REVIEW_TOKEN", "") or "").strip()
    provided = (token or "").strip()
    return bool(expected) and secrets.compare_digest(expected, provided)


def _draft_password_is_valid(password: str) -> bool:
    expected = (os.getenv("BLOG_DRAFT_PASSWORD", "") or "").strip()
    provided = (password or "").strip()
    return bool(expected) and secrets.compare_digest(expected, provided)


def _draft_access_granted() -> bool:
    return bool(session.get(BLOG_DRAFT_ACCESS_SESSION_KEY))


def _get_or_create_csrf_token() -> str:
    token = str(session.get(BLOG_CSRF_SESSION_KEY, "") or "")
    if not token:
        token = secrets.token_urlsafe(32)
        session[BLOG_CSRF_SESSION_KEY] = token
    return token


def _csrf_token_is_valid(provided_token: str) -> bool:
    expected = str(session.get(BLOG_CSRF_SESSION_KEY, "") or "")
    provided = str(provided_token or "")
    return bool(expected) and secrets.compare_digest(expected, provided)


def _require_valid_csrf() -> None:
    provided = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
    if not _csrf_token_is_valid(provided):
        abort(400, description="유효하지 않은 요청 토큰입니다.")


def _prune_draft_login_failures(ip_address: str, *, now: datetime) -> list[datetime]:
    cutoff = now - BLOG_DRAFT_LOGIN_WINDOW
    failures = [timestamp for timestamp in BLOG_DRAFT_LOGIN_FAILURES.get(ip_address, []) if timestamp > cutoff]
    if failures:
        BLOG_DRAFT_LOGIN_FAILURES[ip_address] = failures
    else:
        BLOG_DRAFT_LOGIN_FAILURES.pop(ip_address, None)
    return failures


def _record_draft_login_failure(ip_address: str, *, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    with _blog_draft_login_lock:
        failures = _prune_draft_login_failures(ip_address, now=now)
        failures.append(now)
        BLOG_DRAFT_LOGIN_FAILURES[ip_address] = failures


def _draft_login_is_limited(ip_address: str, *, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    with _blog_draft_login_lock:
        failures = _prune_draft_login_failures(ip_address, now=now)
        return len(failures) >= BLOG_DRAFT_LOGIN_MAX_FAILURES


def _clear_draft_login_failures(ip_address: str) -> None:
    with _blog_draft_login_lock:
        BLOG_DRAFT_LOGIN_FAILURES.pop(ip_address, None)


def _as_blog_localtime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(BLOG_TIMEZONE)


@app.template_filter("blog_datetime")
def blog_datetime(value: datetime | None, fmt: str = "%Y-%m-%d %H:%M") -> str:
    local_dt = _as_blog_localtime(value)
    if local_dt is None:
        return ""
    return local_dt.strftime(fmt)


def _format_sitemap_lastmod(value: datetime | None) -> str | None:
    if value is None:
        return None
    local_dt = _as_blog_localtime(value)
    if local_dt is None:
        return None
    return local_dt.date().isoformat()


def _absolute_url_for(endpoint: str, **values) -> str:
    return f"{SITE_BASE_URL}{url_for(endpoint, **values)}"


def _independent_db_session():
    factory = getattr(SessionLocal, "session_factory", None)
    return factory() if factory is not None else SessionLocal()


def _article_is_publicly_eligible(article: dict[str, object], *, today: date | None = None) -> bool:
    today = today or _current_local_date()
    try:
        expires_at = date.fromisoformat(str(article["expires_at"]))
    except (KeyError, ValueError):
        return False
    return bool(article.get("is_curated")) and bool(article.get("is_indexable")) and today < expires_at


def _eligible_public_blog_slugs(*, today: date | None = None) -> tuple[str, ...]:
    return tuple(
        slug
        for slug, article in BLOG_ARTICLE_BLUEPRINTS.items()
        if _article_is_publicly_eligible(article, today=today)
    )


def _public_blog_slugs() -> tuple[str, ...]:
    return _eligible_public_blog_slugs()


def _published_blog_count() -> int:
    db_session = _independent_db_session()
    try:
        return len(_published_eligible_blog_posts(db_session))
    finally:
        db_session.close()


BLOG_PUBLIC_COUNT_CACHE_TTL_SECONDS = 30
_blog_public_count_cache_lock = threading.Lock()
_blog_public_count_cache: tuple[float, int] | None = None


def _invalidate_blog_public_count_cache() -> None:
    global _blog_public_count_cache
    with _blog_public_count_cache_lock:
        _blog_public_count_cache = None


def _cached_published_blog_count() -> int:
    global _blog_public_count_cache
    if app.config.get("TESTING"):
        return _published_blog_count()
    now = monotonic()
    with _blog_public_count_cache_lock:
        if _blog_public_count_cache and now - _blog_public_count_cache[0] < BLOG_PUBLIC_COUNT_CACHE_TTL_SECONDS:
            return _blog_public_count_cache[1]
    count = _published_blog_count()
    with _blog_public_count_cache_lock:
        _blog_public_count_cache = (now, count)
    return count


def _published_eligible_blog_posts(db_session) -> list[GeneratedPost]:
    public_slugs = _eligible_public_blog_slugs()
    if not public_slugs:
        return []
    posts = (
        db_session.query(GeneratedPost)
        .filter(GeneratedPost.status == "published", GeneratedPost.slug.in_(public_slugs))
        .order_by(GeneratedPost.published_at.desc(), GeneratedPost.id.desc())
        .all()
    )
    public_slug_set = set(public_slugs)
    return [
        post
        for post in posts
        if post.slug in public_slug_set and audit_post(post, require_cover_image=True).keep
    ]


def _is_blog_public_indexable(published_count: int | None = None) -> bool:
    if ADSENSE_REVIEW_MODE or not BLOG_PUBLIC_INDEXING_ENABLED:
        return False
    count = _cached_published_blog_count() if published_count is None else published_count
    return count >= BLOG_INDEX_MIN_POSTS


def _structured_blog_context(post) -> dict[str, object] | None:
    return structured_blog_article_for_slug(post.slug)


def _absolute_article_thumbnail(article: dict[str, object]) -> str:
    thumbnail = str(article["thumbnail"])
    return f"{SITE_BASE_URL}{thumbnail}" if thumbnail.startswith("/") else thumbnail


def _blog_article_schema(post, article: dict[str, object]) -> dict[str, object]:
    image_url = _absolute_article_thumbnail(article)
    schema: dict[str, object] = {
        "@context": "https://schema.org",
        "@type": article["schema_type"],
        "headline": article["h1"],
        "description": article["meta_description"],
        "image": [image_url],
        "author": {"@type": "Organization", "name": article["author"], "url": f"{SITE_BASE_URL}/about"},
        "publisher": {
            "@type": "Organization",
            "name": "AgeCalc",
            "logo": {"@type": "ImageObject", "url": f"{SITE_BASE_URL}/static/images/android-chrome-512x512.png"},
        },
        "mainEntityOfPage": {"@type": "WebPage", "@id": article["canonical_url"]},
        "articleSection": article["category_label"],
        "keywords": list(article["tags"]),
        "isAccessibleForFree": True,
    }
    published_at = getattr(post, "published_at", None) or getattr(post, "created_at", None)
    modified_at = getattr(post, "updated_at", None) or published_at
    if published_at:
        schema["datePublished"] = _as_blog_localtime(published_at).isoformat()
    if modified_at:
        schema["dateModified"] = _as_blog_localtime(modified_at).isoformat()
    return schema


def _rss_date(value: datetime | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    elif value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return format_datetime(value)


def _rss_iso_date(value: datetime | None) -> str:
    if value is None:
        value = datetime.now(timezone.utc)
    elif value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _escape_rss_cdata(value: str) -> str:
    return value.replace("]]>", "]]]]><![CDATA[>")


def _coupang_partners_is_enabled() -> bool:
    return COUPANG_PARTNERS_ENABLED and not ADSENSE_REVIEW_MODE


def _adsense_is_enabled_for_path(path: str, *, blog_public_indexable: bool | None = None) -> bool:
    excluded_prefixes = ("/minigames", "/blog/drafts", "/blog/review")
    if any(path == prefix or path.startswith(f"{prefix}/") for prefix in excluded_prefixes):
        return False
    if path in NON_INDEXABLE_GUIDE_PATHS:
        return False
    if ADSENSE_REVIEW_MODE and path in ADSENSE_REVIEW_HUB_PATHS:
        return False
    if path == "/blog" or path.startswith("/blog/"):
        if blog_public_indexable is None:
            blog_public_indexable = _is_blog_public_indexable()
        if not blog_public_indexable:
            return False
    return bool(ADSENSE_CLIENT_ID)


def _is_valid_page_feedback_payload(page_path: str, vote: str) -> bool:
    return page_path == "/age" and vote in {"helpful", "unhelpful"}


def _build_sitemap_entry(loc: str, lastmod: str | None = None) -> str:
    if lastmod:
        return f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>"
    return f"  <url><loc>{loc}</loc></url>"


def _build_sitemap_index_entry(loc: str) -> str:
    return f"  <sitemap><loc>{loc}</loc></sitemap>"


def _current_local_date():
    return datetime.now(BLOG_TIMEZONE).date()


def _active_coupang_baby_promotions(today=None):
    today = today or _current_local_date()
    return [promotion for promotion in COUPANG_BABY_PROMOTIONS if today <= promotion["end_date"]]


def _parse_optional_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _active_coupang_event_promotions(today=None):
    today = today or _current_local_date()
    try:
        raw_promotions = json.loads(COUPANG_EVENT_PROMOTIONS_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    promotions = []
    for item in raw_promotions:
        if not isinstance(item, dict):
            continue
        url = str(item.get("url") or "").strip()
        image_url = str(item.get("image_url") or "").strip()
        width = item.get("width")
        height = item.get("height")
        if (
            not url
            or not image_url
            or not isinstance(width, int)
            or not isinstance(height, int)
            or width <= 0
            or height <= 0
        ):
            continue

        start_date = _parse_optional_date(item.get("start_date"))
        end_date = _parse_optional_date(item.get("end_date"))
        if start_date and today < start_date:
            continue
        if end_date and today > end_date:
            continue

        promotions.append(
            {
                "title": str(item.get("title") or "쿠팡 이벤트 프로모션").strip(),
                "url": url,
                "image_url": image_url,
                "alt": str(item.get("alt") or "쿠팡 이벤트 프로모션").strip(),
                "width": width,
                "height": height,
            }
        )

    return promotions[:3]


def _generation_label(year: int) -> str:
    for (start, end), label in GENERATION_LABELS:
        if start <= year <= end:
            return label
    return "넓은 세대 구분 없음"


def _birth_year_range_label(year: int, current_year: int) -> str:
    annual_age = current_year - year
    if annual_age <= 0:
        return "만 0세"
    return f"만 {annual_age - 1}~{annual_age}세"


def _build_birth_year_snapshot(year: int, current_year: int) -> dict[str, object]:
    annual_age = current_year - year
    if annual_age <= 0:
        detail = "올해 출생자는 현재 기준으로 만 0세입니다. 실제 출생일이 미래라면 아직 계산 대상이 아닐 수 있습니다."
    else:
        detail = f"생일이 지났다면 만 {annual_age}세, 아직 지나지 않았다면 만 {annual_age - 1}세입니다."

    return {
        "year": year,
        "label": f"{year}년생",
        "annual_age": f"{annual_age}세",
        "man_age_range": _birth_year_range_label(year, current_year),
        "detail": detail,
        "zodiac": KOREAN_ZODIAC[year % 12],
        "generation": _generation_label(year),
    }


def _current_school_year(today=None) -> int:
    if today is None:
        today = _current_local_date()
    return today.year if today.month >= 3 else today.year - 1


def _school_grade_label(birth_year: int, school_year: int) -> tuple[str, str]:
    elementary_entry = birth_year + 7
    diff = school_year - elementary_entry

    if diff < 0:
        if diff == -1:
            return ("취학 전", f"{elementary_entry}학년도 초등학교 입학 예정")
        return ("취학 전", f"{elementary_entry}학년도에 초등학교 입학 예정")
    if diff <= 5:
        return (f"초등학교 {diff + 1}학년", "현재 초등학생 단계")
    if diff <= 8:
        return (f"중학교 {diff - 5}학년", "현재 중학생 단계")
    if diff <= 11:
        return (f"고등학교 {diff - 8}학년", "현재 고등학생 단계")
    if diff == 12:
        return ("고등학교 졸업 이후", "대학 진학 또는 진로 선택 시기")
    return ("고등학교 졸업 이후", "학교급 계산 범위 이후 단계")


def _build_school_grade_snapshot(birth_year: int, school_year: int) -> dict[str, object]:
    current_grade, note = _school_grade_label(birth_year, school_year)
    elementary_entry = birth_year + 7
    middle_entry = birth_year + 13
    high_entry = birth_year + 16
    high_graduation_school_year = birth_year + 18
    high_graduation_year = birth_year + 19

    return {
        "year": birth_year,
        "label": f"{birth_year}년생",
        "current_grade": current_grade,
        "note": note,
        "elementary_entry": f"{elementary_entry}학년도",
        "middle_entry": f"{middle_entry}학년도",
        "high_entry": f"{high_entry}학년도",
        "high_graduation_school_year": f"{high_graduation_school_year}학년도",
        "high_graduation_date": f"{high_graduation_year}년 2월",
    }


def _build_school_entry_snapshot(birth_year: int, school_year: int) -> dict[str, object]:
    grade_snapshot = _build_school_grade_snapshot(birth_year, school_year)
    current_grade = grade_snapshot["current_grade"]

    if "취학 전" in current_grade:
        status_note = f"현재는 {current_grade} 단계이며, 가장 가까운 입학 시점은 {grade_snapshot['elementary_entry']} 초등학교 입학입니다."
    elif "초등학교" in current_grade:
        status_note = f"현재는 {current_grade} 단계이며, 중학교 입학은 {grade_snapshot['middle_entry']}, 고등학교 입학은 {grade_snapshot['high_entry']}입니다."
    elif "중학교" in current_grade:
        status_note = f"현재는 {current_grade} 단계이며, 고등학교 입학은 {grade_snapshot['high_entry']}입니다."
    else:
        status_note = f"초등학교 입학은 {grade_snapshot['elementary_entry']}, 중학교 입학은 {grade_snapshot['middle_entry']}, 고등학교 입학은 {grade_snapshot['high_entry']}였습니다."

    return {
        "year": birth_year,
        "label": grade_snapshot["label"],
        "current_grade": current_grade,
        "status_note": status_note,
        "elementary_entry": grade_snapshot["elementary_entry"],
        "middle_entry": grade_snapshot["middle_entry"],
        "high_entry": grade_snapshot["high_entry"],
        "high_graduation_school_year": grade_snapshot["high_graduation_school_year"],
        "high_graduation_date": grade_snapshot["high_graduation_date"],
    }


def _build_grade_age_snapshot(stage: str, grade: int, school_year: int, current_year: int) -> dict[str, object]:
    stage_map = {
        "elementary": ("초등학교", 7),
        "middle": ("중학교", 13),
        "high": ("고등학교", 16),
    }
    school_label, offset = stage_map[stage]
    birth_year = school_year - offset - (grade - 1)
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)
    elementary_entry = birth_year + 7
    middle_entry = birth_year + 13
    high_entry = birth_year + 16
    high_graduation_year = birth_year + 19

    note = f"{school_year}학년도 {school_label} {grade}학년은 보통 {birth_year}년생이 해당하며, 올해 기준 연나이는 {annual_age}세입니다."

    return {
        "stage": stage,
        "grade": grade,
        "label": f"{school_label} {grade}학년",
        "birth_year_label": f"{birth_year}년생",
        "birth_year": birth_year,
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "elementary_entry": f"{elementary_entry}학년도",
        "middle_entry": f"{middle_entry}학년도",
        "high_entry": f"{high_entry}학년도",
        "high_graduation_date": f"{high_graduation_year}년 2월",
        "note": note,
    }


def _build_age_gap_snapshot(year_a: int, year_b: int) -> dict[str, object]:
    older_year = min(year_a, year_b)
    younger_year = max(year_a, year_b)
    gap = younger_year - older_year

    if gap == 0:
        annual_gap = "0년 차이"
        man_gap_range = "만 0세 차이"
        detail = "같은 출생년도라서 연나이와 만나이 모두 같은 흐름으로 계산됩니다."
    else:
        annual_gap = f"{gap}년 차이"
        lower = max(gap - 1, 0)
        man_gap_range = f"만 {lower}~{gap}세 차이"
        detail = f"연나이는 항상 {gap}세 차이이고, 만나이는 두 사람의 생일이 지났는지에 따라 {lower}~{gap}세 차이로 보일 수 있습니다."

    return {
        "year_a": year_a,
        "year_b": year_b,
        "older_year": older_year,
        "younger_year": younger_year,
        "pair_label": f"{older_year}년생과 {younger_year}년생",
        "annual_gap": annual_gap,
        "man_gap_range": man_gap_range,
        "detail": detail,
    }


def _parse_calendar_date(year: int | None, month: int | None, day: int | None):
    if year is None or month is None or day is None:
        return None
    try:
        return datetime(year, month, day).date()
    except ValueError:
        return None


def _convert_short_birth_year(yy: int, current_year: int) -> int:
    current_yy = current_year % 100
    return 2000 + yy if yy <= current_yy else 1900 + yy


def _parse_six_digit_birth_date(raw: str | None, current_year: int):
    digits = "".join(ch for ch in str(raw or "") if ch.isdigit())
    if len(digits) != 6:
        return None

    year = _convert_short_birth_year(int(digits[:2]), current_year)
    month = int(digits[2:4])
    day = int(digits[4:6])
    birth_date = _parse_calendar_date(year, month, day)
    if birth_date is None or birth_date.year > current_year:
        return None
    return birth_date


def _birth_date_to_six_digits(birth_date) -> str:
    return f"{birth_date.year % 100:02d}{birth_date.month:02d}{birth_date.day:02d}"


def _format_calendar_date(value) -> str:
    return value.strftime("%Y.%m.%d")


def _build_hundred_day_snapshot(start_date, today=None) -> dict[str, object]:
    if today is None:
        today = _current_local_date()

    hundredth_date = start_date + timedelta(days=99)
    diff = (hundredth_date - today).days

    if diff > 0:
        status_label = f"D-{diff}"
        status_note = f"100일째까지 {diff}일 남았습니다."
    elif diff < 0:
        status_label = f"D+{abs(diff)}"
        status_note = f"100일째가 지난 지 {abs(diff)}일 되었습니다."
    else:
        status_label = "D-Day"
        status_note = "바로 오늘이 100일째입니다."

    elapsed = (today - start_date).days + 1
    if elapsed < 1:
        elapsed_label = "시작일 전"
    else:
        elapsed_label = f"{elapsed}일째"

    return {
        "start_date": _format_calendar_date(start_date),
        "hundredth_date": _format_calendar_date(hundredth_date),
        "status_label": status_label,
        "status_note": status_note,
        "elapsed_label": elapsed_label,
        "detail": "시작일을 1일째로 계산해 99일을 더한 날짜를 100일째로 안내합니다.",
    }


def _parse_month_day(month: int | None, day: int | None):
    if month is None or day is None:
        return None
    if not (1 <= month <= 12 and 1 <= day <= 31):
        return None

    validation_year = 2000 if month == 2 and day == 29 else 2001
    try:
        datetime(validation_year, month, day).date()
    except ValueError:
        return None
    return month, day


def _next_birthday_date(month: int, day: int, today):
    year = today.year
    while True:
        try:
            candidate = datetime(year, month, day).date()
        except ValueError:
            year += 1
            continue

        if candidate < today:
            year += 1
            continue
        return candidate


def _build_birthday_dday_snapshot(month: int, day: int, today=None) -> dict[str, object]:
    if today is None:
        today = _current_local_date()

    next_birthday = _next_birthday_date(month, day, today)
    days_until = (next_birthday - today).days

    if days_until == 0:
        status_label = "D-Day"
        status_note = "바로 오늘이 생일입니다."
    else:
        status_label = f"D-{days_until}"
        status_note = f"다음 생일까지 {days_until}일 남았습니다."

    return {
        "birthday_label": f"{month}월 {day}일",
        "next_birthday_date": _format_calendar_date(next_birthday),
        "status_label": status_label,
        "status_note": status_note,
        "days_until_label": f"{days_until}일",
        "detail": "월과 일만 입력하면 오늘 기준으로 가장 가까운 다음 생일 날짜를 계산합니다.",
    }


def _build_annual_age_snapshot(birth_date, current_year: int) -> dict[str, object]:
    birth_year = birth_date.year
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)

    return {
        "birth_date": _format_calendar_date(birth_date),
        "birth_year": birth_year,
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "detail": f"연나이는 생일과 관계없이 {current_year}년 - {birth_year}년으로 계산하므로 올해 기준 {annual_age}세입니다.",
    }


def _build_age_comparison_snapshot(birth_year: int, current_year: int) -> dict[str, object]:
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)

    if annual_age <= 0:
        diff_note = "올해 출생자는 연나이와 만나이 모두 0세 기준으로 안내합니다."
        gap_label = "차이 없음"
    else:
        diff_note = "연나이는 생일과 관계없이 고정되지만, 만나이는 생일 전후에 따라 1살 차이까지 생길 수 있습니다."
        gap_label = "0~1살 차이"

    return {
        "birth_year": birth_year,
        "label": f"{birth_year}년생",
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "gap_label": gap_label,
        "diff_note": diff_note,
    }


def _dog_size_label(size: str) -> str:
    return {
        "small": "소형견",
        "medium": "중형견",
        "large": "대형견",
        "giant": "초대형견",
    }.get(size, "소형견")


def _calc_dog_human_age(years: int, size: str) -> int:
    table = DOG_HUMAN_AGE_TABLE.get(size, DOG_HUMAN_AGE_TABLE["small"])
    if years <= 0:
        return 0
    if years <= len(table):
        return table[years - 1]

    last = table[-1]
    prev = table[-2]
    step = last - prev
    return last + step * (years - len(table))


def _calc_cat_human_age(years: int) -> int:
    if years <= 0:
        return 0
    if years == 1:
        return 15
    if years == 2:
        return 24
    return 24 + 4 * (years - 2)


def _build_pet_age_snapshot(pet: str, years: int, size: str = "small") -> dict[str, object]:
    if pet == "cat":
        human_age = _calc_cat_human_age(years)
        label = f"고양이 {years}살"
        detail = "고양이는 첫 해 15세, 둘째 해 24세, 이후에는 해마다 4세씩 더하는 기준으로 많이 안내합니다."
        size_label = ""
    else:
        human_age = _calc_dog_human_age(years, size)
        label = f"강아지 {years}살"
        detail = f"강아지는 { _dog_size_label(size) } 기준 연령표를 적용해 사람 나이로 환산합니다."
        size_label = _dog_size_label(size)

    return {
        "pet": pet,
        "years": years,
        "label": label,
        "size": size,
        "size_label": size_label,
        "human_age": f"{human_age}세",
        "detail": detail,
    }


def _calc_dog_human_age_precise(age_years: float, size: str) -> float:
    table = DOG_HUMAN_AGE_TABLE.get(size, DOG_HUMAN_AGE_TABLE["small"])
    if age_years <= 0:
        return 0.0
    if age_years <= 1:
        return 15 * age_years
    if age_years <= 2:
        return 15 + (24 - 15) * (age_years - 1)

    whole = math.floor(age_years)
    frac = age_years - whole
    last_index = len(table)

    if whole >= last_index:
        last = table[-1]
        prev = table[-2] if len(table) > 1 else last
        step = last - prev or 4
        return last + step * (age_years - last_index)

    base = table[max(whole - 1, 0)]
    next_value = table[whole] if whole < len(table) else base
    return base + (next_value - base) * frac


def _calc_cat_human_age_precise(age_years: float) -> float:
    if age_years <= 0:
        return 0.0
    if age_years <= 1:
        return 15 * age_years
    if age_years <= 2:
        return 15 + 9 * (age_years - 1)
    return 24 + 4 * (age_years - 2)


def _build_pet_month_snapshot(pet: str, months: int, size: str = "small") -> dict[str, object]:
    age_years = months / 12
    age_text = _format_years_months(months)

    if pet == "cat":
        human_age_value = _calc_cat_human_age_precise(age_years)
        label = f"고양이 {months}개월"
        size_label = ""
        detail = "고양이는 첫 2년의 성장 속도가 빨라 같은 6개월이라도 사람 나이로 보면 빠르게 커지는 편입니다."
    else:
        human_age_value = _calc_dog_human_age_precise(age_years, size)
        label = f"강아지 {months}개월"
        size_label = _dog_size_label(size)
        detail = f"강아지는 {size_label} 기준으로 월령이 빠르게 올라가며, 생후 1년 안에서도 환산 차이가 크게 보일 수 있습니다."

    rounded_human_age = max(0, round(human_age_value))
    return {
        "pet": pet,
        "months": months,
        "age_text": age_text,
        "label": label,
        "size": size,
        "size_label": size_label,
        "human_age": f"약 {rounded_human_age}세",
        "detail": detail,
    }


def _short_school_label(stage: str, grade: int) -> str:
    return {
        "elementary": f"초{grade}",
        "middle": f"중{grade}",
        "high": f"고{grade}",
    }[stage]


def _build_grade_birth_year_snapshot(stage: str, grade: int, school_year: int, current_year: int) -> dict[str, object]:
    snapshot = _build_grade_age_snapshot(stage, grade, school_year, current_year)
    short_label = _short_school_label(stage, grade)
    snapshot["short_label"] = short_label
    snapshot["query_label"] = f"{short_label}은 몇 년생"
    snapshot["school_year_label"] = f"{school_year}학년도"
    snapshot["detail"] = f"{school_year}학년도 {snapshot['label']}은 보통 {snapshot['birth_year_label']}이 해당합니다."
    return snapshot


def _build_birth_year_zodiac_snapshot(year: int, current_year: int) -> dict[str, object]:
    snapshot = _build_birth_year_snapshot(year, current_year)
    zodiac_label = f"{snapshot['zodiac']}띠"
    snapshot["zodiac_label"] = zodiac_label
    snapshot["previous_same_zodiac_year"] = year - 12
    snapshot["next_same_zodiac_year"] = year + 12
    snapshot["detail"] = f"{snapshot['label']}은 {zodiac_label}이며, 같은 띠는 12년 간격으로 반복됩니다."
    return snapshot


def _format_college_cohort_label(entry_year: int) -> str:
    return f"{entry_year % 100:02d}학번"


def _build_college_entry_snapshot(entry_year: int, current_year: int) -> dict[str, object]:
    birth_year = entry_year - 19
    annual_age = current_year - birth_year
    man_age_range = _birth_year_range_label(birth_year, current_year)
    cohort_label = _format_college_cohort_label(entry_year)
    high_graduation_year = entry_year

    if entry_year > current_year:
        status_note = f"{cohort_label}은 아직 입학 전이거나 입학 준비 중인 시기로, 보통 {birth_year}년생 기준으로 안내합니다."
    elif entry_year == current_year:
        status_note = f"{cohort_label}은 올해 입학하는 신입생 기준이며, 보통 {birth_year}년생이 해당합니다."
    else:
        elapsed = current_year - entry_year
        status_note = f"{cohort_label}은 {entry_year}년 입학 기준이며 {current_year}년은 입학연도보다 {elapsed}년 뒤입니다. 보통 {birth_year}년생이 해당합니다."

    return {
        "entry_year": entry_year,
        "cohort_label": cohort_label,
        "birth_year": birth_year,
        "birth_year_label": f"{birth_year}년생",
        "annual_age": f"{annual_age}세",
        "man_age_range": man_age_range,
        "detail": status_note,
        "query_label": f"{cohort_label} 나이·몇년생",
        "high_graduation_date": f"{high_graduation_year}년 2월",
    }


def _format_years_months(months: int) -> str:
    years, remaining_months = divmod(months, 12)
    if years == 0:
        return f"{remaining_months}개월"
    return f"{years}년 {remaining_months}개월"


def _baby_stage_label(months: int) -> str:
    if months <= 1:
        return "신생아 시기"
    if months <= 5:
        return "초기 영아기"
    if months <= 11:
        return "활동이 늘어나는 시기"
    if months <= 23:
        return "돌 이후 영아기"
    if months <= 35:
        return "두돌 이후 유아기 초반"
    return "세돌 전후 시기"


def _build_baby_month_snapshot(months: int) -> dict[str, object]:
    age_text = _format_years_months(months)
    stage = _baby_stage_label(months)

    if months == 0:
        note = "출생 직후부터 한 달 전까지는 수유, 수면, 체중 변화처럼 기본 생활 리듬을 살피는 시기입니다."
    elif months < 12:
        note = "예방접종, 수면 변화, 이유식 시작·확장처럼 월령 기준으로 자주 확인하는 정보가 많은 구간입니다."
    elif months < 24:
        note = "돌 이후에는 걷기, 말문, 식사 리듬처럼 생활 변화가 커져 월령별 흐름을 함께 보는 데 도움이 됩니다."
    else:
        note = "두돌 이후에는 개월 수와 함께 연령대 표현도 같이 쓰는 경우가 많아, 1년 단위와 월 단위를 함께 확인하는 편이 좋습니다."

    return {
        "months": months,
        "label": f"{months}개월",
        "age_text": age_text,
        "stage": stage,
        "note": note,
    }


@app.get("/sitemap.xml")
def sitemap():
    sitemap_groups = tuple(
        group
        for group in SITEMAP_GROUPS
        if indexable_pages_for_sitemap(
            group,
            blog_public_indexable=False if ADSENSE_REVIEW_MODE else _is_blog_public_indexable(),
            include_hubs=not ADSENSE_REVIEW_MODE,
        )
    )
    entries = [
        _build_sitemap_index_entry(
            f"{SITE_BASE_URL}/sitemaps/{group}.xml",
        )
        for group in sitemap_groups
    ]
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{chr(10).join(entries)}\n"
        "</sitemapindex>\n"
    )
    return Response(xml, mimetype="application/xml")


@app.get("/sitemaps/<group>.xml")
def sitemap_group(group):
    if group not in SITEMAP_GROUPS:
        abort(404)

    posts = []
    if group == "guides" and BLOG_PUBLIC_INDEXING_ENABLED and not ADSENSE_REVIEW_MODE:
        db_session = SessionLocal()
        try:
            posts = _published_eligible_blog_posts(db_session)
        finally:
            db_session.close()

    blog_public_indexable = _is_blog_public_indexable(len(posts))
    entries = [
        _build_sitemap_entry(
            f"{SITE_BASE_URL}{page['path']}",
            str(page["lastmod"]),
        )
        for page in indexable_pages_for_sitemap(
            group,
            blog_public_indexable=blog_public_indexable,
            include_hubs=not ADSENSE_REVIEW_MODE,
        )
    ]
    if group == "guides" and blog_public_indexable:
        for post in posts:
            lastmod = _format_sitemap_lastmod(post.updated_at or post.published_at or post.created_at)
            entries.append(
                _build_sitemap_entry(
                    _absolute_url_for("blog_detail", slug=post.slug),
                    lastmod,
                )
            )
        for category_slug in BLOG_CATEGORIES:
            category_posts = [
                post
                for post in posts
                if BLOG_ARTICLE_BLUEPRINTS[post.slug]["category"] == category_slug
            ]
            if len(category_posts) < BLOG_CATEGORY_INDEX_MIN_POSTS:
                continue
            lastmod_value = max(
                (post.updated_at or post.published_at or post.created_at for post in category_posts),
                default=None,
            )
            entries.append(
                _build_sitemap_entry(
                    _absolute_url_for("blog_category", category_slug=category_slug),
                    _format_sitemap_lastmod(lastmod_value),
                )
            )

    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{chr(10).join(entries)}\n"
        "</urlset>\n"
    )
    return Response(xml, mimetype="application/xml")


@app.get("/rss.xml")
def public_rss():
    if ADSENSE_REVIEW_MODE or not BLOG_PUBLIC_INDEXING_ENABLED:
        abort(404)

    db_session = SessionLocal()
    try:
        eligible_posts = _published_eligible_blog_posts(db_session)
    finally:
        db_session.close()
    if not eligible_posts or not _is_blog_public_indexable(len(eligible_posts)):
        abort(404)
    posts = eligible_posts[:20]
    eligible_slug_set = {post.slug for post in eligible_posts}

    items = []
    for post in posts:
        article = BLOG_ARTICLE_BLUEPRINTS[post.slug]
        items.append(
            {
                "title": article["title"],
                "url": article["canonical_url"],
                "description": article["summary"],
                "content_html": _escape_rss_cdata(
                    render_article_content_html(article, eligible_article_slugs=eligible_slug_set)
                ),
                "published_at": _rss_date(post.published_at or post.created_at),
                "updated_at": _rss_iso_date(post.updated_at or post.published_at or post.created_at),
                "category": article["category_label"],
                "author": article["author"],
            }
        )
    xml = render_template(
        "rss.xml",
        items=items,
        feed_url=f"{SITE_BASE_URL}/rss.xml",
        blog_url=f"{SITE_BASE_URL}/blog",
        build_date=_rss_date(max((post.updated_at or post.published_at for post in posts), default=None)),
    )
    return Response(xml, mimetype="application/rss+xml")


def _validated_int_query(name, minimum, maximum):
    """Return a strict integer query value and whether it needs normalization."""
    if name not in request.args:
        return None, False
    if len(request.args.getlist(name)) != 1:
        return None, True
    raw_value = request.args.get(name, "").strip()
    if not raw_value.isdigit():
        return None, True
    value = int(raw_value)
    if raw_value != str(value):
        return None, True
    if not minimum <= value <= maximum:
        return None, True
    return value, False


def _query_keys_are_exact(*expected_keys):
    return set(request.args) == set(expected_keys) and all(
        len(request.args.getlist(key)) == 1 for key in expected_keys
    )


def _mark_result_query_noindex():
    g.result_query_noindex = True


def _validated_grade_query(valid_stage_grades):
    if not request.args:
        return "elementary", None, False
    if not _query_keys_are_exact("stage", "grade"):
        return "elementary", None, True
    stage = request.args.get("stage", "").strip()
    if stage not in valid_stage_grades:
        return "elementary", None, True
    grade, invalid_grade = _validated_int_query("grade", 1, valid_stage_grades[stage])
    return stage, grade, invalid_grade


def _short_grade_label(stage, grade):
    stage_labels = {"elementary": "초", "middle": "중", "high": "고"}
    return f"{stage_labels[stage]}{grade}"


@app.get('/')
def index():
    """메인 페이지 - 나이 계산 도구 안내"""
    return render_template('index.html', today=_current_local_date())


@app.get("/<hub_slug>/")
def life_hub(hub_slug):
    hub = HUB_PAGE_BY_SLUG.get(hub_slug)
    if hub is None:
        abort(404)
    return render_template(
        "hub-detail.html",
        hub=hub,
        hub_number=next(
            index
            for index, candidate in enumerate(HUB_PAGES, start=1)
            if candidate["key"] == hub["key"]
        ),
    )


@app.route('/age', methods=['GET', 'POST'])
def age():
    """만나이 계산 페이지 - 나이 계산 폼과 결과를 표시"""
    if request.method == 'GET' and request.args:
        return redirect(url_for('age'))

    if request.method == 'POST':
        calendar_type = request.form.get('calendar_type', 'solar')
        if calendar_type != 'lunar':
            return jsonify({
                'success': False,
                'client_only': True,
                'message': '양력 생년월일은 브라우저에서만 계산합니다.',
            }), 400

        birth_date = request.form.get('birth_date', '').strip()
        if not birth_date:
            return jsonify({'success': False, 'message': '생년월일을 입력해주세요.'}), 400

        result = AgeController().calculate_age_from_string(birth_date, 'lunar')
        response = jsonify(result)
        response.headers['Cache-Control'] = 'no-store'
        return response

    return render_template(
        'age.html',
        result=None,
        calendar_type='solar',
        page_path="/age",
        today=_current_local_date(),
    )

@app.route('/privacy')
def privacy():
    """개인정보 처리 방침 페이지"""
    return render_template('privacy.html')

@app.route('/about')
def about():
    """운영 및 편집 원칙 페이지"""
    return render_template('about.html')

@app.route('/contact')
def contact():
    """문의 및 운영자 안내 페이지"""
    return render_template('contact.html')

@app.route('/references')
def references():
    """계산 기준과 참고 자료 안내 페이지"""
    return render_template('references.html')

@app.route('/birth-year-age-table')
def birth_year_age_table():
    """출생년도별 나이표 안내 페이지"""
    today = _current_local_date()
    current_year = today.year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    selected_year, invalid_query = _validated_int_query("year", min_year, max_year)
    if invalid_query or (request.args and not _query_keys_are_exact("year")):
        return redirect(url_for("birth_year_age_table"))

    indexable_variant = selected_year == 2010
    canonical_url = f"{SITE_BASE_URL}/birth-year-age-table"
    if indexable_variant:
        canonical_url = f"{canonical_url}?year={selected_year}"
    elif selected_year is not None:
        _mark_result_query_noindex()
    g.page_canonical_url = canonical_url

    rows = []
    selected_row = None
    for year in range(max_year, min_year - 1, -1):
        row = _build_birth_year_snapshot(year, current_year)
        row["is_selected"] = year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [year for year in (1990, 2000, 2010) if min_year <= year <= max_year]
    examples = [_build_birth_year_snapshot(year, current_year) for year in example_years]

    return render_template(
        'birth-year-age-table.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        birth_year_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
        canonical_url=canonical_url,
        robots_content="index,follow" if selected_year is None or indexable_variant else "noindex,follow",
        seo_title=(
            f"{selected_year}년생 몇살? 만나이·연나이 표 | AgeCalc"
            if indexable_variant
            else "몇년생 몇살? 출생연도별 만나이·연나이 표 | AgeCalc"
        ),
    )

@app.route('/school-grade-calculator')
def school_grade_calculator():
    """출생년도 기준 학년 안내 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    selected_year, invalid_query = _validated_int_query("year", min_year, max_year)
    if invalid_query or (request.args and not _query_keys_are_exact("year")):
        return redirect(url_for("school_grade_calculator"))
    if selected_year is not None:
        _mark_result_query_noindex()

    rows = []
    selected_row = _build_school_grade_snapshot(selected_year, school_year) if selected_year else None
    for year in range(max_year, min_year - 1, -1):
        row = _build_school_grade_snapshot(year, school_year)
        row["is_selected"] = year == selected_year
        rows.append(row)

    example_years = [year for year in (2019, 2016, 2013, 2010) if 1900 <= year <= current_year]
    examples = [_build_school_grade_snapshot(year, school_year) for year in example_years]

    return render_template(
        'school-grade-calculator.html',
        school_year=school_year,
        selected_year=selected_year,
        selected_row=selected_row,
        school_grade_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
        canonical_url=f"{SITE_BASE_URL}/school-grade-calculator",
        robots_content="index,follow" if selected_year is None else "noindex,follow",
    )


@app.route('/school-entry-year-table')
def school_entry_year_table():
    """출생년도 기준 입학 학년도 안내 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    selected_year, invalid_query = _validated_int_query("year", min_year, max_year)
    if invalid_query or (request.args and not _query_keys_are_exact("year")):
        return redirect(url_for("school_entry_year_table"))
    if selected_year is not None:
        _mark_result_query_noindex()

    rows = []
    selected_row = _build_school_entry_snapshot(selected_year, school_year) if selected_year is not None else None
    for year in range(max_year, min_year - 1, -1):
        row = _build_school_entry_snapshot(year, school_year)
        row["is_selected"] = year == selected_year
        rows.append(row)

    example_years = [year for year in (2017, 2018, 2019, 2020) if 1900 <= year <= current_year]
    examples = [_build_school_entry_snapshot(year, school_year) for year in example_years]

    return render_template(
        'school-entry-year-table.html',
        school_year=school_year,
        selected_year=selected_year,
        selected_row=selected_row,
        school_entry_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
        canonical_url=f"{SITE_BASE_URL}/school-entry-year-table",
        robots_content="index,follow" if selected_year is None else "noindex,follow",
    )

@app.route('/age-gap-calculator')
def age_gap_calculator():
    """출생년도 기준 나이 차이 안내 페이지"""
    current_year = _current_local_date().year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    if request.args and not _query_keys_are_exact("year_a", "year_b"):
        return redirect(url_for("age_gap_calculator"))
    year_a, invalid_year_a = _validated_int_query("year_a", min_year, max_year)
    year_b, invalid_year_b = _validated_int_query("year_b", min_year, max_year)
    if invalid_year_a or invalid_year_b:
        return redirect(url_for("age_gap_calculator"))

    selected_gap = None
    if year_a is not None and year_b is not None:
        selected_gap = _build_age_gap_snapshot(year_a, year_b)
        _mark_result_query_noindex()

    example_pairs = [(1990, 1995), (2000, 2002), (2010, 2015)]
    examples = [
        _build_age_gap_snapshot(a, b)
        for a, b in example_pairs
        if min_year <= a <= max_year and min_year <= b <= max_year
    ]

    gap_rows = []
    for gap in range(0, 13):
        if gap == 0:
            note = "같은 출생년도라서 동갑인 경우입니다."
            man_gap = "만 0세 차이"
        else:
            note = f"연나이는 {gap}세 차이이고, 만나이는 생일 전후에 따라 {gap - 1}~{gap}세 차이로 보일 수 있습니다."
            man_gap = f"만 {gap - 1}~{gap}세 차이"
        gap_rows.append({
            "gap": f"{gap}년 차이",
            "man_gap": man_gap,
            "note": note,
        })

    return render_template(
        'age-gap-calculator.html',
        current_year=current_year,
        year_options=range(max_year, min_year - 1, -1),
        selected_year_a=year_a,
        selected_year_b=year_b,
        selected_gap=selected_gap,
        examples=examples,
        gap_rows=gap_rows,
    )

@app.route('/100-day-calculator')
def hundred_day_calculator():
    """시작일 기준 100일째 날짜 안내 페이지"""
    if request.args:
        return redirect(url_for('hundred_day_calculator'))

    today = _current_local_date()
    current_year = today.year

    example_inputs = [
        ("커플 100일 예시", today - timedelta(days=30)),
        ("아기 백일 예시", today - timedelta(days=99)),
        ("프로젝트 회고 예시", today - timedelta(days=140)),
    ]
    examples = []
    for title, start_date in example_inputs:
        example = _build_hundred_day_snapshot(start_date, today)
        example["title"] = title
        examples.append(example)

    return render_template(
        '100-day-calculator.html',
        today=today,
        current_year=current_year,
        examples=examples,
    )


@app.route('/baby-months-table')
def baby_months_table():
    """생후 개월 수 기준 안내 페이지"""
    if request.args and not _query_keys_are_exact("months"):
        return redirect(url_for("baby_months_table"))
    selected_months, invalid_query = _validated_int_query("months", 0, 36)
    if invalid_query:
        return redirect(url_for("baby_months_table"))
    if selected_months is not None:
        _mark_result_query_noindex()

    month_rows = [_build_baby_month_snapshot(months) for months in range(0, 37)]
    selected_row = _build_baby_month_snapshot(selected_months) if selected_months is not None else None
    examples = [_build_baby_month_snapshot(months) for months in (6, 12, 18, 24, 36)]

    return render_template(
        'baby-months-table.html',
        selected_months=selected_months,
        selected_row=selected_row,
        month_rows=month_rows,
        month_options=range(0, 37),
        examples=examples,
    )


@app.route('/annual-age-calculator')
def annual_age_calculator():
    """출생연도 기준 연나이 안내 페이지"""
    today = _current_local_date()
    current_year = today.year
    min_year = 1900
    max_year = current_year

    if request.args and not _query_keys_are_exact("birth_year"):
        return redirect(url_for('annual_age_calculator'))
    birth_year, invalid_query = _validated_int_query("birth_year", min_year, max_year)
    if invalid_query:
        return redirect(url_for("annual_age_calculator"))
    selected_birth_date = (
        date(birth_year, 1, 1)
        if birth_year is not None and min_year <= birth_year <= max_year
        else None
    )
    selected_snapshot = _build_annual_age_snapshot(selected_birth_date, current_year) if selected_birth_date else None
    invalid_date = birth_year is not None and selected_snapshot is None
    if selected_snapshot is not None:
        _mark_result_query_noindex()

    example_dates = [
        datetime(1990, 1, 1).date(),
        datetime(2000, 6, 15).date(),
        datetime(2010, 12, 31).date(),
    ]
    examples = [_build_annual_age_snapshot(example_date, current_year) for example_date in example_dates]

    return render_template(
        'annual-age-calculator.html',
        current_year=current_year,
        today=today,
        selected_snapshot=selected_snapshot,
        invalid_date=invalid_date,
        birth_year=birth_year,
        examples=examples,
    )


@app.route('/age-comparison-table')
def age_comparison_table():
    """만나이와 연나이 비교 안내 페이지"""
    current_year = _current_local_date().year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    if request.args and not _query_keys_are_exact("year"):
        return redirect(url_for("age_comparison_table"))
    selected_year, invalid_query = _validated_int_query("year", min_year, max_year)
    if invalid_query:
        return redirect(url_for("age_comparison_table"))
    if selected_year is not None:
        _mark_result_query_noindex()

    rows = []
    selected_row = None
    for year in range(max_year, min_year - 1, -1):
        row = _build_age_comparison_snapshot(year, current_year)
        row["is_selected"] = year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [year for year in (1990, 1992, 2000, 2010) if min_year <= year <= max_year]
    examples = [_build_age_comparison_snapshot(year, current_year) for year in example_years]

    return render_template(
        'age-comparison-table.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        comparison_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
    )


@app.route('/grade-age-table')
def grade_age_table():
    """학년 기준 나이표 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year

    valid_stage_grades = {"elementary": 6, "middle": 3, "high": 3}
    stage, grade, invalid_query = _validated_grade_query(valid_stage_grades)
    if invalid_query:
        return redirect(url_for("grade_age_table"))

    rows = []
    for stage_key, max_grade in valid_stage_grades.items():
        for grade_number in range(1, max_grade + 1):
            row = _build_grade_age_snapshot(stage_key, grade_number, school_year, current_year)
            row["is_selected"] = stage_key == stage and grade_number == grade
            rows.append(row)

    selected_row = _build_grade_age_snapshot(stage, grade, school_year, current_year) if grade is not None else None
    if selected_row is not None:
        _mark_result_query_noindex()
    examples = [
        _build_grade_age_snapshot("elementary", 1, school_year, current_year),
        _build_grade_age_snapshot("middle", 1, school_year, current_year),
        _build_grade_age_snapshot("high", 1, school_year, current_year),
    ]
    featured_grade_rows = [
        _build_grade_age_snapshot("middle", 1, school_year, current_year),
        _build_grade_age_snapshot("middle", 3, school_year, current_year),
        _build_grade_age_snapshot("high", 1, school_year, current_year),
        _build_grade_age_snapshot("high", 3, school_year, current_year),
    ]
    seo_description = (
        f"{school_year}학년도 중1 {featured_grade_rows[0]['annual_age']}, "
        f"중3 {featured_grade_rows[1]['annual_age']}, "
        f"고1 {featured_grade_rows[2]['annual_age']}, "
        f"고3 {featured_grade_rows[3]['annual_age']}의 연나이와 생일 전후 만나이 범위를 "
        "확인하는 학년별 나이표입니다."
    )

    return render_template(
        'grade-age-table.html',
        school_year=school_year,
        selected_stage=stage,
        selected_grade=grade,
        selected_row=selected_row,
        grade_rows=rows,
        examples=examples,
        featured_grade_rows=featured_grade_rows,
        seo_description=seo_description,
        canonical_url=(
            f"{SITE_BASE_URL}/grade-age-table"
        ),
        robots_content="index,follow" if grade is None else "noindex,follow",
        seo_title=(
            f"{_short_grade_label(stage, grade)} 나이 | 연나이·만나이 범위 | AgeCalc"
            if grade is not None
            else "학년별 나이표 | 중1·중3·고1·고3은 몇 살? | AgeCalc"
        ),
    )


@app.route('/pet-age-table')
def pet_age_table():
    """반려동물 나이표 페이지"""
    if request.args and not _query_keys_are_exact("pet", "years", "size"):
        return redirect(url_for("pet_age_table"))
    pet = request.args.get("pet", "dog").strip()
    size = request.args.get("size", "small").strip()
    years, invalid_years = _validated_int_query("years", 1, 20)
    if invalid_years or pet not in {"dog", "cat"} or size not in DOG_HUMAN_AGE_TABLE:
        return redirect(url_for("pet_age_table"))
    if years is not None:
        _mark_result_query_noindex()

    selected_row = _build_pet_age_snapshot(pet, years, size) if years is not None else None

    dog_rows = []
    for age in range(1, 17):
        dog_rows.append({
            "years_label": f"{age}살",
            "small": f"{_calc_dog_human_age(age, 'small')}세",
            "medium": f"{_calc_dog_human_age(age, 'medium')}세",
            "large": f"{_calc_dog_human_age(age, 'large')}세",
            "giant": f"{_calc_dog_human_age(age, 'giant')}세",
        })

    cat_rows = []
    for age in range(1, 17):
        cat_rows.append({
            "years_label": f"{age}살",
            "human_age": f"{_calc_cat_human_age(age)}세",
        })

    examples = [
        _build_pet_age_snapshot("dog", 1, "small"),
        _build_pet_age_snapshot("dog", 7, "large"),
        _build_pet_age_snapshot("cat", 2),
    ]

    return render_template(
        'pet-age-table.html',
        pet=pet,
        years=years,
        size=size,
        selected_row=selected_row,
        dog_rows=dog_rows,
        cat_rows=cat_rows,
        examples=examples,
    )


@app.route('/korean-age-guide')
def korean_age_guide():
    """한국나이 폐지 이후 기준 정리 페이지"""
    return render_template('korean-age-guide.html')


@app.route('/pet-months-table')
def pet_months_table():
    """반려동물 월령표 페이지"""
    if request.args and not _query_keys_are_exact("pet", "months", "size"):
        return redirect(url_for("pet_months_table"))
    pet = request.args.get("pet", "dog").strip()
    size = request.args.get("size", "small").strip()
    months, invalid_months = _validated_int_query("months", 1, 24)
    if invalid_months or pet not in {"dog", "cat"} or size not in DOG_HUMAN_AGE_TABLE:
        return redirect(url_for("pet_months_table"))
    if months is not None:
        _mark_result_query_noindex()

    selected_row = _build_pet_month_snapshot(pet, months, size) if months is not None else None

    dog_rows = []
    for month_value in range(1, 25):
        dog_rows.append({
            "months_label": f"{month_value}개월",
            "age_text": _format_years_months(month_value),
            "small": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'small'))}세",
            "medium": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'medium'))}세",
            "large": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'large'))}세",
            "giant": f"약 {round(_calc_dog_human_age_precise(month_value / 12, 'giant'))}세",
        })

    cat_rows = []
    for month_value in range(1, 25):
        cat_rows.append({
            "months_label": f"{month_value}개월",
            "age_text": _format_years_months(month_value),
            "human_age": f"약 {round(_calc_cat_human_age_precise(month_value / 12))}세",
        })

    examples = [
        _build_pet_month_snapshot("dog", 3, "small"),
        _build_pet_month_snapshot("dog", 12, "large"),
        _build_pet_month_snapshot("cat", 6),
    ]

    return render_template(
        'pet-months-table.html',
        pet=pet,
        months=months,
        size=size,
        selected_row=selected_row,
        dog_rows=dog_rows,
        cat_rows=cat_rows,
        examples=examples,
    )


@app.route('/grade-birth-year-table')
def grade_birth_year_table():
    """학년별 출생연도표 페이지"""
    today = _current_local_date()
    school_year = _current_school_year(today)
    current_year = today.year

    valid_stage_grades = {"elementary": 6, "middle": 3, "high": 3}
    stage, grade, invalid_query = _validated_grade_query(valid_stage_grades)
    if invalid_query:
        return redirect(url_for("grade_birth_year_table"))

    rows = []
    for stage_key, max_grade in valid_stage_grades.items():
        for grade_number in range(1, max_grade + 1):
            row = _build_grade_birth_year_snapshot(stage_key, grade_number, school_year, current_year)
            row["is_selected"] = stage_key == stage and grade_number == grade
            rows.append(row)

    selected_row = _build_grade_birth_year_snapshot(stage, grade, school_year, current_year) if grade is not None else None
    if selected_row is not None:
        _mark_result_query_noindex()
    examples = [
        _build_grade_birth_year_snapshot("elementary", 1, school_year, current_year),
        _build_grade_birth_year_snapshot("middle", 1, school_year, current_year),
        _build_grade_birth_year_snapshot("high", 1, school_year, current_year),
    ]
    faq_grade_rows = [
        _build_grade_birth_year_snapshot("middle", 1, school_year, current_year),
        _build_grade_birth_year_snapshot("high", 1, school_year, current_year),
        _build_grade_birth_year_snapshot("high", 3, school_year, current_year),
    ]
    seo_description = (
        f"{school_year}학년도 중1은 {faq_grade_rows[0]['birth_year_label']}, "
        f"고1은 {faq_grade_rows[1]['birth_year_label']}, "
        f"고3은 {faq_grade_rows[2]['birth_year_label']}입니다. "
        "학년별 일반 출생연도와 빠른년생·입학유예 예외를 확인하세요."
    )

    return render_template(
        'grade-birth-year-table.html',
        school_year=school_year,
        selected_stage=stage,
        selected_grade=grade,
        selected_row=selected_row,
        grade_rows=rows,
        examples=examples,
        faq_grade_rows=faq_grade_rows,
        seo_description=seo_description,
        canonical_url=(
            f"{SITE_BASE_URL}/grade-birth-year-table"
        ),
        robots_content="index,follow" if grade is None else "noindex,follow",
        seo_title=(
            f"{_short_grade_label(stage, grade)} 몇 년생? 출생연도표 | AgeCalc"
            if grade is not None
            else "학년별 출생연도표 | 중1·고1은 몇 년생? | AgeCalc"
        ),
    )


@app.route('/birth-year-zodiac-table')
def birth_year_zodiac_table():
    """출생연도별 띠표 페이지"""
    current_year = _current_local_date().year
    min_year = max(1900, current_year - 100)
    max_year = current_year

    if request.args and not _query_keys_are_exact("year"):
        return redirect(url_for("birth_year_zodiac_table"))
    selected_year, invalid_query = _validated_int_query("year", min_year, max_year)
    if invalid_query:
        return redirect(url_for("birth_year_zodiac_table"))
    if selected_year is not None:
        _mark_result_query_noindex()

    rows = []
    selected_row = None
    for year in range(max_year, min_year - 1, -1):
        row = _build_birth_year_zodiac_snapshot(year, current_year)
        row["is_selected"] = year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [year for year in (1990, 2000, 2012, 2024) if min_year <= year <= max_year]
    examples = [_build_birth_year_zodiac_snapshot(year, current_year) for year in example_years]

    return render_template(
        'birth-year-zodiac-table.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        zodiac_rows=rows,
        year_options=range(max_year, min_year - 1, -1),
        examples=examples,
    )


@app.route('/college-entry-year-calculator')
def college_entry_year_calculator():
    """대학 학번 나이 계산기 페이지"""
    current_year = _current_local_date().year
    min_entry_year = max(1990, current_year - 20)
    max_entry_year = current_year + 1

    selected_year, invalid_query = _validated_int_query("year", min_entry_year, max_entry_year)
    if invalid_query or (request.args and not _query_keys_are_exact("year")):
        return redirect(url_for("college_entry_year_calculator"))

    indexable_variant = selected_year in INDEXABLE_COLLEGE_ENTRY_YEARS
    canonical_url = f"{SITE_BASE_URL}/college-entry-year-calculator"
    if indexable_variant:
        canonical_url = f"{canonical_url}?year={selected_year}"
    elif selected_year is not None:
        _mark_result_query_noindex()
    g.page_canonical_url = canonical_url

    rows = []
    selected_row = None
    for entry_year in range(max_entry_year, min_entry_year - 1, -1):
        row = _build_college_entry_snapshot(entry_year, current_year)
        row["is_selected"] = entry_year == selected_year
        rows.append(row)
        if row["is_selected"]:
            selected_row = row

    example_years = [
        year
        for year in COLLEGE_ENTRY_EXAMPLE_YEARS
        if min_entry_year <= year <= max_entry_year
    ]
    examples = [_build_college_entry_snapshot(year, current_year) for year in example_years]

    if selected_row is not None:
        cohort_label = str(selected_row["cohort_label"])
        seo_title = f"{cohort_label} 나이·몇년생 | 학번 계산기 | AgeCalc"
        seo_description = (
            f"{cohort_label}은 일반적인 진학 기준으로 {selected_row['birth_year_label']}이며, "
            f"{current_year}년 기준 연나이 {selected_row['annual_age']}·{selected_row['man_age_range']}입니다. "
            "재수·편입·학교별 학번 차이도 안내합니다."
        )
        og_title = seo_title
        og_description = seo_description
    else:
        seo_title = "학번 계산기 | 몇 학번·학번 나이·몇년생 확인 | AgeCalc"
        seo_description = "26학번 몇년생, 26학번 나이, 22학번 나이, 09학번 몇살처럼 학번 기준 출생연도와 현재 나이를 확인하는 대학 학번 계산기입니다."
        og_title = "대학 학번 계산기 | AgeCalc"
        og_description = "26학번 몇년생, 26학번 나이, 22학번 나이처럼 학번 기준 출생연도와 현재 나이를 한 화면에서 정리했습니다."

    return render_template(
        'college-entry-year-calculator.html',
        current_year=current_year,
        selected_year=selected_year,
        selected_row=selected_row,
        college_rows=rows,
        year_options=range(max_entry_year, min_entry_year - 1, -1),
        examples=examples,
        indexable_years=INDEXABLE_COLLEGE_ENTRY_YEARS,
        canonical_url=canonical_url,
        robots_content="index,follow" if selected_year is None or indexable_variant else "noindex,follow",
        seo_title=seo_title,
        seo_description=seo_description,
        og_title=og_title,
        og_description=og_description,
    )


@app.route('/birthday-dday-calculator')
def birthday_dday_calculator():
    """생일 D-day 계산기 페이지"""
    today = _current_local_date()
    if request.args and not _query_keys_are_exact("month", "day"):
        return redirect(url_for("birthday_dday_calculator"))
    month, invalid_month = _validated_int_query("month", 1, 12)
    day, invalid_day = _validated_int_query("day", 1, 31)
    if invalid_month or invalid_day:
        return redirect(url_for("birthday_dday_calculator"))

    selected_month_day = _parse_month_day(month, day)
    selected_snapshot = None
    invalid_date = month is not None and day is not None and selected_month_day is None
    if invalid_date:
        return redirect(url_for("birthday_dday_calculator"))

    if selected_month_day is not None:
        selected_snapshot = _build_birthday_dday_snapshot(selected_month_day[0], selected_month_day[1], today)
        _mark_result_query_noindex()

    example_inputs = [(1, 1), (5, 10), (12, 25)]
    examples = [
        _build_birthday_dday_snapshot(example_month, example_day, today)
        for example_month, example_day in example_inputs
    ]

    return render_template(
        'birthday-dday-calculator.html',
        today=today,
        month=month,
        day=day,
        selected_snapshot=selected_snapshot,
        invalid_date=invalid_date,
        examples=examples,
    )

@app.route('/terms')
def terms():
    """이용 약관 페이지"""
    return render_template('terms.html')

@app.route('/guide')
def guide():
    """가이드 페이지"""
    return render_template('guide.html')

@app.route('/guides/<slug>')
def guide_detail(slug):
    """Static AdSense approval guide page."""
    page = GUIDE_PAGE_BY_SLUG.get(slug)
    if page is None:
        abort(404)
    g.page_canonical_url = f"{SITE_BASE_URL}{page['canonical_path']}"
    response = make_response(render_template('guide-detail.html', page=page))
    if not page["indexable"]:
        response.headers["X-Robots-Tag"] = "noindex, follow"
    return response

@app.route('/faq')
def faq():
    """자주 묻는 질문 페이지"""
    return render_template('faq.html')

@app.route('/dog')
def dog():
    """강아지 나이 계산 페이지"""
    return render_template('dog.html')

@app.route('/cat')
def cat():
    """고양이 나이 계산 페이지"""
    return render_template('cat.html')

@app.route('/baby-months')
def baby_months():
    """아기 개월 수 계산 페이지"""
    return render_template('baby-months.html')

@app.route('/d-day')
def d_day():
    """기념일/D-Day 계산 페이지"""
    return render_template('d-day.html')

@app.route('/parent-child')
def parent_child():
    """부모·자녀 나이 관계 계산 페이지"""
    if request.args:
        return redirect(url_for('parent_child'))
    return render_template('parent-child.html')


@app.post("/page-feedback")
def page_feedback():
    data = request.get_json(silent=True) or {}
    page_path = (data.get("page_path") or "").strip()
    vote = (data.get("vote") or "").strip()
    if not _is_valid_page_feedback_payload(page_path, vote):
        return jsonify({"ok": False}), 400

    db_session = SessionLocal()
    try:
        db_session.add(PageFeedback(page_path=page_path, vote=vote))
        db_session.commit()
    except Exception:
        if hasattr(db_session, "rollback"):
            db_session.rollback()
        return jsonify({"ok": False}), 500
    finally:
        db_session.close()

    return jsonify({"ok": True}), 201


@app.route('/blog')
def blog_list():
    page = request.args.get('page', default=1, type=int)
    page = max(page, 1)
    per_page = 8
    session = SessionLocal()

    posts = _published_eligible_blog_posts(session)

    total = len(posts)
    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    if page > total_pages:
        abort(404)

    posts = posts[(page - 1) * per_page : page * per_page]
    blog_indexable = _is_blog_public_indexable(total)
    response = make_response(render_template(
        'blog-list.html',
        posts=posts,
        page=page,
        total_pages=total_pages,
        total=total,
        blog_indexable=blog_indexable,
        canonical_url=(f"{SITE_BASE_URL}/blog" if page == 1 else f"{SITE_BASE_URL}/blog?page={page}"),
        categories=BLOG_CATEGORIES,
        article_by_slug=BLOG_ARTICLE_BLUEPRINTS,
    ))
    if not blog_indexable:
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.route('/blog/category/<category_slug>')
def blog_category(category_slug):
    if category_slug not in BLOG_CATEGORIES or ADSENSE_REVIEW_MODE:
        abort(404)

    page = max(request.args.get('page', default=1, type=int), 1)
    per_page = 8
    category_slugs = {
        slug
        for slug in _eligible_public_blog_slugs()
        if BLOG_ARTICLE_BLUEPRINTS[slug]["category"] == category_slug
    }
    db_session = SessionLocal()
    try:
        posts = [
            post
            for post in _published_eligible_blog_posts(db_session)
            if post.slug in category_slugs
        ]
    finally:
        db_session.close()

    total = len(posts)
    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    if page > total_pages:
        abort(404)
    page_posts = posts[(page - 1) * per_page : page * per_page]
    category_indexable = _is_blog_public_indexable() and total >= BLOG_CATEGORY_INDEX_MIN_POSTS
    canonical_url = f"{SITE_BASE_URL}/blog/category/{category_slug}"
    if page > 1:
        canonical_url = f"{canonical_url}?page={page}"

    response = make_response(
        render_template(
            'blog-category.html',
            posts=page_posts,
            total=total,
            page=page,
            total_pages=total_pages,
            category_slug=category_slug,
            category_label=BLOG_CATEGORIES[category_slug],
            category_editorial_content=CATEGORY_PAGE_EDITORIAL_CONTENT.get(category_slug),
            category_indexable=category_indexable,
            canonical_url=canonical_url,
            article_by_slug=BLOG_ARTICLE_BLUEPRINTS,
        )
    )
    if not category_indexable:
        response.headers["X-Robots-Tag"] = "noindex, follow"
    return response


@app.route('/blog/<slug>')
def blog_detail(slug):
    session = SessionLocal()
    post = (
        session.query(GeneratedPost)
        .filter(GeneratedPost.slug == slug, GeneratedPost.status == "published")
        .first()
    )
    article = structured_blog_article_for_slug(slug)
    is_public_article = (
        post is not None
        and post.status == "published"
        and bool(article)
        and _article_is_publicly_eligible(article)
        and audit_post(post, require_cover_image=True).keep
    )
    if not is_public_article:
        if hasattr(session, "close"):
            session.close()
        abort(404)

    blog_indexable = _is_blog_public_indexable()
    eligible_related_slugs = (
        {eligible_post.slug for eligible_post in _published_eligible_blog_posts(session)}
        if blog_indexable
        else set()
    )
    crumb_label = article["title"] if article else post.title
    breadcrumbs = [
        {"label": "홈", "url": f"{SITE_BASE_URL}/", "current": False},
        {"label": "블로그", "url": f"{SITE_BASE_URL}/blog", "current": False},
        *(
            [
                {
                    "label": article["category_label"],
                    "url": f"{SITE_BASE_URL}/blog/category/{article['category']}",
                    "current": False,
                }
            ]
            if article
            else []
        ),
        {
            "label": crumb_label,
            "url": f"{SITE_BASE_URL}/blog/{slug}",
            "current": True,
        },
    ]
    breadcrumb_schema = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {
                "@type": "ListItem",
                "position": position,
                "name": item["label"],
                "item": item["url"],
            }
            for position, item in enumerate(breadcrumbs, start=1)
        ],
    }
    response = make_response(
        render_template(
            'blog-detail.html',
            post=post,
            draft_mode=False,
            review_mode=False,
            blog_indexable=blog_indexable,
            structured_article=article,
            structured_image_url=_absolute_article_thumbnail(article) if article else None,
            article_schema=_blog_article_schema(post, article) if article and blog_indexable else None,
            breadcrumbs=breadcrumbs,
            breadcrumb_schema=breadcrumb_schema,
            eligible_related_slugs=eligible_related_slugs,
        )
    )
    if hasattr(session, "close"):
        session.close()
    if not blog_indexable:
        response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.route('/blog/drafts', methods=['GET', 'POST'])
def blog_drafts():
    error = None

    if request.method == 'POST':
        _require_valid_csrf()
        ip_address = request.remote_addr or "unknown"
        if _draft_login_is_limited(ip_address):
            return render_template(
                'blog-drafts.html',
                access_granted=False,
                error='로그인 시도가 너무 많습니다. 15분 뒤 다시 시도하세요.',
                posts=[],
            ), 429
        if _draft_password_is_valid(request.form.get('password', '')):
            _clear_draft_login_failures(ip_address)
            session.permanent = True
            session[BLOG_DRAFT_ACCESS_SESSION_KEY] = True
            return redirect(url_for('blog_drafts'))
        _record_draft_login_failure(ip_address)
        error = '비밀번호가 올바르지 않습니다.'

    if not _draft_access_granted():
        return render_template(
            'blog-drafts.html',
            access_granted=False,
            error=error,
            posts=[],
        )

    db_session = SessionLocal()
    posts = (
        db_session.query(GeneratedPost)
        .filter(GeneratedPost.status.in_(["draft", "needs_review"]))
        .order_by(GeneratedPost.created_at.desc(), GeneratedPost.id.desc())
        .all()
    )
    return render_template(
        'blog-drafts.html',
        access_granted=True,
        error=None,
        posts=posts,
    )


@app.post('/blog/drafts/logout')
def blog_drafts_logout():
    _require_valid_csrf()
    session.pop(BLOG_DRAFT_ACCESS_SESSION_KEY, None)
    session.pop(BLOG_CSRF_SESSION_KEY, None)
    return redirect(url_for('blog_drafts'))


@app.route('/blog/drafts/<slug>')
def blog_draft_detail(slug):
    if not _draft_access_granted():
        return redirect(url_for('blog_drafts'))

    db_session = SessionLocal()
    post = (
        db_session.query(GeneratedPost)
        .filter(GeneratedPost.slug == slug, GeneratedPost.status.in_(["draft", "needs_review"]))
        .first()
    )
    if post is None:
        abort(404)
    return render_template(
        'blog-detail.html',
        post=post,
        draft_mode=True,
        review_mode=False,
        structured_article=_structured_blog_context(post),
    )


@app.post('/blog/drafts/<slug>/publish')
def blog_draft_publish(slug):
    if not _draft_access_granted():
        return redirect(url_for('blog_drafts'))
    _require_valid_csrf()

    db_session = SessionLocal()
    post = (
        db_session.query(GeneratedPost)
        .filter(GeneratedPost.slug == slug, GeneratedPost.status == "draft")
        .first()
    )
    if post is None:
        abort(404)

    audit_result = audit_post(post, require_cover_image=True)
    if not audit_result.keep:
        draft_publish_errors = [issue.message for issue in audit_result.issues]
        return (
            render_template(
                'blog-detail.html',
                post=post,
                draft_mode=True,
                review_mode=False,
                draft_publish_errors=draft_publish_errors,
                structured_article=_structured_blog_context(post),
            ),
            400,
        )

    post.status = "published"
    post.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db_session.commit()
    _invalidate_blog_public_count_cache()
    return redirect(url_for('blog_detail', slug=post.slug))


@app.route('/blog/review/<int:post_id>')
def blog_review(post_id):
    token = request.args.get("token", "")
    if not _review_token_is_valid(token):
        abort(403)

    db_session = SessionLocal()
    post = db_session.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    if post is None:
        abort(404)
    response = make_response(render_template(
        'blog-detail.html',
        post=post,
        draft_mode=False,
        review_mode=True,
        review_token=token,
        review_errors=[],
        structured_article=_structured_blog_context(post),
    ))
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@app.post('/blog/review/<int:post_id>/approve')
def blog_review_approve(post_id):
    _require_valid_csrf()
    token = request.form.get("review_token", "")
    if not _review_token_is_valid(token):
        abort(403)

    db_session = SessionLocal()
    post = db_session.query(GeneratedPost).filter(GeneratedPost.id == post_id).first()
    if post is None:
        abort(404)
    audit_result = audit_post(post, require_cover_image=True)
    if not audit_result.keep:
        review_errors = [issue.message for issue in audit_result.issues]
        response = make_response(
            render_template(
                'blog-detail.html',
                post=post,
                draft_mode=False,
                review_mode=True,
                review_token=token,
                review_errors=review_errors,
                structured_article=_structured_blog_context(post),
            ), 400,
        )
        response.headers["Cache-Control"] = "no-store"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
    if post.status != "published":
        post.status = "published"
        post.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
        db_session.commit()
        _invalidate_blog_public_count_cache()
    return redirect(url_for('blog_detail', slug=post.slug))

@app.route('/minigames')
def minigames():
    """미니게임 모음 페이지"""
    return render_template('minigames.html')

@app.route('/minigames/guess')
def guess_game():
    """숫자 맞추기 게임 페이지"""
    return render_template('guess.html')

@app.route('/minigames/snake')
def snake_game():
    """스네이크 게임 페이지"""
    return render_template('snake.html')

@app.route('/minigames/tictactoe')
def tictactoe_game():
    """틱택토 게임 페이지"""
    return render_template('tictactoe.html')

@app.route('/minigames/rps')
def rps_game():
    """가위바위보 게임 페이지"""
    return render_template('rps.html')

@app.route('/minigames/nim')
def nim_game():
    """님 게임 페이지"""
    return render_template('nim.html')

@app.route('/minigames/pong')
def pong_game():
    """퐁 게임 페이지"""
    return render_template('pong.html')

@app.route('/minigames/hangman')
def hangman_game():
    """행맨 게임 페이지"""
    return render_template('hangman.html')

@app.route('/minigames/memory')
def memory_game():
    """메모리 매치 게임 페이지"""
    return render_template('memory.html')

@app.route('/minigames/connect4')
def connect4_game():
    """커넥트4 게임 페이지"""
    return render_template('connect4.html')

@app.route('/minigames/lightsout')
def lightsout_game():
    """라이츠아웃 게임 페이지"""
    return render_template('lightsout.html')

@app.route('/minigames/minesweeper')
def minesweeper_game():
    """지뢰찾기 게임 페이지"""
    return render_template('minesweeper.html')

@app.route('/minigames/simon')
def simon_game():
    """사이먼 게임 페이지"""
    return render_template('simon.html')

@app.route('/minigames/2048')
def game_2048():
    """2048 게임 페이지"""
    return render_template('2048.html')

@app.route('/minigames/blackjack')
def blackjack_game():
    """블랙잭 게임 페이지"""
    return render_template('blackjack.html')

@app.route('/minigames/breakout')
def breakout_game():
    """브레이크아웃 게임 페이지"""
    return render_template('breakout.html')

@app.route('/minigames/hanoi')
def hanoi_game():
    """하노이 게임 페이지"""
    return render_template('hanoi.html')

@app.route('/minigames/pig')
def pig_game():
    """피그 다이스 게임 페이지"""
    return render_template('pig.html')

@app.route('/minigames/gomoku')
def gomoku_game():
    """오목 게임 페이지"""
    return render_template('gomoku.html')

@app.route('/minigames/reversi')
def reversi_game():
    """리버시 게임 페이지"""
    return render_template('reversi.html')

@app.route('/minigames/dotsandboxes')
def dotsandboxes_game():
    """점 잇기 게임 페이지"""
    return render_template('dotsandboxes.html')

@app.route('/minigames/mancala')
def mancala_game():
    """만칼라 게임 페이지"""
    return render_template('mancala.html')

@app.route('/minigames/mastermind')
def mastermind_game():
    """마스터마인드 게임 페이지"""
    return render_template('mastermind.html')

@app.route('/minigames/war')
def war_game():
    """카드 전쟁 게임 페이지"""
    return render_template('war.html')

@app.route('/minigames/battleship')
def battleship_game():
    """해전 게임 페이지"""
    return render_template('battleship.html')

@app.route('/minigames/checkers')
def checkers_game():
    """체커 게임 페이지"""
    return render_template('checkers.html')

@app.route('/minigames/fifteen')
def fifteen_game():
    """15 퍼즐 게임 페이지"""
    return render_template('fifteen.html')

@app.route('/minigames/pegsolitaire')
def pegsolitaire_game():
    """페그 솔리테어 게임 페이지"""
    return render_template('pegsolitaire.html')

@app.route('/minigames/yahtzee')
def yahtzee_game():
    """야추 게임 페이지"""
    return render_template('yahtzee.html')



@app.post("/snake-score")
def snake_score():
    data = request.get_json(silent=True) or {}
    try:
        score = int(data.get("score", 0))
    except (TypeError, ValueError):
        score = 0
    if score < 0:
        score = 0

    now = datetime.now()
    today = _date_key(now)
    month = _month_key(now)

    with _score_lock:
        scores = _load_scores()
        today_scores = [s for s in scores if s.get("date") == today]
        prev_daily_best = max([s.get("score", 0) for s in today_scores], default=0)
        scores.append({
            "score": score,
            "ts": now.isoformat(),
            "date": today,
            "month": month
        })
        # Keep recent 5000 scores
        if len(scores) > 5000:
            scores = scores[-5000:]
        _save_scores(scores)

    today_scores = [s for s in scores if s.get("date") == today]
    month_scores = [s for s in scores if s.get("month") == month]
    daily_best = max([s.get("score", 0) for s in today_scores], default=0)
    monthly_best = max([s.get("score", 0) for s in month_scores], default=0)
    higher = sum(1 for s in today_scores if s.get("score", 0) > score)
    rank = higher + 1
    total = len(today_scores)
    is_new_daily_best = score > prev_daily_best and score > 0
    return jsonify({
        "ok": True,
        "rank": rank,
        "total": total
    })


if __name__ == '__main__':
    app.run(debug=True, port=8000, host='0.0.0.0')
