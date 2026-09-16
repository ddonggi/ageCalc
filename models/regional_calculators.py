"""Pure calculation engines for locale-specific date tools."""

from __future__ import annotations

import calendar
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Callable

from korean_lunar_calendar import KoreanLunarCalendar


HOLIDAY_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "regional_holidays.json"
_MAX_CUSTOM_DATES = 100

_LOCALES = {
    "lunar_birthday": {"ko"},
    "business_days": {"ja", "pt-BR"},
    "school_year": {"ja"},
    "birth_date_range": {"en", "pt-BR"},
    "japanese_era": {"ja"},
}

_PARAMETERS = {
    "lunar_birthday": {"month", "day", "leap", "reference"},
    "business_days": {
        "mode",
        "start",
        "end",
        "amount",
        "include_end",
        "excluded",
    },
    "school_year": {"birth", "gap", "course"},
    "birth_date_range": {"reference", "age"},
    "japanese_era": {"mode", "date", "era", "era_year", "month", "day"},
}


def _iso(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_date") from None


def _integer(value: str) -> int:
    try:
        if not isinstance(value, str) or not value or value.strip() != value:
            raise ValueError
        return int(value)
    except (TypeError, ValueError):
        raise ValueError("invalid_integer") from None


def _bounded_integer(value: str, minimum: int, maximum: int) -> int:
    number = _integer(value)
    if not minimum <= number <= maximum:
        raise ValueError("invalid_range")
    return number


def _require(values: dict[str, str], names: set[str]) -> None:
    if any(not values.get(name) for name in names):
        raise ValueError("invalid_parameters")


def _shift_year(value: date, years: int) -> date:
    year = value.year + years
    if not 1 <= year <= 9999:
        raise ValueError("unsupported_range")
    day = min(value.day, calendar.monthrange(year, value.month)[1])
    return date(year, value.month, day)


def _birth_date_range(values: dict[str, str]) -> dict:
    _require(values, {"reference", "age"})
    reference = _iso(values["reference"])
    age = _bounded_integer(values["age"], 0, 150)
    latest = _shift_year(reference, -age)
    try:
        earliest = _shift_year(reference, -(age + 1)) + timedelta(days=1)
    except OverflowError:
        raise ValueError("unsupported_range") from None
    return {
        "rows": [("earliest", earliest.isoformat()), ("latest", latest.isoformat())],
        "note": "birth_date_range_note",
    }


def _school_year(values: dict[str, str]) -> dict:
    _require(values, {"birth", "gap", "course"})
    birth = _iso(values["birth"])
    gap = _bounded_integer(values["gap"], 0, 10)
    course = _bounded_integer(values["course"], 2, 6)
    if course not in {2, 4, 6}:
        raise ValueError("invalid_range")

    # Japan's school-age cohort runs April 2 through the following April 1.
    elementary_year = birth.year + (6 if (birth.month, birth.day) <= (4, 1) else 7)
    years = {
        "elementary_entry": (elementary_year, 4, 1),
        "elementary_graduation": (elementary_year + 6, 3, 31),
        "junior_high_entry": (elementary_year + 6, 4, 1),
        "junior_high_graduation": (elementary_year + 9, 3, 31),
        "high_school_entry": (elementary_year + 9, 4, 1),
        "high_school_graduation": (elementary_year + 12, 3, 31),
        "university_entry": (elementary_year + 12 + gap, 4, 1),
        "university_graduation": (elementary_year + 12 + gap + course, 3, 31),
    }
    try:
        rows = [(label, date(*parts).isoformat()) for label, parts in years.items()]
    except ValueError:
        raise ValueError("unsupported_range") from None
    return {"rows": rows, "note": "school_year_note"}


_ERAS = (
    ("meiji", "明治", date(1868, 1, 25), date(1912, 7, 29)),
    ("taisho", "大正", date(1912, 7, 30), date(1926, 12, 24)),
    ("showa", "昭和", date(1926, 12, 25), date(1989, 1, 7)),
    ("heisei", "平成", date(1989, 1, 8), date(2019, 4, 30)),
    ("reiwa", "令和", date(2019, 5, 1), date.max),
)
_ERA_BY_NAME = {era[0]: era for era in _ERAS}
_JAPAN_GREGORIAN_START = date(1873, 1, 1)


def _japanese_era(values: dict[str, str]) -> dict:
    _require(values, {"mode"})
    mode = values["mode"]
    if mode == "to_era":
        _require(values, {"date"})
        target = _iso(values["date"])
        if target < _JAPAN_GREGORIAN_START:
            raise ValueError("unsupported_range")
        for _key, symbol, start, end in reversed(_ERAS):
            if start <= target <= end:
                era_year = target.year - start.year + 1
                year_text = "元" if era_year == 1 else str(era_year)
                formatted = f"{symbol}{year_text}年{target.month}月{target.day}日"
                return {"rows": [("era_date", formatted)], "note": "japanese_era_note"}
        raise ValueError("unsupported_range")
    if mode == "from_era":
        _require(values, {"era", "era_year", "month", "day"})
        if values["era"] not in _ERA_BY_NAME:
            raise ValueError("invalid_era")
        _key, _symbol, start, end = _ERA_BY_NAME[values["era"]]
        era_year = _bounded_integer(values["era_year"], 1, 9999)
        month = _bounded_integer(values["month"], 1, 12)
        day = _bounded_integer(values["day"], 1, 31)
        year = start.year + era_year - 1
        try:
            target = date(year, month, day)
        except ValueError:
            raise ValueError("invalid_date") from None
        if target < _JAPAN_GREGORIAN_START:
            raise ValueError("unsupported_range")
        if not start <= target <= end:
            raise ValueError("invalid_era_date")
        return {
            "rows": [("gregorian_date", target.isoformat())],
            "note": "japanese_era_note",
        }
    raise ValueError("invalid_mode")


def _lunar_birthday(values: dict[str, str]) -> dict:
    _require(values, {"month", "day", "reference"})
    month = _bounded_integer(values["month"], 1, 12)
    day = _bounded_integer(values["day"], 1, 30)
    reference = _iso(values["reference"])
    leap_value = values.get("leap", "")
    if leap_value not in {"", "1"}:
        raise ValueError("invalid_parameters")
    is_leap = leap_value == "1"
    if not 1900 <= reference.year <= 2049:
        raise ValueError("unsupported_range")

    reference_lunar = KoreanLunarCalendar()
    if not reference_lunar.setSolarDate(reference.year, reference.month, reference.day):
        raise ValueError("unsupported_range")
    first_lunar_year = reference_lunar.lunarYear

    table: list[list[str]] = []
    future_dates: list[date] = []
    for lunar_year in range(first_lunar_year, first_lunar_year + 6):
        converted = ""
        status = "unsupported_year"
        if lunar_year <= 2049:
            lunar = KoreanLunarCalendar()
            converted_ok = lunar.setLunarDate(lunar_year, month, day, is_leap)
            status = "invalid_lunar_date"
            if converted_ok:
                # The library falls back to the regular month if a requested
                # leap month does not exist, so its returned flag must agree.
                if lunar.isIntercalation == is_leap:
                    candidate = _iso(lunar.SolarIsoFormat())
                    converted = candidate.isoformat()
                    status = "available"
                    if candidate >= reference:
                        future_dates.append(candidate)
                elif is_leap:
                    status = "missing_leap_month"
        table.append([str(lunar_year), converted, status])

    rows = [("next_birthday", min(future_dates).isoformat() if future_dates else "next_unavailable")]
    return {"rows": rows, "table": table, "note": "lunar_birthday_note"}


def _holiday_data() -> dict:
    try:
        data = json.loads(HOLIDAY_DATA_PATH.read_text(encoding="utf-8"))
        start = int(data["start_year"])
        end = int(data["end_year"])
        calendars = data["calendars"]
    except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError):
        raise ValueError("holiday_data_unavailable") from None
    if start > end or not isinstance(calendars, dict):
        raise ValueError("holiday_data_unavailable")
    return data


def _custom_dates(raw: str) -> set[date]:
    entries = [item.strip() for item in raw.splitlines() if item.strip()]
    if len(entries) > _MAX_CUSTOM_DATES:
        raise ValueError("too_many_excluded_dates")
    return {_iso(item) for item in entries}


def _business_days(values: dict[str, str], locale: str) -> dict:
    _require(values, {"mode", "start"})
    mode = values["mode"]
    if mode not in {"count", "add", "subtract"}:
        raise ValueError("invalid_mode")
    holiday_data = _holiday_data()
    start_year = int(holiday_data["start_year"])
    end_year = int(holiday_data["end_year"])
    calendar_data = holiday_data["calendars"].get(locale)
    if not isinstance(calendar_data, dict):
        raise ValueError("holiday_data_unavailable")
    try:
        holidays = {_iso(day) for day in calendar_data}
    except ValueError:
        raise ValueError("holiday_data_unavailable") from None
    custom = _custom_dates(values.get("excluded", ""))
    start = _iso(values["start"])

    def in_range(day: date) -> bool:
        return start_year <= day.year <= end_year

    def is_workday(day: date) -> bool:
        return day.weekday() < 5 and day not in holidays and day not in custom

    if not in_range(start) or any(not in_range(day) for day in custom):
        raise ValueError("unsupported_range")

    if mode == "count":
        _require(values, {"end"})
        end = _iso(values["end"])
        if end < start:
            raise ValueError("invalid_range")
        if not in_range(end):
            raise ValueError("unsupported_range")
        include_end = values.get("include_end", "")
        if include_end not in {"", "1"}:
            raise ValueError("invalid_parameters")
        stop = end if include_end == "1" else end - timedelta(days=1)
        count = 0
        cursor = start
        while cursor <= stop:
            count += is_workday(cursor)
            cursor += timedelta(days=1)
        return {"rows": [("workdays", str(count))], "note": "holiday_range_note"}

    _require(values, {"amount"})
    amount = _integer(values["amount"])
    if amount < 0:
        raise ValueError("invalid_range")
    direction = 1 if mode == "add" else -1
    remaining = amount
    cursor = start
    while remaining:
        try:
            cursor += timedelta(days=direction)
        except OverflowError:
            raise ValueError("unsupported_range") from None
        if not in_range(cursor):
            raise ValueError("unsupported_range")
        if is_workday(cursor):
            remaining -= 1
    return {"rows": [("result_date", cursor.isoformat())], "note": "holiday_range_note"}


def calculate(kind: str, values: dict[str, str], locale: str) -> dict:
    """Validate and dispatch a supported regional calculation."""
    if kind not in _LOCALES:
        raise ValueError("invalid_kind")
    if locale not in _LOCALES[kind]:
        raise ValueError("invalid_locale")
    if not isinstance(values, dict) or any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in values.items()
    ):
        raise ValueError("invalid_parameters")
    if set(values) - _PARAMETERS[kind]:
        raise ValueError("invalid_parameters")

    calculators: dict[str, Callable[[dict[str, str]], dict]] = {
        "lunar_birthday": _lunar_birthday,
        "school_year": _school_year,
        "birth_date_range": _birth_date_range,
        "japanese_era": _japanese_era,
    }
    if kind == "business_days":
        return _business_days(values, locale)
    return calculators[kind](values)
