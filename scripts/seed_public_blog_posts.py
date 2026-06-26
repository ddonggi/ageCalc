from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from content.blog_articles import BLOG_ARTICLE_BLUEPRINTS, structured_blog_article_for_slug
from db import SessionLocal, init_db
from models.blog_models import GeneratedPost


def build_seed_post_payload(slug: str) -> dict[str, object]:
    article = structured_blog_article_for_slug(slug)
    if article is None:
        raise KeyError(slug)

    content_html = "".join(
        [
            "<section>",
            "<h2>만나이는 무엇을 기준으로 계산하나</h2>",
            "<p>만나이는 출생일이 지났는지 여부를 기준으로 계산합니다.</p>",
            "</section>",
            "<section>",
            "<h2>2026년에 결과가 달라지는 핵심은 생일 전후</h2>",
            "<p>생일 전과 후의 결과 차이를 먼저 확인해야 합니다.</p>",
            "</section>",
            "<section>",
            "<h2>이 경우는 바로 단정하면 틀리기 쉽습니다</h2>",
            "<p>출생연도만 아는 경우와 윤년 출생은 범위 또는 예외로 해석해야 합니다.</p>",
            "</section>",
        ]
    )

    return {
        "slug": article["slug"],
        "title": article["title"],
        "excerpt": article["hero_summary"],
        "content_html": content_html,
        "cover_image_url": None,
        "status": "published",
        "published_at": datetime.now(timezone.utc).replace(tzinfo=None),
    }


def upsert_seed_post(slug: str) -> GeneratedPost:
    payload = build_seed_post_payload(slug)
    session = SessionLocal()
    post = session.query(GeneratedPost).filter(GeneratedPost.slug == slug).first()
    if post is None:
        post = GeneratedPost(**payload)
        session.add(post)
    else:
        for field, value in payload.items():
            if field == "published_at" and post.published_at is not None:
                continue
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
