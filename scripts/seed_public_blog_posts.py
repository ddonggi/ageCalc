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


SEED_ARTICLE_HTML = {
    "2026-man-age-guide": "".join(
        [
            "<section><h2>만나이는 무엇을 기준으로 계산하나</h2><p>만나이는 출생일이 지났는지 여부를 기준으로 계산합니다.</p></section>",
            "<section><h2>2026년에 결과가 달라지는 핵심은 생일 전후</h2><p>생일 전과 후의 결과 차이를 먼저 확인해야 합니다.</p></section>",
            "<section><h2>이 경우는 바로 단정하면 틀리기 쉽습니다</h2><p>출생연도만 아는 경우와 윤년 출생은 범위 또는 예외로 해석해야 합니다.</p></section>",
        ]
    ),
    "birth-year-age-interpretation": "".join(
        [
            "<section><h2>출생연도만 알면 단일 나이로 단정하지 않습니다</h2><p>생일 전후를 모르면 현재 만나이는 한 살 차이 범위로 봐야 합니다.</p></section>",
            "<section><h2>몇 년생 몇 살 검색은 기준을 다시 확인해야 합니다</h2><p>일상 표현과 공식 기준이 섞여 있으므로 출생년도별 나이표와 만나이 계산기를 함께 보는 것이 안전합니다.</p></section>",
            "<section><h2>정확한 값이 필요하면 생년월일까지 확인합니다</h2><p>프로필이나 공적 서류처럼 정확성이 중요할 때는 생년월일 전체 입력이 필요합니다.</p></section>",
        ]
    ),
    "early-birth-school-grade-guide": "".join(
        [
            "<section><h2>빠른년생은 나이와 학년 기준을 나눠 봅니다</h2><p>공식 나이는 만나이로 확인하고, 학교 문맥은 학년과 입학연도로 따로 해석해야 합니다.</p></section>",
            "<section><h2>학교 경험 때문에 체감 기준이 남아 있을 수 있습니다</h2><p>같은 출생연도라도 학교 배치 기억 때문에 현재 설명 방식이 달라질 수 있습니다.</p></section>",
            "<section><h2>학년 계산기와 입학년도 계산표를 같이 봅니다</h2><p>현재 학년과 입학 시점을 나눠 확인하면 빠른년생 설명이 훨씬 쉬워집니다.</p></section>",
        ]
    ),
    "baby-months-calculation-guide": "".join(
        [
            "<section><h2>아이 개월 수는 월령 기준으로 확인합니다</h2><p>영유아 시기에는 몇 개월 차이도 크기 때문에 월령 표현이 더 실용적입니다.</p></section>",
            "<section><h2>개월 수와 기념일 계산은 같이 봐야 합니다</h2><p>백일, 첫돌, 다음 생일은 기준이 달라 월령 계산과 함께 정리하는 것이 좋습니다.</p></section>",
            "<section><h2>표와 계산기를 함께 보면 이해가 쉽습니다</h2><p>개월수 계산표로 빠르게 보고, 계산기로 현재 월령을 정확히 확인하면 실수가 줄어듭니다.</p></section>",
        ]
    ),
    "parent-child-age-gap-guide": "".join(
        [
            "<section><h2>부모·자녀 나이 차이는 생일 전후까지 함께 봅니다</h2><p>출생연도 차이가 같아도 현재 만나이 차이는 생일 전후에 따라 달라질 수 있습니다.</p></section>",
            "<section><h2>가족 문맥과 일반 비교는 다르게 해석합니다</h2><p>가족 행사나 소개에서는 관계 맥락이 중요해 부모·자녀 계산기가 더 실용적입니다.</p></section>",
            "<section><h2>개별 만나이와 차이를 같이 확인합니다</h2><p>부모·자녀 계산기와 나이 차이 계산기를 함께 보면 설명과 비교가 쉬워집니다.</p></section>",
        ]
    ),
}


def build_seed_post_payload(slug: str) -> dict[str, object]:
    article = structured_blog_article_for_slug(slug)
    if article is None:
        raise KeyError(slug)
    content_html = SEED_ARTICLE_HTML[slug]

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
