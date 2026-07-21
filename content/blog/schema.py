from __future__ import annotations

import re
from datetime import date
from typing import Mapping
from urllib.parse import urlparse


SITE_ORIGIN = "https://agecalc.cloud"

BLOG_CATEGORIES = {
    "age": "만나이·나이 제도",
    "birth-year": "출생연도",
    "education-family": "학교·육아",
    "policy-benefits": "연금·복지·법적 기준",
    "health": "건강검진",
    "pets": "반려동물",
}

OFFICIAL_SOURCE_HOSTS = {
    "www.aaha.org",
    "www.bokjiro.go.kr",
    "www.gov.kr",
    "www.law.go.kr",
    "www.moe.go.kr",
    "www.nhis.or.kr",
    "www.nps.or.kr",
}

REQUIRED_ARTICLE_FIELDS = (
    "title",
    "slug",
    "summary",
    "h1",
    "hero_summary",
    "category",
    "tags",
    "author",
    "review_owner",
    "reviewed_at",
    "effective_date",
    "expires_at",
    "source_urls",
    "thumbnail",
    "thumbnail_alt",
    "meta_title",
    "meta_description",
    "canonical_url",
    "related_calculators",
    "related_articles",
    "faq",
    "schema_type",
    "is_curated",
    "is_indexable",
    "direct_answer_paragraphs",
    "example_cards",
    "comparison_rows",
    "faq_items",
    "related_tools",
)


class ContentContractError(ValueError):
    """Raised when structured editorial content cannot be published safely."""


def merge_article_registries(
    *registries: Mapping[str, Mapping[str, object]],
) -> dict[str, dict[str, object]]:
    merged: dict[str, dict[str, object]] = {}
    for registry in registries:
        collisions = set(merged).intersection(registry)
        if collisions:
            duplicate = sorted(collisions)[0]
            raise ContentContractError(f"duplicate article slug across content modules: {duplicate}")
        merged.update({slug: dict(article) for slug, article in registry.items()})
    return merged


def article_metadata(
    *,
    slug: str,
    category: str,
    tags: tuple[str, ...],
    reviewed_at: str,
    effective_date: str,
    expires_at: str,
    sources: list[dict[str, str]],
    meta_title: str,
    meta_description: str,
    thumbnail_alt: str,
    author: str = "AgeCalc 편집팀",
    review_owner: str = "AgeCalc 편집책임자",
    is_indexable: bool = True,
) -> dict[str, object]:
    return {
        "category": category,
        "category_label": BLOG_CATEGORIES[category],
        "tags": list(tags),
        "author": author,
        "review_owner": review_owner,
        "reviewed_at": reviewed_at,
        "effective_date": effective_date,
        "expires_at": expires_at,
        "source_urls": sources,
        "thumbnail": f"/static/images/blog/{slug}.jpg",
        "thumbnail_alt": thumbnail_alt,
        "meta_title": meta_title,
        "meta_description": meta_description,
        "canonical_url": f"{SITE_ORIGIN}/blog/{slug}",
        "schema_type": "BlogPosting",
        "is_curated": True,
        "is_indexable": is_indexable,
    }


def complete_article(article: dict[str, object], metadata: dict[str, object]) -> dict[str, object]:
    result = {**article, **metadata}
    result["summary"] = result["hero_summary"]
    result["related_calculators"] = result["related_tools"]
    result["faq"] = result["faq_items"]
    return result


def build_article(
    *,
    slug: str,
    title: str,
    h1: str,
    summary: str,
    category: str,
    tags: tuple[str, ...],
    primary_cta: dict[str, str],
    secondary_cta: dict[str, str],
    direct_answer_title: str,
    direct_answer_paragraphs: list[str],
    audience_items: list[str],
    example_cards: list[dict[str, str]],
    comparison_rows: list[dict[str, str]],
    content_sections: list[dict[str, object]],
    faq_items: list[dict[str, str]],
    related_tools: list[dict[str, str]],
    related_articles: list[dict[str, str]],
    reviewed_at: str,
    effective_date: str,
    expires_at: str,
    sources: list[dict[str, str]],
    meta_title: str,
    meta_description: str,
    thumbnail_alt: str,
    disclaimer: str = "",
) -> dict[str, object]:
    article = {
        "slug": slug,
        "title": title,
        "h1": h1,
        "hero_summary": summary,
        "eyebrow": "검수된 해설",
        "primary_cta": primary_cta,
        "secondary_cta": secondary_cta,
        "direct_answer_title": direct_answer_title,
        "direct_answer_paragraphs": direct_answer_paragraphs,
        "audience_items": audience_items,
        "example_cards": example_cards,
        "comparison_rows": comparison_rows,
        "content_sections": content_sections,
        "faq_items": faq_items,
        "related_tools": related_tools,
        "related_articles": related_articles,
        "disclaimer": disclaimer,
    }
    metadata = article_metadata(
        slug=slug,
        category=category,
        tags=tags,
        reviewed_at=reviewed_at,
        effective_date=effective_date,
        expires_at=expires_at,
        sources=sources,
        meta_title=meta_title,
        meta_description=meta_description,
        thumbnail_alt=thumbnail_alt,
    )
    return complete_article(article, metadata)


def _parse_date(value: object, *, slug: str, field: str) -> date:
    try:
        return date.fromisoformat(str(value))
    except ValueError as exc:
        raise ContentContractError(f"{slug}: {field} must be an ISO date") from exc


def validate_article_registry(
    articles: Mapping[str, Mapping[str, object]],
    *,
    today: date | None = None,
) -> None:
    today = today or date.today()
    registered_slugs = {str(article.get("slug", "")) for article in articles.values()}
    from content.page_registry import PUBLIC_PAGE_REGISTRY

    known_internal_paths = {str(page["path"]) for page in PUBLIC_PAGE_REGISTRY}

    for registry_key, article in articles.items():
        slug = str(article.get("slug", ""))
        if registry_key != slug:
            raise ContentContractError(f"{registry_key}: registry key must match unique article slug {slug!r}")
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
            raise ContentContractError(f"{slug}: slug must use lowercase ASCII words and hyphens")

        for field in REQUIRED_ARTICLE_FIELDS:
            if field not in article or article[field] in (None, "", [], ()):
                raise ContentContractError(f"{slug}: missing required field {field}")

        category = str(article["category"])
        if category not in BLOG_CATEGORIES:
            raise ContentContractError(f"{slug}: unknown category {category}")

        reviewed_at = _parse_date(article["reviewed_at"], slug=slug, field="reviewed_at")
        effective_date = _parse_date(article["effective_date"], slug=slug, field="effective_date")
        expires_at = _parse_date(article["expires_at"], slug=slug, field="expires_at")
        if expires_at <= effective_date:
            raise ContentContractError(f"{slug}: expires_at must be later than effective_date")
        if reviewed_at > today:
            raise ContentContractError(f"{slug}: reviewed_at cannot be in the future")

        if article["canonical_url"] != f"{SITE_ORIGIN}/blog/{slug}":
            raise ContentContractError(f"{slug}: canonical_url must match the public article URL")
        if not str(article["thumbnail"]).startswith("/static/"):
            raise ContentContractError(f"{slug}: thumbnail must be a local static asset")
        if article["schema_type"] not in {"Article", "BlogPosting"}:
            raise ContentContractError(f"{slug}: unsupported schema_type")
        for field in ("is_curated", "is_indexable"):
            if type(article[field]) is not bool:
                raise ContentContractError(f"{slug}: {field} must be a boolean")
        for field in ("tags", "source_urls", "related_tools", "related_articles", "faq_items"):
            if not isinstance(article[field], (list, tuple)):
                raise ContentContractError(f"{slug}: {field} must be a list")

        for source in article["source_urls"]:
            if not isinstance(source, Mapping):
                raise ContentContractError(f"{slug}: each source must be a named mapping")
            for field in ("organization", "title", "url", "checked_at"):
                if not str(source.get(field, "")).strip():
                    raise ContentContractError(f"{slug}: source missing {field}")
            parsed = urlparse(str(source["url"]))
            if parsed.scheme != "https" or not parsed.netloc:
                raise ContentContractError(f"{slug}: source URL must use HTTPS")
            if parsed.hostname not in OFFICIAL_SOURCE_HOSTS:
                raise ContentContractError(f"{slug}: source host is not an approved official institution")
            _parse_date(source["checked_at"], slug=slug, field="source.checked_at")

        for field in ("primary_cta", "secondary_cta"):
            path = str(article[field].get("path", "")) if isinstance(article[field], Mapping) else ""
            if path not in known_internal_paths:
                raise ContentContractError(f"{slug}: unknown internal path {path!r} in {field}")

        for item in article["related_tools"]:
            path = str(item.get("path", "")) if isinstance(item, Mapping) else ""
            if path not in known_internal_paths:
                raise ContentContractError(f"{slug}: unknown internal path {path!r} in related_tools")

        for item in article["related_articles"]:
            path = str(item.get("path", "")) if isinstance(item, Mapping) else ""
            related_slug = path.removeprefix("/blog/") if path.startswith("/blog/") else ""
            if not related_slug or related_slug not in registered_slugs:
                raise ContentContractError(f"{slug}: related article path is not registered: {path!r}")
