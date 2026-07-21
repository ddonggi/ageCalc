from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS, structured_blog_article_for_slug
from content.blog.rendering import render_article_content_html
from db import SessionLocal, init_db
from models.blog_models import GeneratedPost
from scripts.adsense_blog_review import audit_post


def seed_sources_for_slug(slug: str) -> list[dict[str, str | None]]:
    article = structured_blog_article_for_slug(slug)
    if article is None:
        raise KeyError(slug)
    return [
        {
            "source_name": str(source["organization"]),
            "source_url": str(source["url"]),
            "attribution_text": f"{source['title']} · 확인일 {source['checked_at']}",
        }
        for source in article["source_urls"]
    ]


def build_seed_post_payload(slug: str) -> dict[str, object]:
    article = structured_blog_article_for_slug(slug)
    if article is None:
        raise KeyError(slug)
    content_html = render_article_content_html(article)

    return {
        "slug": article["slug"],
        "title": article["title"],
        "excerpt": article["hero_summary"],
        "content_html": content_html,
        "cover_image_url": article["thumbnail"],
        "status": "draft",
        "published_at": None,
    }


def upsert_seed_post(slug: str) -> GeneratedPost:
    payload = build_seed_post_payload(slug)
    session = SessionLocal()
    post = session.query(GeneratedPost).filter(GeneratedPost.slug == slug).first()
    if post is None:
        post = GeneratedPost(**payload)
        session.add(post)
    elif post.status == "published" and audit_post(post, require_cover_image=True).keep:
        pass
    else:
        for field, value in payload.items():
            setattr(post, field, value)
    session.commit()
    session.refresh(post)
    session.close()
    return post


def main() -> list[str]:
    init_db()
    seeded_slugs: list[str] = []
    for slug in BLOG_ARTICLE_BLUEPRINTS:
        upsert_seed_post(slug)
        seeded_slugs.append(slug)
        print(f"seeded {slug}")
    return seeded_slugs


if __name__ == "__main__":
    main()
