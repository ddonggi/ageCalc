from __future__ import annotations

from copy import deepcopy


BLOG_ARTICLE_BLUEPRINTS = {
    "2026-man-age-guide": {
        "slug": "2026-man-age-guide",
        "title": "2026년 만나이 계산 기준 총정리 | 생일 전후·예외까지 정리",
        "h1": "2026년 만나이 계산 기준 총정리",
        "hero_summary": "2026년 기준 만나이 계산법과 생일 전후 예외를 한 번에 정리합니다.",
        "eyebrow": "해설 글",
        "primary_cta": {"label": "만나이 계산기 바로가기", "path": "/age"},
        "secondary_cta": {"label": "나이 비교표 보기", "path": "/age-comparison-table"},
        "direct_answer_title": "2026년 만나이 계산은 이렇게 보면 됩니다",
        "direct_answer_paragraphs": [
            "2026년 현재 만나이는 기준일 현재 생일이 지났는지에 따라 계산합니다.",
            "기본 공식은 기준연도에서 출생연도를 뺀 뒤, 아직 생일 전이면 한 살을 빼는 방식입니다.",
            "출생연도만 알면 정확한 단일 나이가 아니라 만나이 범위로 해석해야 하는 경우가 많습니다.",
            "정확한 값은 만나이 계산기에서, 다른 나이 체계 비교는 비교표에서 함께 확인하는 것이 가장 안전합니다.",
        ],
        "audience_items": [
            "공식 기준으로 현재 만나이를 확인하려는 사람",
            "출생연도만 알고 나이를 해석해야 하는 사람",
            "만나이와 연나이 차이를 한 번에 정리하려는 사람",
        ],
        "example_cards": [
            {
                "label": "사례 1",
                "title": "생일 전",
                "description": "1992년 10월 2일생은 2026년 생일 전까지 이전 만나이를 유지합니다.",
            },
            {
                "label": "사례 2",
                "title": "생일 후",
                "description": "같은 출생일도 2026년 생일이 지나면 만나이가 한 살 올라갑니다.",
            },
            {
                "label": "사례 3",
                "title": "출생연도만 아는 경우",
                "description": "1992년생처럼 생일을 모르면 현재 만나이는 범위로만 해석해야 합니다.",
            },
        ],
        "comparison_rows": [
            {
                "label": "생년월일을 정확히 아는 경우",
                "standard": "만나이 계산기",
                "exception": "생일 전후 차이를 함께 확인",
            },
            {
                "label": "출생연도만 아는 경우",
                "standard": "출생년도별 나이표",
                "exception": "정확한 단일 만나이로 단정하지 않기",
            },
            {
                "label": "연나이와 비교가 필요한 경우",
                "standard": "만나이·연나이 비교표",
                "exception": "공적 기준과 생활 표현 구분",
            },
        ],
        "faq_items": [
            {
                "question": "2026년에도 공적 기준은 만나이인가요?",
                "answer": "네. 공적 기준은 원칙적으로 만나이로 확인하는 것이 안전합니다.",
            },
            {
                "question": "출생연도만 알면 왜 정확한 만나이를 못 정하나요?",
                "answer": "생일이 지났는지 여부를 모르기 때문에 현재 시점에서 한 살 차이가 날 수 있습니다.",
            },
            {
                "question": "생일 전에는 왜 한 살을 빼나요?",
                "answer": "만나이는 출생일이 돌아와야 한 살이 증가하는 방식이기 때문입니다.",
            },
        ],
        "related_tools": [
            {"label": "만나이 계산기", "path": "/age", "summary": "생년월일 기준 현재 만나이 계산"},
            {"label": "만나이·연나이 비교표", "path": "/age-comparison-table", "summary": "나이 체계 차이 비교"},
            {"label": "출생년도별 나이표", "path": "/birth-year-age-table", "summary": "생일을 모를 때 범위 확인"},
            {"label": "계산 기준과 참고 자료", "path": "/references", "summary": "공식 기준과 참고 출처 확인"},
        ],
        "related_articles": [
            {
                "title": "출생연도만 알 때 나이를 해석하는 방법",
                "path": "/blog/birth-year-age-interpretation",
                "summary": "출생연도 기반 해석 순서",
            },
            {
                "title": "빠른년생은 지금 어떻게 봐야 하나",
                "path": "/blog/early-birth-school-grade-guide",
                "summary": "학년과 나이 기준 구분",
            },
        ],
    }
}


def structured_blog_article_for_slug(slug: str) -> dict[str, object] | None:
    blueprint = BLOG_ARTICLE_BLUEPRINTS.get(slug)
    if blueprint is None:
        return None
    return deepcopy(blueprint)
