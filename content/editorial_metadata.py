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
    if not page or page["endpoint"] == "index":
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
