from __future__ import annotations

from content.official_sources import SOURCE_CHECKED_AT, sources_for_hub


EDITORIAL_AUTHOR = "AgeCalc 편집팀"
EDITORIAL_REVIEWER = "AgeCalc 편집팀"
DEFAULT_MODIFIED_AT = "2026-06-22"
CORE_AGE_CONTENT_REVIEWED_AT = "2026-06-22"
INFORMATIONAL_DISCLAIMER = (
    "이 페이지의 계산과 설명은 일반 정보이며, 관계 기관의 공식 판단이나 진단을 대신하지 않습니다. "
    "개별 상황은 관계 기관 또는 전문가에게 확인하세요."
)

NAVER_RELATED_SEARCH_TERMS_CHECKED_AT = "2026-08-12"
NAVER_RELATED_SEARCH_TERMS = (
    {"rank": 1, "term": "26학번 년생", "clicks": 243, "impressions": 1443, "ctr": 16.8, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "naturalize"},
    {"rank": 2, "term": "학년 계산기", "clicks": 137, "impressions": 266, "ctr": 51.5, "page_key": "school_grade_calculator", "slot": "primary", "copy_mode": "exact"},
    {"rank": 3, "term": "22학번 나이", "clicks": 130, "impressions": 725, "ctr": 17.9, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 4, "term": "26학번", "clicks": 115, "impressions": 714, "ctr": 16.1, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 5, "term": "아이 개월수 계산기", "clicks": 110, "impressions": 2161, "ctr": 5.1, "page_key": "baby_months", "slot": "primary", "copy_mode": "exact"},
    {"rank": 6, "term": "26학번 나이", "clicks": 104, "impressions": 461, "ctr": 22.6, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 7, "term": "20학번 나이", "clicks": 100, "impressions": 560, "ctr": 17.9, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 8, "term": "20살 몇년생", "clicks": 89, "impressions": 5770, "ctr": 1.5, "page_key": "birth_year_age_table", "slot": "faq", "copy_mode": "naturalize"},
    {"rank": 9, "term": "만나이 폐지", "clicks": 89, "impressions": 1577, "ctr": 5.6, "page_key": "korean_age_guide", "slot": "section", "copy_mode": "naturalize"},
    {"rank": 10, "term": "연도별 띠", "clicks": 89, "impressions": 1043, "ctr": 8.5, "page_key": "birth_year_zodiac_table", "slot": "primary", "copy_mode": "exact"},
    {"rank": 11, "term": "18학번 나이", "clicks": 88, "impressions": 565, "ctr": 15.6, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 12, "term": "중1 몇년생", "clicks": 87, "impressions": 300, "ctr": 29.0, "page_key": "grade_birth_year_table", "slot": "faq", "copy_mode": "naturalize"},
    {"rank": 13, "term": "나이차이 계산", "clicks": 84, "impressions": 273, "ctr": 30.8, "page_key": "age_gap_calculator", "slot": "section", "copy_mode": "naturalize"},
    {"rank": 14, "term": "입학년도 계산", "clicks": 75, "impressions": 641, "ctr": 11.7, "page_key": "school_entry_year_table", "slot": "primary", "copy_mode": "exact"},
    {"rank": 15, "term": "19학번 나이", "clicks": 71, "impressions": 531, "ctr": 13.4, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 16, "term": "고1 몇년생", "clicks": 69, "impressions": 360, "ctr": 19.2, "page_key": "grade_birth_year_table", "slot": "faq", "copy_mode": "naturalize"},
    {"rank": 17, "term": "나이차이 계산기", "clicks": 59, "impressions": 222, "ctr": 26.6, "page_key": "age_gap_calculator", "slot": "primary", "copy_mode": "naturalize"},
    {"rank": 18, "term": "2026년 20살 몇년생", "clicks": 57, "impressions": 1475, "ctr": 3.9, "page_key": "birth_year_age_table", "slot": "faq", "copy_mode": "naturalize"},
    {"rank": 19, "term": "09학번 몇살", "clicks": 51, "impressions": 396, "ctr": 12.9, "page_key": "college_entry_year_calculator", "slot": "faq", "copy_mode": "naturalize"},
    {"rank": 20, "term": "연나이 계산기", "clicks": 46, "impressions": 3919, "ctr": 1.2, "page_key": "annual_age_calculator", "slot": "primary", "copy_mode": "exact"},
    {"rank": 21, "term": "26학번 몇년생", "clicks": 46, "impressions": 129, "ctr": 35.7, "page_key": "college_entry_year_calculator", "slot": "faq", "copy_mode": "naturalize"},
    {"rank": 22, "term": "나이차이계산", "clicks": 45, "impressions": 169, "ctr": 26.6, "page_key": "age_gap_calculator", "slot": "section", "copy_mode": "naturalize"},
    {"rank": 23, "term": "고3 몇년생", "clicks": 43, "impressions": 218, "ctr": 19.7, "page_key": "grade_birth_year_table", "slot": "faq", "copy_mode": "naturalize"},
    {"rank": 24, "term": "학번 계산기", "clicks": 43, "impressions": 85, "ctr": 50.6, "page_key": "college_entry_year_calculator", "slot": "primary", "copy_mode": "exact"},
    {"rank": 25, "term": "23학번 년생", "clicks": 39, "impressions": 222, "ctr": 17.6, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "naturalize"},
    {"rank": 26, "term": "27학번", "clicks": 39, "impressions": 212, "ctr": 18.4, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 27, "term": "21학번 년생", "clicks": 37, "impressions": 234, "ctr": 15.8, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "naturalize"},
    {"rank": 28, "term": "23학번 나이", "clicks": 37, "impressions": 182, "ctr": 20.3, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 29, "term": "21학번 나이", "clicks": 36, "impressions": 201, "ctr": 17.9, "page_key": "college_entry_year_calculator", "slot": "section", "copy_mode": "exact"},
    {"rank": 30, "term": "만13세 몇학년", "clicks": 32, "impressions": 1487, "ctr": 2.2, "page_key": "school_grade_calculator", "slot": "faq", "copy_mode": "naturalize"},
)


def _build_related_search_term_slots() -> dict[str, dict[str, tuple[str, ...]]]:
    page_keys = (
        "age",
        "birth_year_age_table",
        "annual_age_calculator",
        "school_grade_calculator",
        "school_entry_year_table",
        "grade_age_table",
        "grade_birth_year_table",
        "hundred_day_calculator",
        "college_entry_year_calculator",
        "baby_months",
        "korean_age_guide",
        "birth_year_zodiac_table",
        "age_gap_calculator",
    )
    slots: dict[str, dict[str, list[str]]] = {
        key: {"primary": [], "section": [], "faq": []}
        for key in page_keys
    }
    for assignment in NAVER_RELATED_SEARCH_TERMS:
        slots[str(assignment["page_key"])][str(assignment["slot"])].append(
            str(assignment["term"])
        )
    return {
        page_key: {
            slot_name: tuple(terms)
            for slot_name, terms in page_slots.items()
        }
        for page_key, page_slots in slots.items()
    }


RELATED_SEARCH_TERM_SLOTS = _build_related_search_term_slots()

OFFICIAL_SOURCE_REQUIRED_KEYS = frozenset(
    {
        "age",
        "references",
        "school_grade_calculator",
        "school_entry_year_table",
        "grade_age_table",
        "pet_age_table",
        "korean_age_guide",
        "pet_months_table",
        "grade_birth_year_table",
        "faq",
        "dog",
        "cat",
        "baby_months",
        "baby_months_table",
        "guide:age-calculation-2026",
        "guide:reference-date-age-guide",
        "guide:lunar-birthday-age-guide",
        "guide:korean-age-vs-annual-age",
        "guide:sixtieth-seventieth-eightieth-age-guide",
        "guide:school-entry-year-guide",
        "guide:elementary-school-entry-target-2026",
        "guide:school-grade-birth-year-guide",
        "guide:early-birth-school-grade-guide",
        "guide:baby-months-calculation-guide",
        "guide:dog-age-human-age-guide",
        "guide:cat-age-human-age-guide",
        "guide:pet-age-table-guide",
    }
)


def editorial_metadata_for(page: dict[str, object] | None) -> dict[str, object] | None:
    if not page:
        return None

    official_source_required = str(page["key"]) in OFFICIAL_SOURCE_REQUIRED_KEYS
    source_hub = str(page["hub"])
    if page["key"] in {"references", "faq"}:
        source_hub = "age"
    elif page["key"] == "guide:baby-months-calculation-guide":
        source_hub = "family"
    metadata = {
        "author": EDITORIAL_AUTHOR,
        "reviewer": EDITORIAL_REVIEWER,
        "reviewed_at": (
            CORE_AGE_CONTENT_REVIEWED_AT
            if str(page["key"]) in {
                "age",
                "birth_year_age_table",
                "annual_age_calculator",
                "age_comparison_table",
                "birthday_dday_calculator",
            }
            else SOURCE_CHECKED_AT
        ),
        "modified_at": str(page.get("lastmod") or DEFAULT_MODIFIED_AT),
        "official_source_required": official_source_required,
        "sources": sources_for_hub(
            source_hub,
            official_required=official_source_required,
        ),
        "disclaimer": INFORMATIONAL_DISCLAIMER if official_source_required else "",
        "related_search_term_slots": RELATED_SEARCH_TERM_SLOTS.get(str(page["key"]), {}),
    }
    return metadata


def validate_editorial_metadata(
    page: dict[str, object],
    metadata: dict[str, object] | None,
) -> tuple[str, ...]:
    errors: list[str] = []
    if metadata is None:
        return ("missing editorial metadata",)

    for field in ("author", "reviewer", "reviewed_at", "modified_at", "sources"):
        if not metadata.get(field):
            errors.append(f"missing {field}")

    if str(page["key"]) not in OFFICIAL_SOURCE_REQUIRED_KEYS:
        return tuple(errors)

    if not metadata.get("disclaimer"):
        errors.append("missing YMYL disclaimer")

    official_sources = [
        source
        for source in metadata.get("sources", ())
        if isinstance(source, dict) and source.get("official")
    ]
    if not official_sources:
        errors.append("missing official source")

    for source in official_sources:
        for field in ("institution", "title", "url", "checked_at"):
            if not source.get(field):
                errors.append(f"official source missing {field}")
        if not str(source.get("url", "")).startswith("https://"):
            errors.append("official source URL must use HTTPS")

    return tuple(errors)
