"""Shared, deterministic calendar rules used by age calculations."""

from datetime import date, datetime


def parse_iso_date(value: str) -> date:
    """Parse a strict ISO calendar date without accepting impossible dates."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ValueError("date must use a valid YYYY-MM-DD value") from exc


def calculate_man_age(birth_date: date, reference_date: date) -> int:
    """Return Korean international age as of ``reference_date``.

    A February 29 birthday advances on March 1 in a non-leap year because the
    birthday month/day comparison remains explicit and timezone-independent.
    """
    if birth_date > reference_date:
        raise ValueError("birth date cannot be in the future")

    birthday_has_passed = (reference_date.month, reference_date.day) >= (
        birth_date.month,
        birth_date.day,
    )
    return reference_date.year - birth_date.year - (0 if birthday_has_passed else 1)
