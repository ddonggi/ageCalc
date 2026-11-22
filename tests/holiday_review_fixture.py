"""A reviewed calendar for integration contracts that also freeze other page dates."""
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch
from zoneinfo import ZoneInfo

from content import korean_holidays


def clock_at(instant):
    """Freeze one absolute instant, preserving the timezone requested by each caller."""
    class Clock(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return instant.astimezone().replace(tzinfo=None)
            return instant.astimezone(tz)

    return patch("app.datetime", Clock)


@contextmanager
def reviewed_calendar():
    metadata = dict(korean_holidays.HOLIDAY_METADATA,
                    verified_on="2026-11-01", next_review="2026-11-08")
    with patch.object(korean_holidays, "HOLIDAY_METADATA", metadata), \
            clock_at(datetime(2026, 11, 1, 12, tzinfo=ZoneInfo("Asia/Seoul"))):
        yield
