"""Next calculations, selected from the public tools available in the reader's language."""

import re
from functools import lru_cache
from urllib.parse import urlencode

from jinja2 import pass_context

from content.i18n import PAGE_BY_KEY, catalog, localized_url, supported_locales
from content.page_registry import PRIVACY_NO_THIRD_PARTY_PATHS, PUBLIC_RELEASE_BATCHES


# The result name is a route output. Example rows and default previews never qualify.
# None denotes a browser calculation. The noindex timeline is a source only.
RELATED_TOOLS = {
    "index": (None, ("school_grade_calculator", "birthday_dday_calculator")),
    "age": ("result_details", ("annual_age_calculator", "birthday_dday_calculator")),
    "annual_age_calculator": ("selected_snapshot", ("age", "birth_year_age_table")),
    "birth_year_age_table": ("selected_row", ("annual_age_calculator", "school_grade_calculator")),
    "age_comparison_table": ("selected_row", ("age",)),
    "birth_year_zodiac_table": ("selected_row", ("birth_year_age_table",)),
    "age_gap_calculator": ("selected_gap", ("parent_child", "age")),
    "parent_child": ("parent_results", ("school_grade_calculator", "birthday_dday_calculator")),
    "baby_months": ("baby_result", ("hundred_day_calculator", "baby_months_table")),
    "baby_months_table": ("selected_row", ("baby_months",)),
    "school_grade_calculator": ("selected_row", ("grade_birth_year_table", "birth_year_age_table")),
    "grade_birth_year_table": ("selected_row", ("school_grade_calculator", "college_entry_year_calculator")),
    "college_entry_year_calculator": ("selected_row", ("birth_year_age_table", "school_grade_calculator")),
    "life_timeline": ("timeline", ("birthday_dday_calculator", "birth_year_zodiac_table")),
    "birthday_dday_calculator": ("selected_snapshot", ("d_day", "age")),
    "d_day": ("dday_result", ("days_between_dates", "hundred_day_calculator")),
    "hundred_day_calculator": ("selected_snapshot", ("d_day", "date_add_subtract")),
    "days_between_dates": (None, ("date_add_subtract", "business_days")),
    "date_add_subtract": (None, ("days_between_dates", "d_day")),
    "lunar_birthday": ("result", ("d_day",)),
    "time_duration_calculator": (None, ("weekly_work_hours_calculator",)),
    "weekly_work_hours_calculator": (None, ("time_duration_calculator",)),
    "world_time_converter": (None, ("time_duration_calculator",)),
    "dog": ("pet_result", ()),
    "cat": ("pet_result", ()),
    "pet_age_table": ("selected_row", ()),
    "pet_months_table": ("selected_row", ()),
    "business_days": ("result", ()),
    "school_year": ("result", ("d_day", "age")),
    "birth_date_range": ("result", ("age",)),
    "japanese_era": ("result", ("days_between_dates",)),
}


def _available_destination(key, locale):
    page = PAGE_BY_KEY.get(key)
    return (page is not None and page["indexable"] and page["content_action"] in ("keep", "strengthen")
            and page["release_batch"] in PUBLIC_RELEASE_BATCHES and locale in supported_locales(page))


@lru_cache(maxsize=None)
def baseline_destinations(locale):
    destinations = {}
    for key in RELATED_TOOLS:
        if not _available_destination(key, locale):
            continue
        path = localized_url(key, locale)
        destinations[path] = {"tool": key, "measurable": path not in PRIVACY_NO_THIRD_PARTY_PATHS}
    if locale == "ko":
        destinations["/life-timeline"] = {"tool": "life_timeline", "measurable": True}
    return destinations


# Alternative orders are part of the same mapping used to check translated CTAs.
PET_CALCULATOR_VARIANTS = {
    "adoption": ("d_day",), "months": ("pet_months_table",), "years": ("pet_age_table",),
}
PET_SPECIES = {"dog": ("dog",), "cat": ("cat",)}
CARD_VARIANTS = {
    "age": {"lunar": ("lunar_birthday", "annual_age_calculator")},
    "baby_months": {"over_table_limit": ("hundred_day_calculator",)},
    "dog": PET_CALCULATOR_VARIANTS,
    "cat": PET_CALCULATOR_VARIANTS,
    "pet_age_table": PET_SPECIES,
    "pet_months_table": {**PET_SPECIES, "dog_year": ("dog", "pet_age_table"), "cat_year": ("cat", "pet_age_table")},
    "business_days": {"workdays": ("days_between_dates",), "result_date": ("date_add_subtract",)},
}


def _orders(source, locale):
    if source == "age" and locale != "ko":
        return {"default": ("age_gap_calculator", "birth_date_range")}
    return {"default": RELATED_TOOLS[source][1], **CARD_VARIANTS.get(source, {})}


def _result_variant(source, result, context):
    if not result:
        return "default"
    if source == "age" and context.get("calendar_type") == "lunar":
        return "lunar"
    if source == "baby_months" and result["months"] > 36:
        return "over_table_limit"
    if source in ("dog", "cat"):
        if result["kind"] == "adoption":
            return "adoption"
        if 1 <= result["months"] <= 24:
            return "months"
        if 24 < result["months"] <= 240:
            return "years"
    if source in ("pet_age_table", "pet_months_table"):
        return result["pet"] + ("_year" if result.get("months", 0) >= 12 else "")
    if source == "business_days":
        # The calculator returns a count for a period and a date for both shifts.
        return result["rows"][0][0]
    return "default"


def _year_query(source, destination, result, context):
    """Carry across only existing year links within the destination's input bounds."""
    if not result:
        return {}
    if source == "age" and destination == "annual_age_calculator":
        year = result["birth_year"]
        return {"birth_year": year} if 1900 <= year <= context["today"].year else {}
    if source == "birth_year_age_table":
        parameter = "birth_year" if destination == "annual_age_calculator" else "year"
        return {parameter: result["year"]}
    if source == "grade_birth_year_table" and destination == "college_entry_year_calculator":
        year = int(result["high_graduation_date"][:4])
        if year in context["college_entry_years"]:
            return {"year": year}
    if source == "college_entry_year_calculator" or (
        source == "annual_age_calculator" and destination == "birth_year_age_table"
    ):
        year = result["birth_year"]
        if max(1900, context["current_year"] - 100) <= year <= context["current_year"]:
            return {"year": year}
    return {}


# Some transitions require more specific wording than the destination's usual CTA.
COPY_OVERRIDES = {
    ("lunar_birthday", "d_day"): "lunar_countdown",
    ("college_entry_year_calculator", "birth_year_age_table"): "cohort_age",
    ("college_entry_year_calculator", "school_grade_calculator"): "cohort_school",
    ("world_time_converter", "time_duration_calculator"): "meeting_duration",
}


def validate_related_copy(locale, copy):
    """Check each reachable CTA, including conditionally rendered result modes."""
    def require_text(value, key, placeholders=()):
        if (not isinstance(value, str) or not value.strip()
                or sorted(re.findall(r"\{\w+\}", value)) != sorted(placeholders)):
            raise ValueError(f"Invalid related translation: {locale}/{key}")

    if not isinstance(copy, dict) or not isinstance(copy.get("cards"), dict):
        raise ValueError(f"Missing related translations: {locale}")
    require_text(copy.get("heading"), "heading")
    for source in RELATED_TOOLS:
        if not (_available_destination(source, locale) or (source == "life_timeline" and locale == "ko")):
            continue
        for order in _orders(source, locale).values():
            for destination in order:
                if not _available_destination(destination, locale):
                    continue
                key = COPY_OVERRIDES.get((source, destination), destination)
                pair = copy["cards"].get(key)
                if not isinstance(pair, list) or len(pair) != 2:
                    raise ValueError(f"Missing related translation: {locale}/{key}")
                require_text(pair[0], key, ("{year}",) if key in ("cohort_age", "cohort_school") else ())
                require_text(pair[1], key)


@pass_context
def related_tool_state(context):
    source = context["related_source"]
    locale = context["locale_code"]
    result_key, _ = RELATED_TOOLS[source]
    result = context.get(result_key) if result_key else None
    copy = catalog(locale)["related_tools"]
    cards = []
    seen = {source}
    order = _orders(source, locale)[_result_variant(source, result, context)]
    for destination in order:
        if destination in seen or not _available_destination(destination, locale):
            continue
        seen.add(destination)
        path = localized_url(destination, locale)
        query = _year_query(source, destination, result, context)
        text_key = COPY_OVERRIDES.get((source, destination), destination)
        title, description = copy["cards"][text_key]
        if source == "college_entry_year_calculator" and result:
            title = title.replace("{year}", str(result["birth_year"]))
        elif "{year}" in title:
            title, description = copy["cards"][destination]
        cards.append({
            "key": destination, "title": title, "description": description, "path": path,
            "href": path + ("?" + urlencode(query) if query else ""),
            "measurable": path not in PRIVACY_NO_THIRD_PARTY_PATHS,
        })
        if len(cards) == 2:
            break
    return {"heading": copy["heading"], "success": bool(result), "cards": cards}
