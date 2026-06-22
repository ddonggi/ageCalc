from __future__ import annotations

from content.guide_pages import GUIDE_PAGES
from content.hub_pages import HUB_PAGES


CONTENT_ACTIONS = frozenset({"keep", "strengthen", "merge", "noindex"})
PUBLIC_RELEASE_BATCHES = frozenset({"existing", "foundation"})
REQUIRED_PAGE_FIELDS = frozenset(
    {
        "key",
        "endpoint",
        "route_values",
        "path",
        "hub",
        "title",
        "search_intent",
        "content_action",
        "indexable",
        "release_batch",
        "lastmod",
        "priority",
        "related_endpoints",
        "related_link_groups",
    }
)


def _related_link_groups(
    endpoint: str,
    related_endpoints: tuple[str, ...],
) -> dict[str, tuple[str, ...]]:
    candidates = {
        "before_calculation": ("guide",),
        "after_result": related_endpoints[:1],
        "adjacent_tools": related_endpoints[1:],
        "official_sources": ("references",),
    }
    seen = {endpoint}
    groups: dict[str, tuple[str, ...]] = {}
    for group_name, endpoints in candidates.items():
        unique_endpoints = []
        for related_endpoint in endpoints:
            if related_endpoint in seen:
                continue
            seen.add(related_endpoint)
            unique_endpoints.append(related_endpoint)
        groups[group_name] = tuple(unique_endpoints)
    return groups


def _page(
    endpoint: str,
    path: str,
    hub: str,
    title: str,
    search_intent: str,
    *,
    content_action: str = "strengthen",
    indexable: bool = True,
    priority: str = "supporting",
    related_endpoints: tuple[str, ...] = (),
) -> dict[str, object]:
    return {
        "key": endpoint,
        "endpoint": endpoint,
        "route_values": {},
        "path": path,
        "hub": hub,
        "title": title,
        "search_intent": search_intent,
        "content_action": content_action,
        "indexable": indexable,
        "release_batch": "existing",
        "lastmod": "2026-06-22",
        "priority": priority,
        "related_endpoints": related_endpoints,
        "related_link_groups": _related_link_groups(endpoint, related_endpoints),
    }


STATIC_PAGE_REGISTRY = (
    _page(
        "index",
        "/",
        "core",
        "오늘 기준 생활 나이 캘린더",
        "나이와 생활 기준 계산 도구 전체 탐색",
        content_action="keep",
        priority="core",
        related_endpoints=("age", "school_grade_calculator", "baby_months", "dog"),
    ),
    _page(
        "age",
        "/age",
        "age",
        "만나이 계산기",
        "생년월일 기준 현재 만나이 계산",
        priority="core",
        related_endpoints=(
            "birth_year_age_table",
            "annual_age_calculator",
            "birthday_dday_calculator",
        ),
    ),
    _page(
        "about",
        "/about",
        "core",
        "콘텐츠 운영 원칙",
        "AgeCalc 콘텐츠 작성과 검수 원칙 확인",
        content_action="keep",
        related_endpoints=("references", "contact", "privacy"),
    ),
    _page(
        "contact",
        "/contact",
        "core",
        "문의 및 운영자 안내",
        "AgeCalc 운영자와 오류 수정 문의 방법 확인",
        content_action="keep",
        related_endpoints=("about", "references", "privacy"),
    ),
    _page(
        "references",
        "/references",
        "core",
        "계산 기준과 참고 자료",
        "AgeCalc 계산 공식과 참고 출처 확인",
        content_action="strengthen",
        priority="core",
        related_endpoints=("about", "guide", "faq"),
    ),
    _page(
        "birth_year_age_table",
        "/birth-year-age-table",
        "age",
        "출생년도별 나이표",
        "출생연도별 현재 나이와 만나이 범위 확인",
        priority="core",
        related_endpoints=("age", "birth_year_zodiac_table", "age_comparison_table"),
    ),
    _page(
        "school_grade_calculator",
        "/school-grade-calculator",
        "education",
        "학년 계산기",
        "출생연도 기준 현재 학교 학년 계산",
        priority="core",
        related_endpoints=("school_entry_year_table", "grade_birth_year_table", "college_entry_year_calculator"),
    ),
    _page(
        "school_entry_year_table",
        "/school-entry-year-table",
        "education",
        "입학년도 계산표",
        "출생연도 기준 초중고 입학년도 확인",
        priority="core",
        related_endpoints=("school_grade_calculator", "grade_age_table", "grade_birth_year_table"),
    ),
    _page(
        "age_gap_calculator",
        "/age-gap-calculator",
        "family",
        "나이 차이 계산기",
        "두 출생연도의 나이 차이와 만나이 범위 비교",
        related_endpoints=("parent_child", "age", "birth_year_age_table"),
    ),
    _page(
        "hundred_day_calculator",
        "/100-day-calculator",
        "anniversary",
        "100일 계산기",
        "시작일 기준 백일째 날짜 계산",
        priority="core",
        related_endpoints=("d_day", "baby_months", "birthday_dday_calculator"),
    ),
    _page(
        "baby_months_table",
        "/baby-months-table",
        "family",
        "개월수 계산표",
        "생후 개월 수별 연령 환산표 확인",
        related_endpoints=("baby_months", "hundred_day_calculator", "school_grade_calculator"),
    ),
    _page(
        "annual_age_calculator",
        "/annual-age-calculator",
        "age",
        "연나이 계산기",
        "생일과 무관한 현재 연나이 계산",
        related_endpoints=("age", "age_comparison_table", "birth_year_age_table"),
    ),
    _page(
        "age_comparison_table",
        "/age-comparison-table",
        "age",
        "만나이·연나이 비교표",
        "만나이 연나이 한국식 나이 차이 비교",
        related_endpoints=("age", "annual_age_calculator", "korean_age_guide"),
    ),
    _page(
        "grade_age_table",
        "/grade-age-table",
        "education",
        "학년 기준 나이표",
        "초중고 학년별 일반적인 나이 확인",
        related_endpoints=("school_grade_calculator", "grade_birth_year_table", "school_entry_year_table"),
    ),
    _page(
        "pet_age_table",
        "/pet-age-table",
        "pets",
        "반려동물 나이표",
        "강아지와 고양이 나이 사람 나이 환산표 확인",
        priority="core",
        related_endpoints=("dog", "cat", "pet_months_table"),
    ),
    _page(
        "korean_age_guide",
        "/korean-age-guide",
        "age",
        "한국나이 기준 정리",
        "만나이 통일 이후 한국 나이 사용 기준 확인",
        related_endpoints=("age", "annual_age_calculator", "age_comparison_table"),
    ),
    _page(
        "pet_months_table",
        "/pet-months-table",
        "pets",
        "반려동물 월령표",
        "강아지 고양이 생후 월령별 사람 나이 환산",
        related_endpoints=("pet_age_table", "dog", "cat"),
    ),
    _page(
        "grade_birth_year_table",
        "/grade-birth-year-table",
        "education",
        "학년별 출생연도표",
        "학교 학년별 일반적인 출생연도 확인",
        related_endpoints=("school_grade_calculator", "grade_age_table", "school_entry_year_table"),
    ),
    _page(
        "birth_year_zodiac_table",
        "/birth-year-zodiac-table",
        "age",
        "출생연도별 띠표",
        "출생연도별 띠와 현재 나이 확인",
        related_endpoints=("birth_year_age_table", "age", "age_comparison_table"),
    ),
    _page(
        "college_entry_year_calculator",
        "/college-entry-year-calculator",
        "education",
        "대학교 학번 나이 계산기",
        "대학교 입학 학번 기준 출생연도와 나이 확인",
        related_endpoints=("school_grade_calculator", "school_entry_year_table", "grade_birth_year_table"),
    ),
    _page(
        "birthday_dday_calculator",
        "/birthday-dday-calculator",
        "anniversary",
        "생일 D-day 계산기",
        "다음 생일까지 남은 날짜 계산",
        priority="core",
        related_endpoints=("age", "d_day", "hundred_day_calculator"),
    ),
    _page(
        "privacy",
        "/privacy",
        "core",
        "개인정보처리방침",
        "AgeCalc 개인정보와 쿠키 처리 방식 확인",
        content_action="keep",
        related_endpoints=("terms", "contact", "about"),
    ),
    _page(
        "terms",
        "/terms",
        "core",
        "이용약관",
        "AgeCalc 서비스 이용 조건과 책임 범위 확인",
        content_action="keep",
        related_endpoints=("privacy", "contact", "about"),
    ),
    _page(
        "guide",
        "/guide",
        "guides",
        "나이 계산 가이드",
        "나이 학년 기념일 계산 기준 가이드 탐색",
        priority="core",
        related_endpoints=("age", "faq", "references"),
    ),
    _page(
        "faq",
        "/faq",
        "guides",
        "자주 묻는 질문",
        "나이 계산 기준과 예외 질문 확인",
        content_action="keep",
        related_endpoints=("guide", "references", "age"),
    ),
    _page(
        "dog",
        "/dog",
        "pets",
        "강아지 나이 계산기",
        "강아지 실제 나이를 사람 나이로 환산",
        priority="core",
        related_endpoints=("pet_age_table", "pet_months_table", "cat"),
    ),
    _page(
        "cat",
        "/cat",
        "pets",
        "고양이 나이 계산기",
        "고양이 실제 나이를 사람 나이로 환산",
        priority="core",
        related_endpoints=("pet_age_table", "pet_months_table", "dog"),
    ),
    _page(
        "baby_months",
        "/baby-months",
        "family",
        "아이 개월 수 계산기",
        "출생일 기준 현재 아이 월령 계산",
        priority="core",
        related_endpoints=("baby_months_table", "hundred_day_calculator", "birthday_dday_calculator"),
    ),
    _page(
        "d_day",
        "/d-day",
        "anniversary",
        "기념일 계산기",
        "특정 날짜까지 남은 일수와 지난 일수 계산",
        priority="core",
        related_endpoints=("hundred_day_calculator", "birthday_dday_calculator", "baby_months"),
    ),
    _page(
        "parent_child",
        "/parent-child",
        "family",
        "부모·자녀 나이 관계 계산기",
        "부모와 자녀의 나이 차이와 주요 생애 시점 계산",
        priority="core",
        related_endpoints=("age_gap_calculator", "baby_months", "school_grade_calculator"),
    ),
    _page(
        "blog_list",
        "/blog",
        "guides",
        "AgeCalc 블로그",
        "나이 건강 생활 기준 편집 글 탐색",
        content_action="keep",
        priority="supporting",
        related_endpoints=("guide", "references", "age"),
    ),
)


def _guide_page(page: dict[str, object]) -> dict[str, object]:
    category_to_hub = {
        "age": "age",
        "school": "education",
        "anniversary": "anniversary",
        "pet": "pets",
        "family": "family",
    }
    slug = str(page["slug"])
    related_endpoints = tuple(endpoint for endpoint, _label in page["related_links"])
    return {
        "key": f"guide:{slug}",
        "endpoint": "guide_detail",
        "route_values": {"slug": slug},
        "path": f"/guides/{slug}",
        "hub": category_to_hub[str(page["category"])],
        "title": str(page["title"]),
        "search_intent": f"{page['title']}에 대한 계산 기준과 예외 확인",
        "content_action": "strengthen",
        "indexable": True,
        "release_batch": "existing",
        "lastmod": "2026-06-22",
        "priority": "supporting",
        "related_endpoints": related_endpoints,
        "related_link_groups": _related_link_groups("guide_detail", related_endpoints),
    }


GUIDE_PAGE_REGISTRY = tuple(_guide_page(page) for page in GUIDE_PAGES)
HUB_PAGE_REGISTRY = tuple(
    {
        "key": f"hub:{hub['key']}",
        "endpoint": "life_hub",
        "route_values": {"hub_key": hub["key"]},
        "path": hub["path"],
        "hub": hub["key"],
        "title": hub["title"],
        "search_intent": f"{hub['title']} 관련 계산기와 기준 탐색",
        "content_action": "keep",
        "indexable": True,
        "release_batch": "foundation",
        "lastmod": "2026-06-22",
        "priority": "core",
        "related_endpoints": tuple(link["endpoint"] for link in hub["primary_links"]),
        "related_link_groups": _related_link_groups(
            "life_hub",
            tuple(link["endpoint"] for link in hub["primary_links"]),
        ),
    }
    for hub in HUB_PAGES
)
PUBLIC_PAGE_REGISTRY = STATIC_PAGE_REGISTRY + HUB_PAGE_REGISTRY + GUIDE_PAGE_REGISTRY


def validate_page_registry() -> tuple[str, ...]:
    errors: list[str] = []

    for page in PUBLIC_PAGE_REGISTRY:
        missing = REQUIRED_PAGE_FIELDS.difference(page)
        if missing:
            errors.append(f"{page.get('key', '<unknown>')}: missing {sorted(missing)}")
        if page.get("content_action") not in CONTENT_ACTIONS:
            errors.append(f"{page.get('key', '<unknown>')}: invalid content_action")

    for field in ("key", "path", "search_intent"):
        values = [str(page[field]) for page in PUBLIC_PAGE_REGISTRY]
        duplicates = sorted({value for value in values if values.count(value) > 1})
        if duplicates:
            errors.append(f"duplicate {field}: {duplicates}")

    return tuple(errors)


def find_page(endpoint: str | None, route_values: dict[str, object] | None = None) -> dict[str, object] | None:
    if not endpoint:
        return None

    route_values = route_values or {}
    for page in PUBLIC_PAGE_REGISTRY:
        if page["endpoint"] != endpoint:
            continue
        expected_values = dict(page["route_values"])
        if all(route_values.get(key) == value for key, value in expected_values.items()):
            return page
    return None


def contextual_links_for(
    page: dict[str, object] | None,
    *,
    recommended_endpoints: tuple[str, ...] = (),
) -> dict[str, object] | None:
    if not page or page["endpoint"] == "index":
        return None

    hub_page = next(
        (
            candidate
            for candidate in HUB_PAGE_REGISTRY
            if candidate["hub"] == page["hub"] and candidate["key"] != page["key"]
        ),
        None,
    )
    if hub_page is None:
        return None

    registry_by_endpoint = {
        str(candidate["endpoint"]): candidate
        for candidate in PUBLIC_PAGE_REGISTRY
        if candidate["endpoint"] != "guide_detail"
    }
    groups = {
        group_name: list(endpoints)
        for group_name, endpoints in dict(page["related_link_groups"]).items()
    }
    if recommended_endpoints:
        groups["after_result"] = list(recommended_endpoints) + groups["after_result"]

    seen_paths = {str(page["path"]), str(hub_page["path"])}
    resolved_groups: dict[str, tuple[dict[str, str], ...]] = {}
    for group_name in (
        "before_calculation",
        "after_result",
        "adjacent_tools",
        "official_sources",
    ):
        links = []
        for endpoint in groups.get(group_name, ()):
            candidate = registry_by_endpoint.get(str(endpoint))
            if candidate is None:
                continue
            path = str(candidate["path"])
            if path in seen_paths:
                continue
            seen_paths.add(path)
            links.append(
                {
                    "endpoint": str(candidate["endpoint"]),
                    "path": path,
                    "label": str(candidate["title"]),
                    "summary": str(candidate["search_intent"]),
                }
            )
        resolved_groups[group_name] = tuple(links)

    return {
        "hub": {
            "path": str(hub_page["path"]),
            "label": str(hub_page["title"]),
        },
        "groups": resolved_groups,
    }


def indexable_static_pages(*, blog_public_indexable: bool) -> tuple[dict[str, object], ...]:
    static_pages = tuple(
        page
        for page in STATIC_PAGE_REGISTRY
        if page["indexable"] and (page["endpoint"] != "blog_list" or blog_public_indexable)
    )
    return static_pages + tuple(page for page in HUB_PAGE_REGISTRY if page["indexable"])


def indexable_guide_pages() -> tuple[dict[str, object], ...]:
    return tuple(page for page in GUIDE_PAGE_REGISTRY if page["indexable"])


SITEMAP_GROUPS = (
    "core",
    "age",
    "family",
    "education",
    "anniversary",
    "retirement",
    "health",
    "pets",
    "generations",
    "guides",
)


def indexable_pages_for_sitemap(
    group: str,
    *,
    blog_public_indexable: bool,
) -> tuple[dict[str, object], ...]:
    if group not in SITEMAP_GROUPS:
        return ()

    if group == "core":
        return tuple(
            page
            for page in STATIC_PAGE_REGISTRY
            if page["indexable"]
            and page["release_batch"] in PUBLIC_RELEASE_BATCHES
            and page["hub"] == "core"
        )

    if group == "guides":
        static_guides = tuple(
            page
            for page in STATIC_PAGE_REGISTRY
            if page["indexable"]
            and page["release_batch"] in PUBLIC_RELEASE_BATCHES
            and page["hub"] == "guides"
            and (page["endpoint"] != "blog_list" or blog_public_indexable)
        )
        return static_guides + indexable_guide_pages()

    static_pages = tuple(
        page
        for page in STATIC_PAGE_REGISTRY
        if page["indexable"]
        and page["release_batch"] in PUBLIC_RELEASE_BATCHES
        and page["hub"] == group
    )
    hub_pages = tuple(
        page
        for page in HUB_PAGE_REGISTRY
        if page["indexable"]
        and page["release_batch"] in PUBLIC_RELEASE_BATCHES
        and page["hub"] == group
    )
    return hub_pages + static_pages


PUBLIC_SITEMAP_ENDPOINTS = tuple(page["endpoint"] for page in STATIC_PAGE_REGISTRY if page["indexable"])
