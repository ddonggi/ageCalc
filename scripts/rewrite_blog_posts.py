#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Callable, Sequence

from sqlalchemy import select


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env.rss"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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
        if key and key not in os.environ:
            os.environ[key] = value.strip().strip('"').strip("'")


_load_env_file(ENV_FILE)

from db import SessionLocal  # noqa: E402
from models.blog_models import GeneratedPost  # noqa: E402
from scripts import rss_blog_scheduler as scheduler  # noqa: E402
from scripts.adsense_blog_review import audit_post  # noqa: E402


Generator = Callable[[str, str], tuple[str, str, str]]
SourceResolver = Callable[[str], str | None]
CoverGenerator = Callable[[str, str, str, str], list[str]]
VALID_REWRITE_STATUSES = ("needs_review", "draft", "published")


@dataclass(frozen=True)
class RewriteOutcome:
    post_id: int | None
    title: str
    changed: bool
    reason: str


def _primary_source_url(post: GeneratedPost) -> str | None:
    for source in post.sources or []:
        if source.source_url:
            return source.source_url
    return None


def build_rewrite_prompt(post: GeneratedPost, source_url: str, feedback: str = "") -> str:
    body_text = scheduler._normalize_space(scheduler._strip_tags(post.content_html))[:6000]
    feedback_instructions = (
        f"""

이전 재작성 결과 검수 실패:
- {feedback}
- 같은 문제가 반복되지 않게 본문을 충분히 확장하고, 응답 직전에 HTML 태그를 제외한 실제 한글 본문 길이가 {scheduler.PROMPT_TARGET_BODY_CHARS:,}자 이상인지 자체 점검한다.
""".rstrip()
        if feedback
        else ""
    )
    return f"""
아래 기존 초안을 참고해 AgeCalc 블로그에 공개할 수 있는 한국어 설명형 글로 다시 작성해.
번역이나 요약이 아니라, 한국 독자가 바로 이해할 수 있는 독립 콘텐츠로 재창작해야 한다.

작성 기준:
- 본문은 {scheduler.TARGET_GENERATED_BODY_RANGE} 분량을 목표로 한다.
- HTML 태그를 제외한 본문 텍스트는 최소 {scheduler.MIN_GENERATED_BODY_CHARS:,}자 이상이어야 한다.
- 생성 단계에서는 한글 기준 {scheduler.PROMPT_TARGET_BODY_CHARS:,}자 이상을 목표로 한다.
- 각 소제목 아래에는 2문단 이상을 두고, 각 문단은 2~4문장으로 충분히 설명한다.
- 최소 5개 이상의 h2/h3 소제목을 사용한다.
- 핵심 요약, 배경과 맥락, 한국 독자가 확인할 점, AgeCalc 활용 포인트, 주의할 점과 한계, 참고 링크를 포함한다.
- content_html에는 관련 있는 AgeCalc 내부 계산기 링크를 1개 이상 포함한다.
- AgeCalc 내부 계산기 링크 후보: /age, /d-day, /baby-months, /parent-child, /school-grade-calculator, /school-entry-year-table, /birth-year-age-table, /age-gap-calculator, /100-day-calculator, /birthday-dday-calculator, /baby-months-table, /pet-age-table, /pet-months-table
- "Generated from RSS", "원문에 따르면", 영어식 직역 문장을 쓰지 않는다.
- 실제 원문 URL은 참고 링크 섹션에 1개 이상 포함한다.
- 과장 광고, 의학적 단정, 투자/정책 단정은 피한다.
- JSON 외 다른 설명을 붙이지 않는다.
{feedback_instructions}

응답 형식(JSON):
{{
  "title": "...",
  "excerpt": "...",
  "content_html": "<h2>...</h2>..."
}}

기존 제목: {post.title}
기존 요약: {post.excerpt or ""}
실제 원문 URL: {source_url}
기존 본문: {body_text}
""".strip()


def _generate_with_openai(prompt: str, model: str) -> tuple[str, str, str]:
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set")

    import urllib.request

    body = {
        "model": model,
        "input": prompt,
        "max_output_tokens": scheduler._env_int(
            "OPENAI_BLOG_MAX_OUTPUT_TOKENS",
            scheduler.DEFAULT_BLOG_MAX_OUTPUT_TOKENS,
        ),
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = json.loads(response.read().decode("utf-8"))

    text = scheduler._extract_output_text(payload)
    if not text:
        raise RuntimeError("OpenAI response was empty")
    return scheduler._parse_generated_json(text)


def _unique_slug_for_post(
    session,
    title: str,
    current_post_id: int | None,
    reserved_slugs: set[str] | None = None,
) -> str:
    reserved_slugs = reserved_slugs or set()
    base = scheduler._slugify(title)[:160] or "blog-post"
    candidate = base
    suffix = 2
    while True:
        query = select(GeneratedPost.id).where(GeneratedPost.slug == candidate)
        if current_post_id is not None:
            query = query.where(GeneratedPost.id != current_post_id)
        if candidate not in reserved_slugs and session.scalar(query) is None:
            return candidate
        candidate = f"{base}-{suffix}"
        suffix += 1


def _validate_rewrite(post: GeneratedPost, source_url: str, title: str, excerpt: str, content_html: str) -> str:
    feed_item = SimpleNamespace(
        original_title=post.title,
        original_url=source_url,
        summary=post.excerpt or "",
        content=scheduler._strip_tags(post.content_html or ""),
    )
    is_valid, reason = scheduler._evaluate_generated_post(feed_item, title, excerpt, content_html)
    if not is_valid:
        return reason

    audit_source = SimpleNamespace(source_name="원문", source_url=source_url, attribution_text=None)
    audit_target = SimpleNamespace(
        id=post.id,
        slug=post.slug,
        title=title,
        content_html=content_html,
        sources=[audit_source],
    )
    audit_result = audit_post(audit_target)
    if not audit_result.keep:
        return "감사 기준 실패: " + ", ".join(audit_result.issue_codes)
    return ""


def _build_rewrite_feedback(reason: str, title: str, excerpt: str, content_html: str) -> str:
    plain_text = scheduler._normalize_space(scheduler._strip_tags(content_html or ""))
    heading_count = content_html.lower().count("<h2") + content_html.lower().count("<h3")
    return (
        f"이전 실패 사유: {reason} "
        f"이전 본문 길이: {len(plain_text):,}자, 소제목 수: {heading_count}개. "
        f"이전 제목: {title or '없음'}. 이전 요약: {excerpt or '없음'}."
    )


def _apply_rewrite(
    session,
    post: GeneratedPost,
    *,
    slug: str,
    title: str,
    excerpt: str,
    content_html: str,
    cover_image_url: str,
    source_url: str,
    publish: bool,
) -> None:
    post.title = title[:255]
    post.slug = slug
    post.excerpt = excerpt[:500]
    post.content_html = content_html
    post.cover_image_url = cover_image_url
    if publish:
        post.status = "published"
        if post.published_at is None:
            post.published_at = datetime.now(timezone.utc).replace(tzinfo=None)
    else:
        post.status = "draft"
        post.published_at = None
    for source in post.sources or []:
        source.source_url = source_url
        source.attribution_text = None


def _apply_failure_review(
    post: GeneratedPost,
    *,
    source_url: str,
    reason: str,
    candidate_title: str = "",
    candidate_excerpt: str = "",
    candidate_content_html: str = "",
) -> None:
    failure_item = SimpleNamespace(
        original_title=post.title,
        original_url=source_url,
        summary=post.excerpt or "",
        content=scheduler._strip_tags(post.content_html or ""),
    )
    title, excerpt, content_html = scheduler._build_needs_review_post(
        failure_item,
        reason,
        candidate_title=candidate_title,
        candidate_excerpt=candidate_excerpt,
        candidate_content_html=candidate_content_html,
    )
    post.title = title[:255]
    post.excerpt = excerpt[:500]
    post.content_html = content_html
    post.status = "needs_review"
    post.published_at = None
    for source in post.sources or []:
        source.source_url = source_url
        source.attribution_text = None


def _load_candidates(
    session,
    *,
    limit: int | None,
    post_id: int | None,
    statuses: Sequence[str],
) -> list[GeneratedPost]:
    query = session.query(GeneratedPost).filter(GeneratedPost.status.in_(tuple(statuses)))
    if post_id is not None:
        query = query.filter(GeneratedPost.id == post_id)
    query = query.order_by(GeneratedPost.created_at.desc(), GeneratedPost.id.desc())
    if limit is not None:
        query = query.limit(limit)
    return query.all()


def rewrite_posts(
    *,
    session,
    limit: int | None,
    post_id: int | None,
    statuses: Sequence[str],
    apply: bool,
    model: str,
    publish_on_pass: bool,
    demote_failed_published: bool,
    attempts: int = 1,
    source_resolver: SourceResolver = scheduler.resolve_source_url,
    generator: Generator = _generate_with_openai,
    cover_generator: CoverGenerator = scheduler._generate_cover_with_openai,
) -> int:
    invalid_statuses = sorted(set(statuses) - set(VALID_REWRITE_STATUSES))
    if invalid_statuses:
        raise ValueError(f"unsupported statuses: {', '.join(invalid_statuses)}")

    attempts = max(1, attempts)
    changed = 0
    reserved_slugs: set[str] = set()
    outcomes: list[RewriteOutcome] = []
    for post in _load_candidates(session, limit=limit, post_id=post_id, statuses=statuses):
        source_url = _primary_source_url(post)
        if not source_url:
            if apply and post.status == "published" and demote_failed_published:
                _apply_failure_review(post, source_url="", reason="missing_source_url")
                changed += 1
                outcomes.append(RewriteOutcome(post.id, post.title, True, "demoted:missing_source_url"))
            else:
                outcomes.append(RewriteOutcome(post.id, post.title, False, "missing_source_url"))
            continue

        resolved_url = source_resolver(source_url)
        if not resolved_url:
            if apply and post.status == "published" and demote_failed_published:
                _apply_failure_review(post, source_url=source_url, reason="unresolved_source_url")
                changed += 1
                outcomes.append(RewriteOutcome(post.id, post.title, True, "demoted:unresolved_source_url"))
            else:
                outcomes.append(RewriteOutcome(post.id, post.title, False, "unresolved_source_url"))
            continue

        feedback = ""
        title = ""
        excerpt = ""
        content_html = ""
        failure_reason = ""
        for _attempt in range(1, attempts + 1):
            prompt = build_rewrite_prompt(post, resolved_url, feedback=feedback)
            try:
                title, excerpt, content_html = generator(prompt, model)
            except Exception as exc:  # noqa: BLE001
                failure_reason = f"generation_failed:{exc}"
                feedback = failure_reason
                continue

            validation_reason = _validate_rewrite(post, resolved_url, title, excerpt, content_html)
            if not validation_reason:
                failure_reason = ""
                break

            failure_reason = validation_reason
            feedback = _build_rewrite_feedback(validation_reason, title, excerpt, content_html)
        else:
            validation_reason = failure_reason

        if failure_reason:
            should_mark_review = post.status != "needs_review" or bool(content_html)
            if apply and should_mark_review and (post.status != "published" or demote_failed_published):
                _apply_failure_review(
                    post,
                    source_url=resolved_url,
                    reason=failure_reason,
                    candidate_title=title,
                    candidate_excerpt=excerpt,
                    candidate_content_html=content_html,
                )
                changed += 1
                outcomes.append(RewriteOutcome(post.id, title or post.title, True, f"needs_review:{failure_reason}"))
            else:
                outcomes.append(RewriteOutcome(post.id, title or post.title, False, failure_reason))
            continue

        slug = _unique_slug_for_post(session, title, post.id, reserved_slugs)
        reserved_slugs.add(slug)
        cover_image_url = post.cover_image_url or ""
        if apply and not cover_image_url:
            try:
                image_urls = cover_generator(title, excerpt, content_html, slug)
            except Exception as exc:  # noqa: BLE001
                outcomes.append(RewriteOutcome(post.id, title, False, f"cover_generation_failed:{exc}"))
                continue
            if not image_urls:
                outcomes.append(RewriteOutcome(post.id, title, False, "cover_generation_failed:no_image"))
                continue
            cover_image_url = image_urls[0]
            content_html = scheduler._inject_inline_images(content_html, image_urls)

        if apply:
            _apply_rewrite(
                session,
                post,
                slug=slug,
                title=title,
                excerpt=excerpt,
                content_html=content_html,
                cover_image_url=cover_image_url,
                source_url=resolved_url,
                publish=publish_on_pass,
            )
        changed += 1
        outcomes.append(RewriteOutcome(post.id, title, True, "published" if publish_on_pass else "rewritten"))

    if apply and changed:
        session.commit()
    elif apply:
        session.rollback()

    for outcome in outcomes:
        status = "changed" if outcome.changed else "skipped"
        print(f"[rewrite] {status} post_id={outcome.post_id} reason={outcome.reason} title={outcome.title}")
    return changed


def rewrite_needs_review_posts(
    *,
    session,
    limit: int,
    post_id: int | None,
    apply: bool,
    model: str,
    source_resolver: SourceResolver = scheduler.resolve_source_url,
    generator: Generator = _generate_with_openai,
    cover_generator: CoverGenerator = scheduler._generate_cover_with_openai,
) -> int:
    return rewrite_posts(
        session=session,
        limit=limit,
        post_id=post_id,
        statuses=("needs_review",),
        apply=apply,
        model=model,
        publish_on_pass=False,
        demote_failed_published=False,
        attempts=1,
        source_resolver=source_resolver,
        generator=generator,
        cover_generator=cover_generator,
    )


def _statuses_from_args(status: str, include_all: bool) -> tuple[str, ...]:
    if include_all or status == "all":
        return VALID_REWRITE_STATUSES
    return (status,)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rewrite blog posts into AdSense-safe Korean articles.")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--post-id", type=int, default=None)
    parser.add_argument("--status", choices=[*VALID_REWRITE_STATUSES, "all"], default="needs_review")
    parser.add_argument("--all", action="store_true", help="Rewrite every matching post instead of applying --limit.")
    parser.add_argument("--attempts", type=int, default=1, help="Generation attempts per post before marking review.")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", scheduler.DEFAULT_MODEL))
    parser.add_argument("--apply", action="store_true", help="Persist rewrite results.")
    parser.add_argument("--dry-run", action="store_true", help="Generate and validate without persisting changes.")
    parser.add_argument("--publish-on-pass", action="store_true", help="Publish posts that pass rewrite validation.")
    parser.add_argument(
        "--demote-failed-published",
        action="store_true",
        help="Move published posts that fail rewrite validation back to needs_review.",
    )
    args = parser.parse_args(argv)

    session = SessionLocal()
    try:
        changed = rewrite_posts(
            session=session,
            limit=None if args.all else args.limit,
            post_id=args.post_id,
            statuses=_statuses_from_args(args.status, args.all),
            apply=bool(args.apply and not args.dry_run),
            model=args.model,
            publish_on_pass=args.publish_on_pass,
            demote_failed_published=args.demote_failed_published,
            attempts=args.attempts,
        )
        print(f"[done] changed={changed} applied={'yes' if args.apply and not args.dry_run else 'no'}")
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
