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
from types import SimpleNamespace
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
DEFAULT_BLOG_MAX_OUTPUT_TOKENS = 5000
IMAGE_OUTPUT_DIR = PROJECT_ROOT / "static" / "generated" / "blog-covers"
PROMPTS_DIR = PROJECT_ROOT / "prompts"
TARGET_GENERATED_BODY_RANGE = "1,800~2,400자"
MIN_GENERATED_BODY_CHARS = 1600
MIN_GENERATED_HEADINGS = 5
AGECALC_INTERNAL_LINKS = (
    "/age",
    "/d-day",
    "/baby-months",
    "/parent-child",
    "/school-grade-calculator",
    "/school-entry-year-table",
    "/birth-year-age-table",
    "/age-gap-calculator",
    "/100-day-calculator",
    "/birthday-dday-calculator",
    "/baby-months-table",
    "/pet-age-table",
    "/pet-months-table",
)
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


def _is_google_news_redirect_url(url: str) -> bool:
    parsed = urllib.parse.urlparse(url or "")
    return parsed.netloc == "news.google.com" and "/rss/articles/" in parsed.path


def _google_news_article_id(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url or "")
    if parsed.netloc != "news.google.com":
        return None
    parts = [part for part in parsed.path.split("/") if part]
    for marker in ("articles", "read"):
        if marker in parts:
            index = parts.index(marker)
            if index + 1 < len(parts):
                return urllib.parse.unquote(parts[index + 1])
    return None


def _decode_google_news_batchexecute_response(text: str) -> str | None:
    try:
        payload_text = (text or "").split("\n\n", 1)[1]
        rows = json.loads(payload_text)
        for row in rows:
            if (
                isinstance(row, list)
                and len(row) >= 3
                and row[0] == "wrb.fr"
                and row[1] == "Fbv4je"
                and row[2]
            ):
                decoded_payload = json.loads(row[2])
                if (
                    isinstance(decoded_payload, list)
                    and len(decoded_payload) >= 2
                    and decoded_payload[0] == "garturlres"
                ):
                    return decoded_payload[1]
    except (IndexError, TypeError, json.JSONDecodeError):
        pass

    patterns = (
        r'\[\\"garturlres\\",\\"(?P<url>https?://.*?)(?<!\\)\\"',
        r'\["garturlres","(?P<url>https?://.*?)(?<!\\)"',
    )
    for pattern in patterns:
        match = re.search(pattern, text or "")
        if not match:
            continue
        encoded_url = match.group("url").replace("\\/", "/")
        try:
            return json.loads(f'"{encoded_url}"')
        except json.JSONDecodeError:
            return encoded_url.replace('\\"', '"')
    return None


def _google_news_decoding_params(article_id: str, timeout: int = DEFAULT_TIMEOUT) -> tuple[str, str] | None:
    for path in ("articles", "rss/articles"):
        request = urllib.request.Request(
            f"https://news.google.com/{path}/{article_id}",
            headers={"User-Agent": "Mozilla/5.0 AgeCalcBot/1.0 (+https://agecalc.cloud/about)"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                text = response.read().decode("utf-8", "replace")
        except (urllib.error.URLError, TimeoutError, ValueError):
            continue

        signature_match = re.search(r'data-n-a-sg="([^"]+)"', text)
        timestamp_match = re.search(r'data-n-a-ts="([^"]+)"', text)
        if signature_match and timestamp_match:
            return signature_match.group(1), timestamp_match.group(1)
    return None


def _resolve_google_news_batchexecute(url: str, timeout: int = DEFAULT_TIMEOUT) -> str | None:
    article_id = _google_news_article_id(url)
    if not article_id:
        return None
    params = _google_news_decoding_params(article_id, timeout=timeout)
    if not params:
        return None
    signature, timestamp = params

    inner_payload = (
        '["garturlreq",'
        '[["X","X",["X","X"],null,null,1,1,"US:en",null,1,null,null,null,null,null,0,1],'
        '"X","X",1,[1,1,1],1,1,null,0,0,null,0],'
        f'"{article_id}",{timestamp},"{signature}"]'
    )
    request_payload = [[
            [
                "Fbv4je",
                inner_payload,
            ]
    ]]
    body = urllib.parse.urlencode(
        {"f.req": json.dumps(request_payload, separators=(",", ":"), ensure_ascii=False)}
    ).encode("utf-8")
    request = urllib.request.Request(
        "https://news.google.com/_/DotsSplashUi/data/batchexecute?rpcids=Fbv4je",
        data=body,
        method="POST",
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=utf-8",
            "Referer": "https://news.google.com/",
            "User-Agent": "Mozilla/5.0 AgeCalcBot/1.0 (+https://agecalc.cloud/about)",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            text = response.read().decode("utf-8", "replace")
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None

    decoded_url = _decode_google_news_batchexecute_response(text)
    if decoded_url and not _is_google_news_redirect_url(decoded_url):
        return decoded_url
    return None


def _is_agecalc_internal_link(href: str) -> bool:
    parsed = urllib.parse.urlparse(href or "")
    if parsed.netloc and parsed.netloc not in {"agecalc.cloud", "www.agecalc.cloud"}:
        return False
    return parsed.path in AGECALC_INTERNAL_LINKS


def _has_agecalc_internal_link(content_html: str) -> bool:
    hrefs = re.findall(r"""href=["']([^"']+)["']""", content_html or "", flags=re.IGNORECASE)
    return any(_is_agecalc_internal_link(href) for href in hrefs)


def resolve_source_url(url: str, timeout: int = DEFAULT_TIMEOUT) -> str | None:
    if not url:
        return None
    if not _is_google_news_redirect_url(url):
        return url

    decoded_url = _resolve_google_news_batchexecute(url, timeout=timeout)
    if decoded_url:
        return decoded_url

    request = urllib.request.Request(
        url,
        headers={"User-Agent": "AgeCalcBot/1.0 (+https://agecalc.cloud/about)"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            final_url = response.geturl()
    except (urllib.error.URLError, TimeoutError, ValueError):
        return None

    if final_url and not _is_google_news_redirect_url(final_url):
        return final_url
    return None


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


def _contains_korean(text: str) -> int:
    return len(re.findall(r"[가-힣]", text or ""))


def _contains_latin(text: str) -> int:
    return len(re.findall(r"[A-Za-z]", text or ""))


def _detect_source_language(feed_item: FeedItem) -> str:
    sample = " ".join(
        part for part in [feed_item.original_title, feed_item.summary or "", feed_item.content or ""] if part
    )
    korean_count = _contains_korean(sample)
    latin_count = _contains_latin(sample)
    if korean_count >= latin_count and korean_count >= 20:
        return "ko"
    if latin_count >= 20 and korean_count < 10:
        return "en"
    return "mixed"


def _build_generation_prompt(feed_item: FeedItem) -> str:
    source_language = _detect_source_language(feed_item)
    language_instructions = (
        """
- 원문이 한국어인 경우에도 단순 요약이나 문장 치환으로 끝내지 말고, 한국어 독자를 위한 설명형 블로그 글로 재구성한다.
- AgeCalc 독자가 이 주제를 왜 읽어야 하는지와, 계산기/생활 기준과 어떻게 연결되는지 1개 이상 설명한다.
""".strip()
        if source_language != "en"
        else """
- 영어 원문을 한국어 독자를 위한 설명형 블로그 글로 재창작한다.
- 영어 제목을 직역하지 말고, 원문 문장 순서를 그대로 따라 쓰지 말고, 맥락을 이해한 뒤 자연스러운 한국어 기사형 해설로 다시 쓴다.
- 고유명사, 기관명, 날짜, 수치 정보는 유지하되 번역체 문장을 피한다.
- 한국 독자에게 왜 중요한지, AgeCalc 계산기나 생활 기준과 어떤 식으로 연결해 읽을 수 있는지 반드시 설명한다.
""".strip()
    )
    return f"""
아래 원문 정보를 참고해서 한국어 독자를 위한 설명형 블로그 글을 작성해.
당신의 목표는 원문을 번역하거나 요약하는 것이 아니라, 독립적인 한국어 설명 콘텐츠로 재창작하는 것이다.
조건:
- 한국어 독자를 위한 설명형 블로그 글이어야 한다.
- 제목 1개는 원문 제목을 번역하지 말고 새로 작성한다.
- 본문은 {TARGET_GENERATED_BODY_RANGE} 분량을 목표로 작성한다.
- HTML 태그를 제외한 본문 텍스트만 최소 1,600자 이상이어야 한다.
- 각 소제목 아래에는 2문단 이상을 두고, 각 문단은 2~4문장으로 충분히 설명한다.
- 서론 1문단, 본문 최소 5개 소제목, 결론 1문단
- 본문에 다음 내용을 반드시 포함한다:
  1. 사건/연구/정책의 핵심 요약
  2. 배경 설명 또는 맥락
  3. 한국 독자에게 중요한 이유
  4. AgeCalc 계산기 또는 생활 기준과 연결되는 활용 포인트
  5. 해석 시 주의점 또는 한계
- content_html 안에는 관련 있는 AgeCalc 내부 계산기 링크를 1개 이상 포함한다.
- 사용할 수 있는 내부 링크: /age, /d-day, /baby-months, /parent-child, /school-grade-calculator, /school-entry-year-table, /birth-year-age-table, /age-gap-calculator, /100-day-calculator, /birthday-dday-calculator, /baby-months-table, /pet-age-table, /pet-months-table
- 사실 왜곡 금지, 출처 링크를 '참고 링크' 섹션에 1개 이상 포함
- 과장 광고 문구 금지
- 영어 원문이더라도 최종 결과는 자연스러운 한국어여야 한다.
- "요약하면", "원문에 따르면" 같은 뉴스 브리핑체를 반복하지 않는다.
- '계산기 활용 포인트' 또는 '생활 기준에서 볼 점' 같은 실용 섹션을 포함한다.
- 본문은 최소 5개 이상의 소제목 구조를 가져야 한다.
- JSON 외 다른 설명을 붙이지 않는다.
{language_instructions}
- 응답 형식(JSON):
  {{
    "title": "...",
    "excerpt": "...",
    "content_html": "<h2>...</h2>...",
    "editor_note": "편집 메모 한 줄"
  }}

원문 제목: {feed_item.original_title}
원문 언어 추정: {source_language}
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


def _evaluate_generated_post(
    feed_item: FeedItem,
    title: str,
    excerpt: str,
    content_html: str,
) -> tuple[bool, str]:
    plain_text = _normalize_space(_strip_tags(content_html))
    heading_count = len(re.findall(r"<h[23]\b", content_html, flags=re.IGNORECASE))
    source_language = _detect_source_language(feed_item)
    normalized_source_title = _normalize_space(feed_item.original_title).casefold()
    normalized_generated_title = _normalize_space(title).casefold()

    if "Generated from RSS" in content_html or "Generated from RSS" in plain_text:
        return False, "내부 RSS 자동 생성 표식이 남아 있어 공개할 수 없습니다."

    if _is_google_news_redirect_url(feed_item.original_url):
        return False, "Google News RSS 리디렉션이 아닌 실제 원문 URL이 필요합니다."

    if len(plain_text) < MIN_GENERATED_BODY_CHARS:
        return False, "재창작 본문 길이가 짧아 설명형 콘텐츠 기준에 미달합니다."

    if heading_count < MIN_GENERATED_HEADINGS:
        return False, "재창작 구조가 부족합니다."

    if "참고 링크" not in content_html:
        return False, "출처 섹션이 없어 재창작 검토 기준을 충족하지 못했습니다."

    if not _has_agecalc_internal_link(content_html):
        return False, "AgeCalc 내부 계산기 링크가 없어 승인용 블로그 기준에 미달합니다."

    if not any(keyword in plain_text for keyword in ("AgeCalc", "계산기", "생활 기준", "활용 포인트")):
        return False, "서비스 또는 계산기와 연결되는 활용 설명이 없습니다."

    if source_language == "en":
        if _contains_korean(plain_text) < 120:
            return False, "영어 원문을 한국어 설명형 글로 충분히 재창작하지 못했습니다."
        if (
            normalized_source_title == normalized_generated_title
            or normalized_source_title in normalized_generated_title
            or normalized_generated_title in normalized_source_title
        ):
            return False, "원문 제목과 지나치게 유사해 재창작 기준에 미달합니다."

    if excerpt and _normalize_space(excerpt).casefold() == normalized_source_title:
        return False, "발췌문이 원문 제목 수준에 머물러 재창작 기준에 미달합니다."

    return True, ""


def _build_needs_review_post(feed_item: FeedItem, reason: str) -> tuple[str, str, str]:
    safe_title = html.escape(_normalize_space(feed_item.original_title)[:200] or "원문 검토 필요")
    safe_url = html.escape(feed_item.original_url)
    safe_reason = html.escape(reason)
    title = f"[검토 필요] {feed_item.original_title[:160]}".strip()
    excerpt = "자동 초안 생성 품질 검토가 필요해 공개 가능한 설명형 글로 전환되지 않았습니다."
    content_html = (
        "<h2>자동 초안 생성 품질 검토 필요</h2>"
        f"<p>{safe_reason}</p>"
        "<h3>원문 정보</h3>"
        f"<p><strong>원문 제목</strong>: {safe_title}</p>"
        f'<p><a href="{safe_url}" rel="noopener noreferrer nofollow" target="_blank">원문 확인하기</a></p>'
        "<h3>다음 작업</h3>"
        "<p>한국어 독자를 위한 설명형 구조, 계산기 활용 포인트, 주의사항을 보강한 뒤 다시 검토하세요.</p>"
    )
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
        "max_output_tokens": _env_int("OPENAI_BLOG_MAX_OUTPUT_TOKENS", DEFAULT_BLOG_MAX_OUTPUT_TOKENS),
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
        used_mode = "needs-review"
        failure_reason = ""
        post_status = status
        effective_source_url = item.original_url
        generation_item = item

        if _is_google_news_redirect_url(item.original_url):
            resolved_source_url = resolve_source_url(item.original_url)
            if not resolved_source_url:
                failure_reason = "Google News RSS 리디렉션 URL을 실제 원문 URL로 해석하지 못했습니다."
            else:
                effective_source_url = resolved_source_url
                generation_item = SimpleNamespace(
                    original_title=item.original_title,
                    original_url=resolved_source_url,
                    summary=item.summary,
                    content=item.content,
                )

        if not failure_reason and provider == "openai":
            try:
                post_title, excerpt, content_html = _generate_with_openai(generation_item, model=model)
                used_mode = "openai"
            except Exception as exc:  # noqa: BLE001
                print(f"[generate] openai failed for {item.original_url}: {exc}", file=sys.stderr)
                failure_reason = f"자동 생성 실패: {exc}"
        elif not failure_reason and provider == "ollama":
            try:
                post_title, excerpt, content_html = _generate_with_ollama(
                    generation_item, model=model, base_url=ollama_url
                )
                used_mode = "ollama"
            except Exception as exc:  # noqa: BLE001
                print(f"[generate] ollama failed for {item.original_url}: {exc}", file=sys.stderr)
                failure_reason = f"자동 생성 실패: {exc}"

        if not content_html:
            post_title, excerpt, content_html = _build_needs_review_post(
                item,
                failure_reason or "자동 생성 결과가 비어 있어 편집 검토가 필요합니다.",
            )
            post_status = "needs_review"

        if post_status == status:
            is_valid, validation_reason = _evaluate_generated_post(generation_item, post_title, excerpt, content_html)
            if not is_valid:
                post_title, excerpt, content_html = _build_needs_review_post(item, validation_reason)
                post_status = "needs_review"
                used_mode = f"{used_mode}-quality-review"

        slug = _unique_slug(session, post_title)
        image_urls: list[str] = []
        if provider == "openai" and post_status == status:
            try:
                image_urls = _generate_cover_with_openai(post_title, excerpt, content_html, slug)
            except Exception as exc:  # noqa: BLE001
                print(f"[image] openai failed for {item.original_url}: {exc}", file=sys.stderr)
        cover_image_url = image_urls[0] if image_urls else None
        if image_urls and post_status == status:
            content_html = _inject_inline_images(content_html, image_urls)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        post = GeneratedPost(
            slug=slug,
            title=post_title[:255],
            excerpt=excerpt[:500],
            content_html=content_html,
            cover_image_url=cover_image_url,
            status=post_status,
            published_at=now if post_status == "published" else None,
        )
        session.add(post)
        session.flush()
        session.add(
            PostSource(
                generated_post_id=post.id,
                feed_item_id=item.id,
                source_name=(item.source.name if item.source else "RSS"),
                source_url=effective_source_url,
                attribution_text=None,
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
        if post.status == "draft":
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
