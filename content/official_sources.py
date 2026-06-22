from __future__ import annotations


SOURCE_CHECKED_AT = "2026-06-22"


def _source(institution: str, title: str, url: str) -> dict[str, object]:
    return {
        "institution": institution,
        "title": title,
        "url": url,
        "checked_at": SOURCE_CHECKED_AT,
        "official": True,
    }


OFFICIAL_SOURCES_BY_HUB = {
    "age": (
        _source(
            "국가법령정보센터",
            "민법 제158조(나이의 계산과 표시)",
            "https://www.law.go.kr/법령/민법",
        ),
    ),
    "education": (
        _source(
            "국가법령정보센터",
            "초·중등교육법 제13조(취학 의무)",
            "https://www.law.go.kr/법령/초·중등교육법",
        ),
    ),
    "family": (
        _source(
            "질병관리청",
            "예방접종도우미",
            "https://nip.kdca.go.kr/",
        ),
        _source(
            "국민건강보험공단",
            "영유아 건강검진 안내",
            "https://www.nhis.or.kr/",
        ),
    ),
    "health": (
        _source(
            "국민건강보험공단",
            "건강검진 안내",
            "https://www.nhis.or.kr/",
        ),
    ),
    "pets": (
        _source(
            "American Animal Hospital Association",
            "Canine Life Stage Guidelines",
            "https://www.aaha.org/resources/life-stage-canine-2019/",
        ),
        _source(
            "Feline Veterinary Medical Association",
            "Feline Life Stage Guidelines",
            "https://catvets.com/resource/life-stage-guidelines/",
        ),
    ),
}


INTERNAL_METHOD_SOURCE = {
    "institution": "AgeCalc",
    "title": "계산 기준과 참고 자료",
    "url": "/references",
    "checked_at": SOURCE_CHECKED_AT,
    "official": False,
}


def sources_for_hub(hub: str, *, official_required: bool) -> tuple[dict[str, object], ...]:
    sources = tuple(OFFICIAL_SOURCES_BY_HUB.get(hub, ()))
    if official_required and sources:
        return sources
    if sources:
        return sources + (INTERNAL_METHOD_SOURCE,)
    return (INTERNAL_METHOD_SOURCE,)
