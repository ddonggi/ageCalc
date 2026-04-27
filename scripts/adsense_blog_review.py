from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / ".env.rss"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
MIN_BODY_CHARS = 1200
MIN_HEADINGS = 3
SIMILAR_TITLE_THRESHOLD = 0.42

RELATED_KEYWORDS = (
    "AgeCalc",
    "계산기",
    "생활 기준",
    "나이",
    "연령",
    "개월",
    "생년",
    "학년",
    "입학",
    "생일",
    "디데이",
    "D-Day",
    "반려",
    "강아지",
    "고양이",
    "아이",
    "부모",
    "자녀",
)
TITLE_STOPWORDS = {
    "그리고",
    "대한",
    "위한",
    "우리",
    "이야기",
    "의미",
    "활용법",
    "중요성",
    "소개",
    "방법",
    "가이드",
}


@dataclass(frozen=True)
class BlogAuditIssue:
    code: str
    severity: str
    message: str


@dataclass(frozen=True)
class BlogAuditResult:
    post_id: int | None
    slug: str
    title: str
    keep: bool
    issues: tuple[BlogAuditIssue, ...]

    @property
    def issue_codes(self) -> list[str]:
        return [issue.code for issue in self.issues]

    @property
    def critical_issue_codes(self) -> list[str]:
        return [issue.code for issue in self.issues if issue.severity == "critical"]


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


def _strip_tags(content_html: str) -> str:
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", content_html or "", flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _heading_count(content_html: str) -> int:
    return len(re.findall(r"<h[23]\b", content_html or "", flags=re.IGNORECASE))


def _sources(post: object) -> list[object]:
    return list(getattr(post, "sources", None) or [])


def _source_text(sources: Iterable[object]) -> str:
    parts: list[str] = []
    for source in sources:
        parts.append(str(getattr(source, "source_name", "") or ""))
        parts.append(str(getattr(source, "source_url", "") or ""))
        parts.append(str(getattr(source, "attribution_text", "") or ""))
    return " ".join(parts)


def _title_tokens(title: str) -> set[str]:
    tokens: set[str] = set()
    for raw in re.findall(r"[0-9A-Za-z가-힣]+", title.casefold()):
        token = re.sub(r"(으로|에서|에게|까지|부터|으로는|으로도|의|와|과|을|를|은|는|이|가)$", "", raw)
        if len(token) < 2 or token in TITLE_STOPWORDS:
            continue
        tokens.add(token)
    return tokens


def _similar_title_counts(posts: Sequence[object]) -> dict[int | None, int]:
    signatures = [(getattr(post, "id", None), _title_tokens(getattr(post, "title", "") or "")) for post in posts]
    counts: dict[int | None, int] = {post_id: 0 for post_id, _ in signatures}
    for index, (left_id, left_tokens) in enumerate(signatures):
        if not left_tokens:
            continue
        for right_id, right_tokens in signatures[index + 1 :]:
            if not right_tokens:
                continue
            similarity = len(left_tokens & right_tokens) / len(left_tokens | right_tokens)
            if similarity >= SIMILAR_TITLE_THRESHOLD:
                counts[left_id] = counts.get(left_id, 0) + 1
                counts[right_id] = counts.get(right_id, 0) + 1
    return counts


def audit_post(
    post: object,
    *,
    similar_title_count: int = 0,
    min_body_chars: int = MIN_BODY_CHARS,
) -> BlogAuditResult:
    content_html = getattr(post, "content_html", "") or ""
    title = getattr(post, "title", "") or ""
    body_text = _strip_tags(content_html)
    sources = _sources(post)
    source_text = _source_text(sources)
    issues: list[BlogAuditIssue] = []
    risk_score = 0

    def add_issue(code: str, severity: str, message: str, score: int) -> None:
        nonlocal risk_score
        issues.append(BlogAuditIssue(code=code, severity=severity, message=message))
        risk_score += score

    if "Generated from RSS" in source_text or "Generated from RSS" in body_text:
        add_issue("generated_rss_marker", "critical", "내부 RSS 자동 생성 문구가 남아 있습니다.", 5)

    if len(body_text) < min_body_chars:
        add_issue("thin_body", "critical", "본문 길이가 공개 설명 글 기준보다 짧습니다.", 4)

    if _heading_count(content_html) < MIN_HEADINGS:
        add_issue("shallow_structure", "high", "소제목 구조가 부족합니다.", 2)

    if not sources:
        add_issue("missing_sources", "critical", "참고 자료가 없습니다.", 4)

    if "news.google.com/rss/articles" in source_text:
        add_issue("google_news_redirect_source", "medium", "Google News RSS 리디렉션 URL만 출처로 남아 있습니다.", 1)

    if not any(keyword in body_text for keyword in RELATED_KEYWORDS):
        add_issue("weak_agecalc_relevance", "high", "AgeCalc 계산기나 생활 기준과의 연결이 약합니다.", 3)

    if similar_title_count > 0:
        add_issue("similar_title_cluster", "high", "유사한 제목의 공개 글이 가까운 묶음으로 존재합니다.", 2)

    keep = not any(issue.severity == "critical" for issue in issues) and risk_score < 4
    return BlogAuditResult(
        post_id=getattr(post, "id", None),
        slug=getattr(post, "slug", "") or "",
        title=title,
        keep=keep,
        issues=tuple(issues),
    )


def audit_posts(posts: Sequence[object], *, min_body_chars: int = MIN_BODY_CHARS) -> list[BlogAuditResult]:
    similar_counts = _similar_title_counts(posts)
    return [
        audit_post(
            post,
            similar_title_count=similar_counts.get(getattr(post, "id", None), 0),
            min_body_chars=min_body_chars,
        )
        for post in posts
    ]


def _load_published_posts(session, limit: int | None):
    from models.blog_models import GeneratedPost

    query = (
        session.query(GeneratedPost)
        .filter(GeneratedPost.status == "published")
        .order_by(GeneratedPost.published_at.desc(), GeneratedPost.id.desc())
    )
    if limit:
        query = query.limit(limit)
    return query.all()


def _apply_results(session, posts: Sequence[object], results: Sequence[BlogAuditResult]) -> int:
    risky_ids = {result.post_id for result in results if not result.keep and result.post_id is not None}
    if not risky_ids:
        return 0
    changed = 0
    for post in posts:
        if getattr(post, "id", None) in risky_ids:
            post.status = "needs_review"
            changed += 1
    session.commit()
    return changed


def _result_payload(results: Sequence[BlogAuditResult]) -> list[dict[str, object]]:
    return [
        {
            "post_id": result.post_id,
            "slug": result.slug,
            "title": result.title,
            "keep": result.keep,
            "issues": [issue.code for issue in result.issues],
        }
        for result in results
    ]


def _print_text_report(results: Sequence[BlogAuditResult], changed: int, *, applied: bool) -> None:
    risky = [result for result in results if not result.keep]
    print(f"audited={len(results)} risky={len(risky)} applied={'yes' if applied else 'no'} changed={changed}")
    for result in risky[:80]:
        codes = ",".join(result.issue_codes)
        print(f"- id={result.post_id} slug={result.slug} issues={codes} title={result.title}")
    if len(risky) > 80:
        print(f"- omitted={len(risky) - 80}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit published blog posts before AdSense re-review.")
    parser.add_argument("--apply", action="store_true", help="Move risky published posts to needs_review.")
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-body-chars", type=int, default=MIN_BODY_CHARS)
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    _load_env_file(ENV_FILE)
    from db import SessionLocal

    session = SessionLocal()
    try:
        posts = _load_published_posts(session, args.limit)
        results = audit_posts(posts, min_body_chars=args.min_body_chars)
        changed = _apply_results(session, posts, results) if args.apply else 0
        if args.format == "json":
            print(json.dumps({"changed": changed, "results": _result_payload(results)}, ensure_ascii=False, indent=2))
        else:
            _print_text_report(results, changed, applied=args.apply)
    finally:
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
