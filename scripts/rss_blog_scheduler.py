#!/usr/bin/env python3
import argparse
import hashlib
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from sqlalchemy import select

from db import SessionLocal, init_db
from models.blog_models import FeedItem, FeedSource, GeneratedPost, PostSource


DEFAULT_TIMEOUT = 15
DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_OLLAMA_MODEL = "mistral:latest"
DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


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
    req = urllib.request.Request(
        url,
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
    created = 0
    for item in parsed_items:
        url = (item.get("url") or "").strip()
        title = _normalize_space(item.get("title") or "")
        if not url or not title:
            continue
        existing = session.scalar(select(FeedItem).where(FeedItem.original_url == url))
        if existing:
            continue
        session.add(
            FeedItem(
                source_id=source.id,
                original_title=title[:255],
                original_url=url[:500],
                published_at=item.get("published_at"),
                summary=(item.get("summary") or "")[:100000],
                content=(item.get("content") or "")[:200000],
                content_hash=_content_hash(item),
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
        .order_by(FeedItem.published_at.desc().nullslast(), FeedItem.id.desc())
        .limit(limit)
    )
    feed_items = session.scalars(q).all()
    created_count = 0

    for item in feed_items:
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
        now = datetime.utcnow()
        post = GeneratedPost(
            slug=slug,
            title=post_title[:255],
            excerpt=excerpt[:500],
            content_html=content_html,
            cover_image_url=None,
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

        print(f"[post] created slug={slug} source={item.original_url} mode={used_mode}")
        if dry_run:
            session.rollback()
            return created_count
        session.commit()

    return created_count


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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
