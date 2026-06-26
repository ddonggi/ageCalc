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
            {"label": "사례 1", "title": "생일 전", "description": "1992년 10월 2일생은 2026년 생일 전까지 이전 만나이를 유지합니다."},
            {"label": "사례 2", "title": "생일 후", "description": "같은 출생일도 2026년 생일이 지나면 만나이가 한 살 올라갑니다."},
            {"label": "사례 3", "title": "출생연도만 아는 경우", "description": "1992년생처럼 생일을 모르면 현재 만나이는 범위로만 해석해야 합니다."},
        ],
        "comparison_rows": [
            {"label": "생년월일을 정확히 아는 경우", "standard": "만나이 계산기", "exception": "생일 전후 차이를 함께 확인"},
            {"label": "출생연도만 아는 경우", "standard": "출생년도별 나이표", "exception": "정확한 단일 만나이로 단정하지 않기"},
            {"label": "연나이와 비교가 필요한 경우", "standard": "만나이·연나이 비교표", "exception": "공적 기준과 생활 표현 구분"},
        ],
        "faq_items": [
            {"question": "2026년에도 공적 기준은 만나이인가요?", "answer": "네. 공적 기준은 원칙적으로 만나이로 확인하는 것이 안전합니다."},
            {"question": "출생연도만 알면 왜 정확한 만나이를 못 정하나요?", "answer": "생일이 지났는지 여부를 모르기 때문에 현재 시점에서 한 살 차이가 날 수 있습니다."},
            {"question": "생일 전에는 왜 한 살을 빼나요?", "answer": "만나이는 출생일이 돌아와야 한 살이 증가하는 방식이기 때문입니다."},
        ],
        "related_tools": [
            {"label": "만나이 계산기", "path": "/age", "summary": "생년월일 기준 현재 만나이 계산"},
            {"label": "만나이·연나이 비교표", "path": "/age-comparison-table", "summary": "나이 체계 차이 비교"},
            {"label": "출생년도별 나이표", "path": "/birth-year-age-table", "summary": "생일을 모를 때 범위 확인"},
            {"label": "계산 기준과 참고 자료", "path": "/references", "summary": "공식 기준과 참고 출처 확인"},
        ],
        "related_articles": [
            {"title": "출생연도만 알 때 나이를 해석하는 방법", "path": "/blog/birth-year-age-interpretation", "summary": "출생연도 기반 해석 순서"},
            {"title": "빠른년생은 지금 어떻게 봐야 하나", "path": "/blog/early-birth-school-grade-guide", "summary": "학년과 나이 기준 구분"},
        ],
    },
    "birth-year-age-interpretation": {
        "slug": "birth-year-age-interpretation",
        "title": "출생연도만 알 때 나이를 해석하는 방법 | 만나이 범위 정리",
        "h1": "출생연도만 알 때 나이를 해석하는 방법",
        "hero_summary": "출생연도만 알 때는 단일 나이보다 만나이 범위와 기준일을 함께 봐야 합니다.",
        "eyebrow": "해설 글",
        "primary_cta": {"label": "출생년도별 나이표 바로가기", "path": "/birth-year-age-table"},
        "secondary_cta": {"label": "만나이 계산기 보기", "path": "/age"},
        "direct_answer_title": "출생연도만 알면 이렇게 해석하는 것이 안전합니다",
        "direct_answer_paragraphs": [
            "출생연도만 알고 생일을 모르면 현재 만나이를 한 값으로 단정하면 안 됩니다.",
            "기준일 현재 생일이 지났는지 여부를 모르기 때문에 보통 한 살 차이 범위로 해석해야 합니다.",
            "정확한 값이 필요하면 생년월일까지 입력하고, 대략적인 비교만 필요하면 출생년도별 나이표를 먼저 보는 순서가 안전합니다.",
        ],
        "audience_items": [
            "몇 년생 몇 살인지 빠르게 확인하려는 사람",
            "생일 정보 없이 나이 범위만 해석해야 하는 사람",
            "연나이 표현과 만나이 표현이 헷갈리는 사람",
        ],
        "example_cards": [
            {"label": "사례 1", "title": "1990년생", "description": "생일 전인지 후인지 모르므로 현재 만나이는 두 값 범위로 봐야 합니다."},
            {"label": "사례 2", "title": "채용·소개 문맥", "description": "프로필용 표현은 연나이처럼 보일 수 있어 공식 기준과 구분해야 합니다."},
            {"label": "사례 3", "title": "가족 비교", "description": "부모·형제와 나이 차이를 볼 때도 생일 미확인 상태면 범위로 비교해야 합니다."},
        ],
        "comparison_rows": [
            {"label": "생일 정보 없음", "standard": "출생년도별 나이표", "exception": "만나이 범위로 해석"},
            {"label": "정확한 공식 나이 필요", "standard": "만나이 계산기", "exception": "생년월일 입력 필수"},
            {"label": "표현 방식 비교", "standard": "만나이·연나이 비교표", "exception": "일상 표현과 공적 기준 구분"},
        ],
        "faq_items": [
            {"question": "출생연도만 알면 왜 한 살 차이가 생기나요?", "answer": "기준일보다 생일이 지났는지 모르면 만나이가 한 살 달라질 수 있기 때문입니다."},
            {"question": "몇 년생 몇 살 검색은 만나이인가요?", "answer": "검색 결과나 일상 표현은 혼재돼 있으므로 공식 판단은 만나이 기준으로 다시 확인해야 합니다."},
            {"question": "가장 빠른 확인 방법은 무엇인가요?", "answer": "출생년도별 나이표로 범위를 보고, 필요하면 만나이 계산기로 정확한 값을 확인하는 순서가 좋습니다."},
        ],
        "related_tools": [
            {"label": "출생년도별 나이표", "path": "/birth-year-age-table", "summary": "출생연도 기반 현재 나이 범위 확인"},
            {"label": "만나이 계산기", "path": "/age", "summary": "생년월일 기준 정확한 만나이 계산"},
            {"label": "만나이·연나이 비교표", "path": "/age-comparison-table", "summary": "표현 방식 차이 비교"},
            {"label": "띠와 출생연도 표", "path": "/birth-year-zodiac-table", "summary": "연도 프로필과 띠 함께 확인"},
        ],
        "related_articles": [
            {"title": "2026년 만나이 계산 기준 총정리", "path": "/blog/2026-man-age-guide", "summary": "공식 기준과 예외 먼저 보기"},
            {"title": "빠른년생은 지금 어떻게 봐야 하나", "path": "/blog/early-birth-school-grade-guide", "summary": "출생연도와 학년 기준이 엇갈릴 때"},
        ],
    },
    "early-birth-school-grade-guide": {
        "slug": "early-birth-school-grade-guide",
        "title": "빠른년생은 지금 어떻게 봐야 하나 | 학년과 나이 기준 정리",
        "h1": "빠른년생은 지금 어떻게 봐야 하나",
        "hero_summary": "빠른년생은 만나이, 학년, 입학연도 기준이 서로 다를 수 있어 문맥별로 나눠 봐야 합니다.",
        "eyebrow": "해설 글",
        "primary_cta": {"label": "학년 계산기 바로가기", "path": "/school-grade-calculator"},
        "secondary_cta": {"label": "입학년도 계산표 보기", "path": "/school-entry-year-table"},
        "direct_answer_title": "빠른년생은 나이와 학년 기준을 분리해서 봐야 합니다",
        "direct_answer_paragraphs": [
            "현재 공식 나이는 만나이 기준으로 확인하고, 학교 문맥은 학년과 입학연도 기준으로 따로 봐야 합니다.",
            "빠른년생은 같은 출생연도라도 학교 배치 경험 때문에 체감 연령과 공식 기준이 다르게 느껴질 수 있습니다.",
            "따라서 학년 계산기와 입학년도 계산표를 함께 보는 것이 가장 정확합니다.",
        ],
        "audience_items": [
            "빠른년생 기준을 다시 확인하려는 사람",
            "학년과 나이 표현이 엇갈려 헷갈리는 사람",
            "자녀 입학·학교 문맥에서 설명이 필요한 보호자",
        ],
        "example_cards": [
            {"label": "사례 1", "title": "공식 문서", "description": "나이는 만나이로 판단하고 학교 경험과 분리해서 설명해야 합니다."},
            {"label": "사례 2", "title": "학년 비교", "description": "같은 출생연도라도 학년 배치 기억 때문에 체감 기준이 달라질 수 있습니다."},
            {"label": "사례 3", "title": "자녀 설명", "description": "입학연도와 출생연도를 함께 보면 가장 쉽게 설명할 수 있습니다."},
        ],
        "comparison_rows": [
            {"label": "공식 나이 확인", "standard": "만나이 계산기", "exception": "학교 경험과 구분"},
            {"label": "현재 학교 학년 확인", "standard": "학년 계산기", "exception": "출생연도 기준으로 보기"},
            {"label": "입학 시점 확인", "standard": "입학년도 계산표", "exception": "학년도 기준으로 해석"},
        ],
        "faq_items": [
            {"question": "빠른년생도 지금은 만나이로만 보나요?", "answer": "공식 나이 판단은 만나이로 보는 것이 기본입니다."},
            {"question": "왜 학년 얘기가 함께 나오나요?", "answer": "빠른년생 이슈는 학교 배치 경험과 연결돼 체감 기준이 남아 있기 때문입니다."},
            {"question": "가장 헷갈리지 않는 확인 방법은 무엇인가요?", "answer": "나이는 만나이 계산기, 학교 문맥은 학년 계산기와 입학년도 계산표로 나눠 확인하면 됩니다."},
        ],
        "related_tools": [
            {"label": "학년 계산기", "path": "/school-grade-calculator", "summary": "출생연도 기준 현재 학년 확인"},
            {"label": "입학년도 계산표", "path": "/school-entry-year-table", "summary": "초중고 입학 시점 확인"},
            {"label": "학년별 출생연도 표", "path": "/grade-birth-year-table", "summary": "학년과 출생연도 대응 보기"},
            {"label": "만나이 계산기", "path": "/age", "summary": "공식 나이 따로 확인"},
        ],
        "related_articles": [
            {"title": "출생연도만 알 때 나이를 해석하는 방법", "path": "/blog/birth-year-age-interpretation", "summary": "연도만 있을 때 범위 해석"},
            {"title": "2026년 만나이 계산 기준 총정리", "path": "/blog/2026-man-age-guide", "summary": "공식 기준 자체 먼저 보기"},
        ],
    },
    "baby-months-calculation-guide": {
        "slug": "baby-months-calculation-guide",
        "title": "아이 개월수 계산은 어떻게 보나 | 월령 해석 기준 정리",
        "h1": "아이 개월수 계산은 어떻게 보나",
        "hero_summary": "아이 월령은 생후 개월 수를 기준으로 확인하고, 기념일과 발달 설명은 월령 기준으로 함께 보는 것이 좋습니다.",
        "eyebrow": "해설 글",
        "primary_cta": {"label": "아이 개월 수 계산기 바로가기", "path": "/baby-months"},
        "secondary_cta": {"label": "개월수 계산표 보기", "path": "/baby-months-table"},
        "direct_answer_title": "아이 개월 수는 월령 기준으로 이렇게 확인합니다",
        "direct_answer_paragraphs": [
            "아이 개월 수는 출생일로부터 현재까지 지난 개월 수를 기준으로 계산합니다.",
            "생후 12개월처럼 표현할 때는 단순 나이보다 월령이 더 중요한 경우가 많습니다.",
            "계산기에서 정확한 월령을 확인한 뒤, 표나 기념일 계산기로 다음 시점을 함께 보면 이해가 쉽습니다.",
        ],
        "audience_items": [
            "아이 월령을 정확히 확인하려는 보호자",
            "예방접종·발달 설명을 월령 기준으로 보고 싶은 사람",
            "100일·첫돌 같은 기념 시점을 함께 정리하려는 사람",
        ],
        "example_cards": [
            {"label": "사례 1", "title": "생후 11개월", "description": "연나이로는 0세지만 월령 기준 설명이 더 실용적인 시기입니다."},
            {"label": "사례 2", "title": "첫돌 전후", "description": "12개월과 돌 기준을 함께 보면 행사와 설명을 정리하기 쉽습니다."},
            {"label": "사례 3", "title": "백일 확인", "description": "개월 수 계산과 백일 계산은 기준일이 달라 함께 확인하는 것이 좋습니다."},
        ],
        "comparison_rows": [
            {"label": "정확한 월령 계산", "standard": "아이 개월 수 계산기", "exception": "출생일 기준으로 계산"},
            {"label": "월령 범위 빠른 확인", "standard": "개월수 계산표", "exception": "대략적인 대응 보기"},
            {"label": "기념일 시점 확인", "standard": "100일 계산기", "exception": "행사 날짜와 구분"},
        ],
        "faq_items": [
            {"question": "아이 개월 수는 왜 만나이보다 더 자주 쓰이나요?", "answer": "영유아 시기에는 몇 개월 차이도 크기 때문에 월령 기준 설명이 더 실용적입니다."},
            {"question": "12개월이면 1살과 같은 뜻인가요?", "answer": "비슷하게 쓰이지만 기념일이나 발달 설명에서는 월령 표현이 더 구체적입니다."},
            {"question": "어떤 도구를 같이 보면 좋나요?", "answer": "개월수 계산표와 100일 계산기를 함께 보면 기념 시점 정리에 도움이 됩니다."},
        ],
        "related_tools": [
            {"label": "아이 개월 수 계산기", "path": "/baby-months", "summary": "출생일 기준 현재 월령 계산"},
            {"label": "개월수 계산표", "path": "/baby-months-table", "summary": "월령별 빠른 대응 보기"},
            {"label": "100일 계산기", "path": "/100-day-calculator", "summary": "백일 시점 확인"},
            {"label": "생일 D-day 계산기", "path": "/birthday-dday-calculator", "summary": "다음 생일과 돌 시점 확인"},
        ],
        "related_articles": [
            {"title": "부모·자녀 나이 차이를 해석하는 방법", "path": "/blog/parent-child-age-gap-guide", "summary": "가족 맥락에서 함께 보기"},
            {"title": "2026년 만나이 계산 기준 총정리", "path": "/blog/2026-man-age-guide", "summary": "공식 나이 기준 자체 확인"},
        ],
    },
    "parent-child-age-gap-guide": {
        "slug": "parent-child-age-gap-guide",
        "title": "부모·자녀 나이 차이를 해석하는 방법 | 가족 나이 관계 정리",
        "h1": "부모·자녀 나이 차이를 해석하는 방법",
        "hero_summary": "부모와 자녀의 나이 차이는 출생연도 차이만 보지 말고 만나이와 생일 전후를 함께 봐야 정확합니다.",
        "eyebrow": "해설 글",
        "primary_cta": {"label": "부모·자녀 나이 계산기 바로가기", "path": "/parent-child"},
        "secondary_cta": {"label": "나이 차이 계산기 보기", "path": "/age-gap-calculator"},
        "direct_answer_title": "부모·자녀 나이 관계는 이렇게 해석하면 됩니다",
        "direct_answer_paragraphs": [
            "부모와 자녀의 나이 차이는 출생연도 차이만으로는 충분하지 않고, 생일 전후에 따라 만나이 차이가 달라질 수 있습니다.",
            "가족 소개나 행사 준비처럼 실제 생활에서 쓰려면 현재 만나이와 연도 차이를 함께 보는 것이 안전합니다.",
            "부모·자녀 나이 계산기와 일반 나이 차이 계산기를 같이 보면 해석이 훨씬 쉬워집니다.",
        ],
        "audience_items": [
            "부모와 자녀의 현재 나이 차이를 정확히 확인하려는 사람",
            "가족 행사나 소개 문구를 정리하려는 사람",
            "출생연도 차이와 실제 만나이 차이가 다른 이유를 알고 싶은 사람",
        ],
        "example_cards": [
            {"label": "사례 1", "title": "생일 전후 차이", "description": "같은 연도 차이라도 생일이 지나지 않았으면 현재 만나이 차이는 다르게 보일 수 있습니다."},
            {"label": "사례 2", "title": "행사 문구", "description": "환갑·입학처럼 가족 일정에서는 현재 나이와 연도 차이를 함께 확인하는 것이 좋습니다."},
            {"label": "사례 3", "title": "형제 비교와 혼동", "description": "일반 나이 차이 계산과 부모·자녀 관계 계산은 쓰는 문맥이 다릅니다."},
        ],
        "comparison_rows": [
            {"label": "가족 관계 중심 확인", "standard": "부모·자녀 나이 계산기", "exception": "현재 만나이와 연도 차이 함께 보기"},
            {"label": "두 사람 일반 비교", "standard": "나이 차이 계산기", "exception": "관계 맥락 없이 비교"},
            {"label": "출생연도만 아는 경우", "standard": "출생년도별 나이표", "exception": "현재 차이는 범위로 해석"},
        ],
        "faq_items": [
            {"question": "부모·자녀 나이 차이는 출생연도 차이와 항상 같나요?", "answer": "연도 차이는 같아도 현재 만나이 차이는 생일 전후에 따라 달라질 수 있습니다."},
            {"question": "가장 정확한 확인 방법은 무엇인가요?", "answer": "부모와 자녀의 생년월일을 모두 넣어 현재 만나이와 차이를 함께 보는 것입니다."},
            {"question": "일반 나이 차이 계산기와 무엇이 다른가요?", "answer": "부모·자녀 계산기는 가족 문맥에서 해석하기 쉬운 정보를 같이 보여주는 데 의미가 있습니다."},
        ],
        "related_tools": [
            {"label": "부모·자녀 나이 계산기", "path": "/parent-child", "summary": "가족 관계 기준 현재 나이 계산"},
            {"label": "나이 차이 계산기", "path": "/age-gap-calculator", "summary": "두 출생연도 차이 비교"},
            {"label": "만나이 계산기", "path": "/age", "summary": "개별 현재 나이 확인"},
            {"label": "출생년도별 나이표", "path": "/birth-year-age-table", "summary": "생일 없이 범위 확인"},
        ],
        "related_articles": [
            {"title": "아이 개월수 계산은 어떻게 보나", "path": "/blog/baby-months-calculation-guide", "summary": "육아 시기 월령 해석"},
            {"title": "출생연도만 알 때 나이를 해석하는 방법", "path": "/blog/birth-year-age-interpretation", "summary": "가족 비교 전 연도 해석"},
        ],
    },
}


def structured_blog_article_for_slug(slug: str) -> dict[str, object] | None:
    blueprint = BLOG_ARTICLE_BLUEPRINTS.get(slug)
    if blueprint is None:
        return None
    return deepcopy(blueprint)
