#!/usr/bin/env python3
import argparse
import base64
import hashlib
import html
import json
import os
from pathlib import Path
import re
import smtplib
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from email.message import EmailMessage
from typing import Any

from sqlalchemy import or_, select

# Allow running via `python /path/to/scripts/rss_blog_scheduler.py`
# without requiring the project root on PYTHONPATH.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

ENV_FILE = PROJECT_ROOT / ".env.rss"


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

from db import SessionLocal, init_db
from models.blog_models import FeedItem, FeedSource, GeneratedPost, PostSource


DEFAULT_TIMEOUT = 15
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_OLLAMA_MODEL = "mistral:latest"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OPENAI_IMAGE_MODEL = "gpt-image-1"
DEFAULT_IMAGE_SIZE = "1536x1024"
DEFAULT_IMAGE_COUNT = 1
DEFAULT_IMAGE_QUALITY = "medium"
DEFAULT_SMTP_PORT = 25
IMAGE_OUTPUT_DIR = PROJECT_ROOT / "static" / "generated" / "blog-covers"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
DEFAULT_BLOG_COVER_PROMPT = """
한국어 건강/육아 정보 블로그용 커버 이미지를 제작해.

목표:
- 따뜻하고 신뢰감 있는 에디토리얼 일러스트 스타일
- 텍스트가 이미지 안에 들어가지 않게
- 썸네일과 블로그 커버로 쓰기 좋은 16:9 느낌의 안정적인 구도
- 과장 광고 느낌, 선정적 표현, 자극적 대비 금지
- 의료/육아 주제라도 불안감을 과도하게 자극하지 않게

이미지 방향:
- 블로그 메인 커버로 사용할 이미지 1장을 생성한다.
- 16:9 비율에 어울리는 안정적인 구도로 구성한다.

주제 제목: {title}
요약: {excerpt}
본문 핵심: {body}
""".strip()


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value.strip())


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def _load_prompt_template(name: str, fallback: str) -> str:
    path = PROMPTS_DIR / name
    if not path.exists():
        return fallback
    return path.read_text(encoding="utf-8").strip() or fallback


def _slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9가-힣\s-]", "", text or "")
    cleaned = re.sub(r"[\s_-]+", "-", cleaned).strip("-").lower()
    return cleaned[:140] or "post"


def _unique_slug(session, title: str) -> str:
    base = _slugify(title)
    candidate = base
    seq = 2
    while session.scalar(select(GeneratedPost.id).where(GeneratedPost.slug == candidate)) is not None:
        candidate = f"{base}-{seq}"
        seq += 1
    return candidate


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (TypeError, ValueError):
        pass
    try:
        v = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(v)
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (TypeError, ValueError):
        return None


def _fetch(url: str, timeout: int = DEFAULT_TIMEOUT) -> bytes:
    # Accept IRI-like input (e.g., Korean query) and normalize to ASCII URL.
    parsed = urllib.parse.urlsplit(url.strip())
    netloc = parsed.netloc.encode("idna").decode("ascii")
    path = urllib.parse.quote(parsed.path, safe="/%:@")
    query = urllib.parse.quote_plus(parsed.query, safe="=&%:+,;@()!$'*-._~")
    fragment = urllib.parse.quote(parsed.fragment, safe="%!$&'()*+,;=:@/?-._~")
    normalized_url = urllib.parse.urlunsplit((parsed.scheme, netloc, path, query, fragment))

    req = urllib.request.Request(
        normalized_url,
        headers={
            "User-Agent": "agecalc-rss-bot/1.0 (+https://agecalc.cloud)",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _text(elem: ET.Element | None, path: str, ns: dict[str, str] | None = None) -> str | None:
    if elem is None:
        return None
    found = elem.find(path, ns or {})
    if found is None:
        return None
    if found.text:
        return found.text.strip()
    return None


def _extract_atom_content(entry: ET.Element, ns: dict[str, str]) -> str:
    for tag in ("content", "summary"):
        node = entry.find(f"atom:{tag}", ns)
        if node is None:
            continue
        if node.text:
            return node.text.strip()
    return ""


def _parse_feed(content: bytes) -> list[dict[str, Any]]:
    root = ET.fromstring(content)
    tag = root.tag.lower()
    items: list[dict[str, Any]] = []

    # RSS 2.0
    if "rss" in tag or root.find("channel") is not None:
        channel = root.find("channel")
        if channel is None:
            return []
        for item in channel.findall("item"):
            link = _text(item, "link")
            title = _text(item, "title") or ""
            summary = _text(item, "description") or ""
            published = _text(item, "pubDate")
            content_encoded = ""
            for child in item:
                if child.tag.lower().endswith("encoded") and child.text:
                    content_encoded = child.text.strip()
                    break
            if not link or not title:
                continue
            items.append(
                {
                    "title": title,
                    "url": link,
                    "published_at": _parse_date(published),
                    "summary": summary,
                    "content": content_encoded or summary,
                }
            )
        return items

    # Atom
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    if "feed" in tag:
        for entry in root.findall("atom:entry", ns):
            link = ""
            for link_node in entry.findall("atom:link", ns):
                href = (link_node.attrib.get("href") or "").strip()
                rel = (link_node.attrib.get("rel") or "alternate").strip()
                if href and rel == "alternate":
                    link = href
                    break
                if href and not link:
                    link = href
            title = _text(entry, "atom:title", ns) or ""
            published = _text(entry, "atom:published", ns) or _text(entry, "atom:updated", ns)
            summary = _text(entry, "atom:summary", ns) or ""
            content_text = _extract_atom_content(entry, ns)
            if not link or not title:
                continue
            items.append(
                {
                    "title": title,
                    "url": link,
                    "published_at": _parse_date(published),
                    "summary": summary,
                    "content": content_text or summary,
                }
            )
        return items

    return []


def _content_hash(item: dict[str, Any]) -> str:
    payload = f"{item.get('title','')}|{item.get('url','')}|{item.get('summary','')}|{item.get('content','')}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _story_identity_key(source_id: int, title: str, published_at: datetime | None) -> tuple[int, str, datetime] | None:
    if published_at is None:
        return None
    return (source_id, _normalize_space(title).casefold(), published_at)


def _extract_output_text(resp_json: dict[str, Any]) -> str:
    if isinstance(resp_json.get("output_text"), str) and resp_json["output_text"].strip():
        return resp_json["output_text"].strip()

    chunks: list[str] = []
    for out in resp_json.get("output", []):
        for content in out.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def _build_generation_prompt(feed_item: FeedItem) -> str:
    return f"""
아래 원문 정보를 참고해서 한국어 블로그 글을 작성해.
조건:
- 제목 1개
- 서론 1문단, 본문 3~5개 소제목, 결론 1문단
- 사실 왜곡 금지, 출처 링크를 '참고 링크' 섹션에 1개 이상 포함
- 과장 광고 문구 금지
- 응답 형식(JSON):
  {{
    "title": "...",
    "excerpt": "...",
    "content_html": "<h2>...</h2>..."
  }}

원문 제목: {feed_item.original_title}
원문 링크: {feed_item.original_url}
원문 요약: {feed_item.summary or ""}
원문 본문 일부: {(feed_item.content or "")[:4000]}
""".strip()


def _build_image_prompt(title: str, excerpt: str, content_html: str) -> str:
    body = _normalize_space(_strip_tags(content_html))[:1200]
    template = _load_prompt_template("blog_cover_image_prompt.txt", DEFAULT_BLOG_COVER_PROMPT)
    return template.format(title=title, excerpt=excerpt, body=body)


def _parse_generated_json(text: str) -> tuple[str, str, str]:
    data = json.loads(text)
    title = _normalize_space(data.get("title", ""))
    excerpt = _normalize_space(data.get("excerpt", ""))
    content_html = data.get("content_html", "")

    if not title or not content_html:
        raise RuntimeError("response missing title/content_html")
    if not excerpt:
        excerpt = _normalize_space(_strip_tags(content_html))[:180]
    return title, excerpt, content_html


def _save_cover_bytes(data: bytes, ext: str, slug: str, suffix: str) -> str:
    IMAGE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{slug[:120]}-{suffix}{ext}"
    path = IMAGE_OUTPUT_DIR / filename
    path.write_bytes(data)
    return f"/static/generated/blog-covers/{filename}"


def _cleanup_generated_images(image_urls: list[str]) -> None:
    for image_url in image_urls:
        if not image_url.startswith("/static/generated/"):
            continue
        try:
            (PROJECT_ROOT / image_url.lstrip("/")).unlink(missing_ok=True)
        except OSError:
            pass


def _send_review_email(post: GeneratedPost) -> None:
    smtp_host = os.getenv("SMTP_HOST", "").strip()
    smtp_to = os.getenv("SMTP_TO_EMAIL", "").strip()
    review_token = (os.getenv("BLOG_REVIEW_TOKEN", "") or "").strip()
    base_url = (os.getenv("BLOG_BASE_URL", "https://agecalc.cloud") or "").rstrip("/")
    if not smtp_host or not smtp_to or not review_token:
        return

    try:
        smtp_port = int(os.getenv("SMTP_PORT", str(DEFAULT_SMTP_PORT)).strip())
    except ValueError as exc:
        raise RuntimeError("SMTP_PORT must be an integer") from exc

    smtp_username = os.getenv("SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = (os.getenv("SMTP_FROM_EMAIL", smtp_username or smtp_to) or "").strip()
    use_tls = _env_bool("SMTP_USE_TLS", default=True)
    review_url = f"{base_url}/blog/review/{post.id}?token={urllib.parse.quote(review_token)}"
    approve_url = f"{base_url}/blog/review/{post.id}/approve?token={urllib.parse.quote(review_token)}"

    msg = EmailMessage()
    msg["Subject"] = f"[AgeCalc] 블로그 초안 검토 필요: {post.title}"
    msg["From"] = smtp_from
    msg["To"] = smtp_to
    msg.set_content(
        "\n".join(
            [
                "새 블로그 초안이 생성되었습니다.",
                "",
                f"제목: {post.title}",
                f"초안 ID: {post.id}",
                f"상태: {post.status}",
                "",
                f"검토 페이지: {review_url}",
                f"즉시 승인: {approve_url}",
            ]
        )
    )

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as client:
        client.ehlo()
        if use_tls:
            client.starttls()
            client.ehlo()
        if smtp_password and not smtp_username:
            raise RuntimeError("SMTP_USERNAME is required when SMTP_PASSWORD is set")
        if smtp_username:
            client.login(smtp_username, smtp_password)
        client.send_message(msg)
    print(f"[notify] sent review email for post_id={post.id}")


def _generate_with_openai(feed_item: FeedItem, model: str) -> tuple[str, str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    body = {
        "model": model,
        "input": _build_generation_prompt(feed_item),
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )

    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    text = _extract_output_text(payload)
    if not text:
        raise RuntimeError("OpenAI response was empty")

    return _parse_generated_json(text)


def _generate_cover_with_openai(title: str, excerpt: str, content_html: str, slug: str) -> list[str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        return []

    body = {
        "model": os.getenv("OPENAI_IMAGE_MODEL", DEFAULT_OPENAI_IMAGE_MODEL),
        "prompt": _build_image_prompt(title, excerpt, content_html),
        "size": os.getenv("OPENAI_IMAGE_SIZE", DEFAULT_IMAGE_SIZE),
        "n": _env_int("OPENAI_IMAGE_COUNT", DEFAULT_IMAGE_COUNT),
        "quality": os.getenv("OPENAI_IMAGE_QUALITY", DEFAULT_IMAGE_QUALITY),
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    image_urls: list[str] = []
    for idx, item in enumerate(payload.get("data", []), start=1):
        image_data = item.get("b64_json") or ""
        if not image_data:
            continue
        image_bytes = base64.b64decode(image_data)
        image_urls.append(_save_cover_bytes(image_bytes, ".png", slug, f"openai-{idx}"))
    return image_urls


def _inject_inline_images(content_html: str, image_urls: list[str]) -> str:
    if len(image_urls) < 2:
        return content_html
    if "blog-inline-figure" in content_html:
        return content_html
    first_inline = (
        f'<figure class="blog-inline-figure"><img src="{image_urls[1]}" alt="" loading="lazy"></figure>'
    )
    return re.sub(r"</p>", f"</p>{first_inline}", content_html, count=1, flags=re.IGNORECASE)


def _generate_with_ollama(feed_item: FeedItem, model: str, base_url: str) -> tuple[str, str, str]:
    body = {
        "model": model,
        "prompt": _build_generation_prompt(feed_item),
        "stream": False,
    }
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/generate",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    text = (payload.get("response") or "").strip()
    if not text:
        raise RuntimeError("Ollama response was empty")
    return _parse_generated_json(text)


def _generate_fallback(feed_item: FeedItem) -> tuple[str, str, str]:
    title = _normalize_space(feed_item.original_title)
    summary = _normalize_space(_strip_tags(feed_item.summary or ""))
    content = _normalize_space(_strip_tags(feed_item.content or ""))

    excerpt = (summary or content or title)[:180]
    body_text = summary or content or "원문 내용을 확인해 주세요."
    safe = html.escape(body_text)
    safe_title = html.escape(title)
    safe_url = html.escape(feed_item.original_url)

    content_html = (
        f"<h2>{safe_title}</h2>"
        f"<p>{safe}</p>"
        "<h3>핵심 내용</h3>"
        f"<p>{safe}</p>"
        "<h3>참고 링크</h3>"
        f'<p><a href="{safe_url}" rel="noopener noreferrer nofollow" target="_blank">원문 보기</a></p>'
    )
    return title, excerpt, content_html


def upsert_feed_items(session, source: FeedSource, parsed_items: list[dict[str, Any]]) -> int:
    normalized_rows: list[dict[str, Any]] = []
    candidate_urls: set[str] = set()

    for item in parsed_items:
        url = (item.get("url") or "").strip()
        title = _normalize_space(item.get("title") or "")
        if not url or not title:
            continue
        normalized_rows.append(
            {
                "url": url,
                "title": title,
                "published_at": item.get("published_at"),
                "summary": item.get("summary") or "",
                "content": item.get("content") or "",
                "content_hash": _content_hash(item),
            }
        )
        candidate_urls.add(url)

    existing_urls: set[str] = set()
    if candidate_urls:
        existing_urls = set(
            session.scalars(select(FeedItem.original_url).where(FeedItem.original_url.in_(candidate_urls))).all()
        )

    candidate_titles = {row["title"] for row in normalized_rows if row["published_at"] is not None}
    existing_story_keys: set[tuple[int, str, datetime]] = set()
    if candidate_titles:
        existing_rows = session.execute(
            select(FeedItem.original_title, FeedItem.published_at)
            .where(FeedItem.source_id == source.id)
            .where(FeedItem.original_title.in_(candidate_titles))
            .where(FeedItem.published_at.is_not(None))
        ).all()
        existing_story_keys = {
            key
            for title, published_at in existing_rows
            if (key := _story_identity_key(source.id, title, published_at)) is not None
        }

    created = 0
    seen_urls: set[str] = set()
    seen_story_keys: set[tuple[int, str, datetime]] = set()
    for row in normalized_rows:
        url = row["url"]
        story_key = _story_identity_key(source.id, row["title"], row["published_at"])
        if url in existing_urls or url in seen_urls:
            continue
        if story_key is not None and (story_key in existing_story_keys or story_key in seen_story_keys):
            continue
        seen_urls.add(url)
        if story_key is not None:
            seen_story_keys.add(story_key)
        session.add(
            FeedItem(
                source_id=source.id,
                original_title=row["title"][:255],
                original_url=url[:500],
                published_at=row["published_at"],
                summary=row["summary"][:100000],
                content=row["content"][:200000],
                content_hash=row["content_hash"],
                status="new",
            )
        )
        created += 1
    return created


def ingest_sources(session, timeout: int) -> tuple[int, int]:
    total_sources = 0
    total_items = 0
    sources = session.scalars(select(FeedSource).where(FeedSource.is_active == 1)).all()
    for source in sources:
        total_sources += 1
        try:
            raw = _fetch(source.rss_url, timeout=timeout)
            parsed = _parse_feed(raw)
            created = upsert_feed_items(session, source, parsed)
            total_items += created
            print(f"[ingest] {source.name}: parsed={len(parsed)} created={created}")
        except (urllib.error.URLError, TimeoutError, ET.ParseError) as exc:
            print(f"[ingest] {source.name}: failed={exc}", file=sys.stderr)
    session.commit()
    return total_sources, total_items


def create_posts(
    session,
    limit: int,
    status: str,
    provider: str,
    model: str,
    ollama_url: str,
    dry_run: bool,
) -> int:
    q = (
        select(FeedItem)
        .where(FeedItem.status == "new")
        .order_by(FeedItem.published_at.is_(None), FeedItem.published_at.desc(), FeedItem.id.desc())
        .limit(limit)
    )
    feed_items = session.scalars(q).all()
    created_count = 0

    for item in feed_items:
        story_exists_q = (
            select(GeneratedPost.id)
            .join(PostSource, PostSource.generated_post_id == GeneratedPost.id)
            .join(FeedItem, FeedItem.id == PostSource.feed_item_id)
            .where(FeedItem.source_id == item.source_id)
            .where(FeedItem.original_title == item.original_title)
        )
        if item.published_at is not None:
            story_exists_q = story_exists_q.where(FeedItem.published_at == item.published_at)

        existing_post_id = session.scalar(story_exists_q.limit(1))
        if existing_post_id is not None:
            item.status = "used"
            if not dry_run:
                session.commit()
            else:
                session.rollback()
            print(
                f"[post] skipped source={item.original_url} reason=duplicate-story existing_post_id={existing_post_id}"
            )
            continue

        post_title = ""
        excerpt = ""
        content_html = ""
        used_mode = "fallback"

        if provider == "openai":
            try:
                post_title, excerpt, content_html = _generate_with_openai(item, model=model)
                used_mode = "openai"
            except Exception as exc:  # noqa: BLE001
                print(f"[generate] openai failed for {item.original_url}: {exc}", file=sys.stderr)
        elif provider == "ollama":
            try:
                post_title, excerpt, content_html = _generate_with_ollama(
                    item, model=model, base_url=ollama_url
                )
                used_mode = "ollama"
            except Exception as exc:  # noqa: BLE001
                print(f"[generate] ollama failed for {item.original_url}: {exc}", file=sys.stderr)

        if not content_html:
            post_title, excerpt, content_html = _generate_fallback(item)

        slug = _unique_slug(session, post_title)
        image_urls: list[str] = []
        if provider == "openai":
            try:
                image_urls = _generate_cover_with_openai(post_title, excerpt, content_html, slug)
            except Exception as exc:  # noqa: BLE001
                print(f"[image] openai failed for {item.original_url}: {exc}", file=sys.stderr)
        cover_image_url = image_urls[0] if image_urls else None
        if image_urls:
            content_html = _inject_inline_images(content_html, image_urls)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        post = GeneratedPost(
            slug=slug,
            title=post_title[:255],
            excerpt=excerpt[:500],
            content_html=content_html,
            cover_image_url=cover_image_url,
            status=status,
            published_at=now if status == "published" else None,
        )
        session.add(post)
        session.flush()
        session.add(
            PostSource(
                generated_post_id=post.id,
                feed_item_id=item.id,
                source_name=(item.source.name if item.source else "RSS"),
                source_url=item.original_url,
                attribution_text=f"Generated from RSS ({used_mode})",
            )
        )
        item.status = "used"
        created_count += 1

        print(
            f"[post] created slug={slug} source={item.original_url} mode={used_mode} "
            f"image_count={len(image_urls)} cover={cover_image_url or 'none'}"
        )
        if dry_run:
            _cleanup_generated_images(image_urls)
            session.rollback()
            return created_count
        session.commit()
        if status == "draft":
            try:
                _send_review_email(post)
            except Exception as exc:  # noqa: BLE001
                print(f"[notify] review email failed for post_id={post.id}: {exc}", file=sys.stderr)

    return created_count


def backfill_post_covers(session, limit: int, status: str, dry_run: bool) -> int:
    q = select(GeneratedPost).where(
        or_(GeneratedPost.cover_image_url.is_(None), GeneratedPost.cover_image_url == "")
    )
    if status != "all":
        q = q.where(GeneratedPost.status == status)
    q = q.order_by(GeneratedPost.created_at.desc(), GeneratedPost.id.desc()).limit(limit)
    posts = session.scalars(q).all()
    updated_count = 0

    for post in posts:
        image_urls: list[str] = []
        try:
            image_urls = _generate_cover_with_openai(post.title, post.excerpt or "", post.content_html, post.slug)
        except Exception as exc:  # noqa: BLE001
            print(f"[backfill] image failed for post_id={post.id} slug={post.slug}: {exc}", file=sys.stderr)
            continue

        if not image_urls:
            print(f"[backfill] skipped post_id={post.id} slug={post.slug} reason=no-image")
            continue

        cover_image_url = image_urls[0]
        if dry_run:
            print(
                f"[backfill] would-update post_id={post.id} slug={post.slug} "
                f"image_count={len(image_urls)} cover={cover_image_url}"
            )
            _cleanup_generated_images(image_urls)
            continue

        post.cover_image_url = cover_image_url
        post.content_html = _inject_inline_images(post.content_html, image_urls)
        session.commit()
        updated_count += 1
        print(
            f"[backfill] updated post_id={post.id} slug={post.slug} "
            f"image_count={len(image_urls)} cover={cover_image_url}"
        )

    if dry_run:
        session.rollback()
    return updated_count


def cmd_list_sources() -> int:
    init_db()
    session = SessionLocal()
    try:
        sources = session.scalars(select(FeedSource).order_by(FeedSource.id.asc())).all()
        if not sources:
            print("No feed sources. Add one with `add-source`.")
            return 0
        for s in sources:
            print(f"{s.id}\tactive={s.is_active}\t{s.name}\t{s.rss_url}")
        return 0
    finally:
        session.close()


def cmd_add_source(name: str, rss_url: str, site_url: str | None) -> int:
    init_db()
    session = SessionLocal()
    try:
        existing = session.scalar(select(FeedSource).where(FeedSource.rss_url == rss_url))
        if existing:
            print(f"already exists: id={existing.id} name={existing.name}")
            return 0
        source = FeedSource(name=name.strip()[:120], rss_url=rss_url.strip()[:500], site_url=(site_url or "")[:500])
        session.add(source)
        session.commit()
        print(f"added source id={source.id} name={source.name}")
        return 0
    finally:
        session.close()


def cmd_import_sources(path: str) -> int:
    init_db()
    with open(path, "r", encoding="utf-8") as f:
        payload = json.load(f)
    if not isinstance(payload, list):
        raise ValueError("source file must be a JSON array")

    session = SessionLocal()
    try:
        added = 0
        for row in payload:
            name = str(row.get("name", "")).strip()
            rss_url = str(row.get("rss_url", "")).strip()
            site_url = str(row.get("site_url", "")).strip()
            if not name or not rss_url:
                continue
            existing = session.scalar(select(FeedSource).where(FeedSource.rss_url == rss_url))
            if existing:
                continue
            session.add(FeedSource(name=name[:120], rss_url=rss_url[:500], site_url=site_url[:500], is_active=1))
            added += 1
        session.commit()
        print(f"imported {added} sources")
        return 0
    finally:
        session.close()


def cmd_run(
    limit: int,
    status: str,
    timeout: int,
    provider: str,
    model: str,
    ollama_url: str,
    dry_run: bool,
) -> int:
    init_db()
    session = SessionLocal()
    try:
        source_count, new_items = ingest_sources(session, timeout=timeout)
        created_posts = create_posts(
            session=session,
            limit=limit,
            status=status,
            provider=provider,
            model=model,
            ollama_url=ollama_url,
            dry_run=dry_run,
        )
        print(
            f"[done] sources={source_count} new_items={new_items} created_posts={created_posts} "
            f"status={status} provider={provider} model={model} dry_run={dry_run}"
        )
        return 0
    finally:
        session.close()


def cmd_backfill_covers(limit: int, status: str, dry_run: bool) -> int:
    init_db()
    session = SessionLocal()
    try:
        updated_posts = backfill_post_covers(
            session=session,
            limit=limit,
            status=status,
            dry_run=dry_run,
        )
        print(
            f"[done] backfill_covers updated_posts={updated_posts} "
            f"status={status} dry_run={dry_run}"
        )
        return 0
    finally:
        session.close()


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="AgeCalc RSS -> blog scheduler")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-sources", help="List feed sources")

    p_add = sub.add_parser("add-source", help="Add one RSS source")
    p_add.add_argument("--name", required=True)
    p_add.add_argument("--rss-url", required=True)
    p_add.add_argument("--site-url", default="")

    p_import = sub.add_parser("import-sources", help="Import sources from JSON array")
    p_import.add_argument("--file", required=True)

    p_run = sub.add_parser("run", help="Fetch RSS and create posts")
    p_run.add_argument("--limit", type=int, default=3, help="Max new posts per run")
    p_run.add_argument("--status", choices=["draft", "published"], default="draft")
    p_run.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT)
    p_run.add_argument("--provider", choices=["openai", "ollama", "fallback"], default="openai")
    p_run.add_argument("--model", default=os.getenv("OPENAI_MODEL", DEFAULT_MODEL))
    p_run.add_argument("--ollama-url", default=os.getenv("OLLAMA_URL", DEFAULT_OLLAMA_URL))
    p_run.add_argument("--no-openai", action="store_true", help="Deprecated: same as --provider fallback")
    p_run.add_argument("--dry-run", action="store_true")

    p_backfill = sub.add_parser("backfill-covers", help="Generate missing cover images for existing posts")
    p_backfill.add_argument("--limit", type=int, default=20, help="Max posts to update per run")
    p_backfill.add_argument("--status", choices=["draft", "published", "all"], default="all")
    p_backfill.add_argument("--dry-run", action="store_true")
    return p


def main() -> int:
    args = build_parser().parse_args()
    if args.cmd == "list-sources":
        return cmd_list_sources()
    if args.cmd == "add-source":
        return cmd_add_source(args.name, args.rss_url, args.site_url)
    if args.cmd == "import-sources":
        return cmd_import_sources(args.file)
    if args.cmd == "run":
        provider = "fallback" if args.no_openai else args.provider
        model = args.model
        if provider == "ollama" and model == DEFAULT_MODEL:
            model = os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL)
        return cmd_run(
            limit=max(1, args.limit),
            status=args.status,
            timeout=max(3, args.timeout),
            provider=provider,
            model=model,
            ollama_url=args.ollama_url,
            dry_run=args.dry_run,
        )
    if args.cmd == "backfill-covers":
        return cmd_backfill_covers(
            limit=max(1, args.limit),
            status=args.status,
            dry_run=args.dry_run,
        )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
