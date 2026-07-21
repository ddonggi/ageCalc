#!/usr/bin/env python3
"""Audit indexable AgeCalc pages for structural and editorial quality signals."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from html import unescape
from html.parser import HTMLParser
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

MIN_BODY_TEXT_LENGTH = 1000
THIN_CONTENT_EXEMPT_PATHS = frozenset({"/about", "/contact", "/privacy", "/terms"})


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.ignored_depth = 0
        self.inside_body = False

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag == "body":
            self.inside_body = True
        if tag in {"script", "style", "noscript", "header", "footer", "nav", "aside"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "header", "footer", "nav", "aside"} and self.ignored_depth:
            self.ignored_depth -= 1
        if tag == "body":
            self.inside_body = False

    def handle_data(self, data: str) -> None:
        if self.inside_body and not self.ignored_depth:
            normalized = re.sub(r"\s+", " ", data).strip()
            if normalized:
                self.parts.append(normalized)


@dataclass
class QualityIssue:
    code: str
    severity: str
    message: str


@dataclass
class PageQualityResult:
    path: str
    hub: str = ""
    title: str = ""
    description: str = ""
    h1: str = ""
    body_text: str = ""
    sentences: tuple[str, ...] = ()
    issues: list[QualityIssue] = field(default_factory=list)

    @property
    def errors(self) -> list[QualityIssue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[QualityIssue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    @property
    def passed(self) -> bool:
        return not self.errors

    def add(self, code: str, severity: str, message: str) -> None:
        self.issues.append(QualityIssue(code, severity, message))


@dataclass
class ContentQualityReport:
    results: list[PageQualityResult] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return all(result.passed for result in self.results)

    @property
    def error_count(self) -> int:
        return sum(len(result.errors) for result in self.results)

    @property
    def warning_count(self) -> int:
        return sum(len(result.warnings) for result in self.results)

    def add(self, result: PageQualityResult) -> None:
        self.results.append(result)

    def detect_duplicates(self) -> None:
        for attribute, code, label in (
            ("title", "duplicate_title_warning", "title"),
            ("description", "duplicate_description_warning", "description"),
            ("h1", "duplicate_h1_warning", "H1"),
        ):
            groups: dict[str, list[PageQualityResult]] = defaultdict(list)
            for result in self.results:
                value = getattr(result, attribute).strip().casefold()
                if value:
                    groups[value].append(result)
            for duplicates in groups.values():
                if len(duplicates) < 2:
                    continue
                paths = ", ".join(result.path for result in duplicates)
                for result in duplicates:
                    result.add(code, "warning", f"동일한 {label}이 여러 페이지에 있습니다: {paths}")

        sentence_groups: dict[str, list[PageQualityResult]] = defaultdict(list)
        for result in self.results:
            for sentence in set(result.sentences):
                sentence_groups[sentence.casefold()].append(result)
        for sentence, duplicates in sentence_groups.items():
            if len(duplicates) < 2:
                continue
            paths = ", ".join(result.path for result in duplicates)
            for result in duplicates:
                result.add(
                    "repeated_sentence_warning",
                    "warning",
                    f"본문 문장이 반복됩니다: {paths} / {sentence[:80]}",
                )


def _first_match(pattern: str, html: str) -> str:
    match = re.search(pattern, html, re.I | re.S)
    if not match:
        return ""
    return re.sub(r"<[^>]+>", " ", unescape(match.group(1))).strip()


def _visible_text(html: str) -> str:
    parser = _TextExtractor()
    parser.feed(html)
    return re.sub(r"\s+", " ", " ".join(parser.parts)).strip()


def _sentences(text: str) -> tuple[str, ...]:
    candidates = re.split(r"(?<=[.!?다요])\s+", text)
    return tuple(
        sentence.strip()
        for sentence in candidates
        if len(sentence.strip()) >= 35
    )


def audit_html(
    path: str,
    html: str,
    *,
    ymyl: bool,
    hub: str = "",
) -> PageQualityResult:
    title = _first_match(r"<title[^>]*>(.*?)</title>", html)
    description = _first_match(
        r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](.*?)["\']',
        html,
    )
    h1 = _first_match(r"<h1[^>]*>(.*?)</h1>", html)
    body_text = _visible_text(html)
    result = PageQualityResult(
        path=path,
        hub=hub,
        title=title,
        description=description,
        h1=h1,
        body_text=body_text,
        sentences=_sentences(body_text),
    )

    required_checks = (
        ("title_missing", title, "title이 없습니다."),
        ("description_missing", description, "meta description이 없습니다."),
        ("h1_missing", h1, "H1이 없습니다."),
        (
            "canonical_missing",
            re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\'][^"\']+', html, re.I),
            "canonical 링크가 없습니다.",
        ),
        (
            "direct_answer_missing",
            re.search(r'class=["\'][^"\']*\bdirect-answer\b', html, re.I),
            "검색 질문에 바로 답하는 직접 답변 블록이 없습니다.",
        ),
        (
            "editorial_meta_missing",
            'class="editorial-meta"' in html,
            "작성·검수 메타데이터가 없습니다.",
        ),
        (
            "related_paths_missing",
            'class="related-paths"' in html,
            "문맥형 관련 링크가 없습니다.",
        ),
    )
    for code, condition, message in required_checks:
        if not condition:
            result.add(code, "error", message)

    if len(re.findall(r"<h2\b", html, re.I)) < 3:
        result.add("insufficient_h2", "error", "독립적인 H2 섹션이 3개 미만입니다.")

    is_public_blog_article = (
        path.startswith("/blog/")
        and not path.startswith("/blog/category/")
        and not path.startswith("/blog/drafts")
        and not path.startswith("/blog/review")
    )
    if is_public_blog_article and not re.search(
        r'["\']@type["\']\s*:\s*["\'](?:BlogPosting|Article)["\']',
        html,
        re.I,
    ):
        result.add("article_schema_missing", "error", "공개 블로그 글에 Article 구조화 데이터가 없습니다.")

    if ymyl:
        if 'data-official-source="true"' not in html:
            result.add("official_source_missing", "error", "공식 출처가 없습니다.")
        if 'class="editorial-disclaimer"' not in html:
            result.add("ymyl_disclaimer_missing", "error", "YMYL 면책문구가 없습니다.")

    if path not in THIN_CONTENT_EXEMPT_PATHS and len(body_text) < MIN_BODY_TEXT_LENGTH:
        result.add(
            "thin_content_warning",
            "warning",
            f"보이는 본문이 {len(body_text)}자로 1,000자 미만입니다.",
        )

    return result


def _auditable_pages(*, paths: tuple[str, ...], hub: str | None):
    from app import ADSENSE_REVIEW_MODE
    from content.page_registry import PUBLIC_PAGE_REGISTRY

    selected_paths = set(paths)
    return tuple(
        page
        for page in PUBLIC_PAGE_REGISTRY
        if page["indexable"]
        and page["endpoint"] != "blog_list"
        and (not ADSENSE_REVIEW_MODE or not str(page["key"]).startswith("hub:"))
        and (not selected_paths or page["path"] in selected_paths)
        and (hub is None or page["hub"] == hub)
    )


def audit_local_pages(
    *,
    paths: tuple[str, ...] = (),
    hub: str | None = None,
) -> ContentQualityReport:
    from app import (
        ADSENSE_REVIEW_MODE,
        BLOG_ARTICLE_BLUEPRINTS,
        BLOG_CATEGORIES,
        BLOG_CATEGORY_INDEX_MIN_POSTS,
        BLOG_PUBLIC_INDEXING_ENABLED,
        SessionLocal,
        _is_blog_public_indexable,
        _published_eligible_blog_posts,
        app,
    )
    from content.editorial_metadata import OFFICIAL_SOURCE_REQUIRED_KEYS

    report = ContentQualityReport()
    client = app.test_client()
    for page in _auditable_pages(paths=paths, hub=hub):
        path = str(page["path"])
        response = client.get(path)
        if response.status_code != 200:
            result = PageQualityResult(path=path, hub=str(page["hub"]))
            result.add("page_not_200", "error", f"응답 코드가 {response.status_code}입니다.")
        else:
            result = audit_html(
                path,
                response.get_data(as_text=True),
                ymyl=str(page["key"]) in OFFICIAL_SOURCE_REQUIRED_KEYS,
                hub=str(page["hub"]),
            )
        report.add(result)

    selected_paths = set(paths)
    audit_public_blogs = (
        not ADSENSE_REVIEW_MODE
        and BLOG_PUBLIC_INDEXING_ENABLED
        and (hub is None or hub == "blog")
    )
    if audit_public_blogs:
        db_session = SessionLocal()
        try:
            blog_posts = _published_eligible_blog_posts(db_session)
        finally:
            db_session.close()
        if _is_blog_public_indexable(len(blog_posts)):
            for post in blog_posts:
                path = f"/blog/{post.slug}"
                if selected_paths and path not in selected_paths:
                    continue
                response = client.get(path)
                if response.status_code != 200:
                    result = PageQualityResult(path=path, hub="blog")
                    result.add("page_not_200", "error", f"응답 코드가 {response.status_code}입니다.")
                else:
                    category = str(BLOG_ARTICLE_BLUEPRINTS[post.slug]["category"])
                    result = audit_html(
                        path,
                        response.get_data(as_text=True),
                        ymyl=category in {"policy-benefits", "health"},
                        hub="blog",
                    )
                report.add(result)
            category_counts: dict[str, int] = defaultdict(int)
            for post in blog_posts:
                category_counts[str(BLOG_ARTICLE_BLUEPRINTS[post.slug]["category"])] += 1
            for category_slug in BLOG_CATEGORIES:
                if category_counts[category_slug] < BLOG_CATEGORY_INDEX_MIN_POSTS:
                    continue
                path = f"/blog/category/{category_slug}"
                if selected_paths and path not in selected_paths:
                    continue
                response = client.get(path)
                if response.status_code != 200:
                    result = PageQualityResult(path=path, hub="blog")
                    result.add("page_not_200", "error", f"응답 코드가 {response.status_code}입니다.")
                else:
                    result = audit_html(
                        path,
                        response.get_data(as_text=True),
                        ymyl=False,
                        hub="blog",
                    )
                report.add(result)
    report.detect_duplicates()
    return report


def format_text(report: ContentQualityReport) -> str:
    status = "PASS" if report.ok else "FAIL"
    lines = [
        (
            f"[content-quality] {status} checked_pages={len(report.results)} "
            f"errors={report.error_count} warnings={report.warning_count}"
        )
    ]
    for result in report.results:
        page_status = "PASS" if result.passed else "FAIL"
        lines.append(
            f"- {page_status} {result.path} errors={len(result.errors)} warnings={len(result.warnings)}"
        )
        for issue in result.issues:
            lines.append(f"  - {issue.severity}:{issue.code} - {issue.message}")
    return "\n".join(lines)


def format_json(report: ContentQualityReport) -> str:
    payload = {
        "ok": report.ok,
        "checked_pages": len(report.results),
        "errors": report.error_count,
        "warnings": report.warning_count,
        "results": [
            {
                "path": result.path,
                "hub": result.hub,
                "passed": result.passed,
                "issues": [asdict(issue) for issue in result.issues],
            }
            for result in report.results
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit indexable AgeCalc content quality.")
    parser.add_argument("--format", choices=("text", "json"), default="text")
    parser.add_argument("--paths", nargs="*", default=())
    parser.add_argument("--hub")
    args = parser.parse_args(argv)

    report = audit_local_pages(paths=tuple(args.paths), hub=args.hub)
    print(format_json(report) if args.format == "json" else format_text(report))
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
