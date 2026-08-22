"""Deterministic calculations for a birth-date life timeline."""

from __future__ import annotations

from datetime import date


KOREAN_ZODIAC = (
    "원숭이",
    "닭",
    "개",
    "돼지",
    "쥐",
    "소",
    "호랑이",
    "토끼",
    "용",
    "뱀",
    "말",
    "양",
)


def _birthday_for_age(birth_date: date, year: int) -> date:
    try:
        return birth_date.replace(year=year)
    except ValueError:
        return date(year, 3, 1)


def _next_exact_birthday(birth_date: date, as_of: date) -> date:
    year = as_of.year
    while True:
        try:
            candidate = birth_date.replace(year=year)
        except ValueError:
            year += 1
            continue
        if candidate >= as_of:
            return candidate
        year += 1


def _constellation(month: int, day: int) -> str:
    month_day = (month, day)
    if month_day >= (12, 22) or month_day <= (1, 19):
        return "염소자리"
    boundaries = (
        ((1, 20), "물병자리"),
        ((2, 19), "물고기자리"),
        ((3, 21), "양자리"),
        ((4, 20), "황소자리"),
        ((5, 21), "쌍둥이자리"),
        ((6, 22), "게자리"),
        ((7, 23), "사자자리"),
        ((8, 23), "처녀자리"),
        ((9, 23), "천칭자리"),
        ((10, 23), "전갈자리"),
        ((11, 23), "사수자리"),
    )
    constellation = "염소자리"
    for boundary, label in boundaries:
        if month_day >= boundary:
            constellation = label
        else:
            break
    return constellation


def build_life_timeline(birth_date: date, as_of: date) -> dict[str, object]:
    """Return life-timeline facts calculated against one explicit date."""
    if birth_date > as_of:
        raise ValueError("생년월일은 기준일보다 늦을 수 없습니다.")

    birthday_this_year = _birthday_for_age(birth_date, as_of.year)
    full_age = as_of.year - birth_date.year - (as_of < birthday_this_year)
    next_birthday = _next_exact_birthday(birth_date, as_of)

    return {
        "full_age": full_age,
        "korean_year_age": as_of.year - birth_date.year,
        "days_lived": (as_of - birth_date).days,
        "next_birthday": next_birthday,
        "days_until_birthday": (next_birthday - as_of).days,
        "zodiac": KOREAN_ZODIAC[birth_date.year % 12],
        "constellation": _constellation(birth_date.month, birth_date.day),
    }
