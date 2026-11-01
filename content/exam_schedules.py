"""Reviewed official CSAT dates; no inferred or automatically renewed schedules."""
from collections.abc import Mapping
from datetime import date, timedelta
import re
from types import MappingProxyType
from urllib.parse import urlsplit


EXAM_SCHEDULES = (
    MappingProxyType({
        'id': 'csat-academic-2027',
        'academic_year': 2027,
        'execution_year': 2026,
        'exam_date': '2026-11-19',
        'label': '2027학년도 수능 (2026년 시행)',
        'source_url': 'https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=100526&lev=0&m=020402&s=moe',
        'source_title': '2027학년도 대학수학능력시험은 2026년 11월 19일(목)에 시행됩니다',
        'published_on': '2024-08-16',
        'verified_on': '2026-10-31',
        'review_due': '2026-11-12',
        'enabled': True,
    }),
    MappingProxyType({
        'id': 'csat-academic-2028',
        'academic_year': 2028,
        'execution_year': 2027,
        'exam_date': '2027-11-18',
        'label': '2028학년도 수능 (2027년 시행)',
        'source_url': 'https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=103512&lev=0&m=020402&s=moe',
        'source_title': '2028학년도 대학수학능력시험은 2027년 11월 18일(목)에 시행됩니다',
        'published_on': '2025-06-01',
        'verified_on': '2026-10-31',
        'review_due': '2027-03-31',
        'enabled': True,
    }),
)


def _iso_date(value):
    if not isinstance(value, str) or not re.fullmatch(r'[0-9]{4}-[0-9]{2}-[0-9]{2}', value):
        raise ValueError('Schedule dates must use YYYY-MM-DD')
    return date.fromisoformat(value)


def validate_exam_schedules(records):
    """Reject malformed source records without changing them or reading the clock."""
    seen = set()
    for record in records:
        if not isinstance(record, Mapping):
            raise ValueError('Schedule must be a mapping')
        for field in ('id', 'label', 'source_title', 'source_url'):
            if not isinstance(record.get(field), str) or not record[field].strip():
                raise ValueError(f'Missing schedule {field}')
        if record['id'] in seen:
            raise ValueError('Duplicate schedule id')
        seen.add(record['id'])
        if len(record['label']) > 40:
            raise ValueError('Schedule label exceeds the form limit')
        for field in ('academic_year', 'execution_year'):
            if type(record.get(field)) is not int or not 1 <= record[field] <= 9999:
                raise ValueError(f'Invalid {field}')
        exam_date = _iso_date(record.get('exam_date'))
        if exam_date.year != record['execution_year']:
            raise ValueError('Execution year must match the exam date')
        for field in ('published_on', 'verified_on', 'review_due'):
            _iso_date(record.get(field))
        if type(record.get('enabled')) is not bool:
            raise ValueError('Schedule enabled must be a boolean')
        try:
            source = urlsplit(record['source_url'])
            valid_source = (source.scheme == 'https' and bool(source.hostname)
                            and not source.username and not source.password)
        except ValueError as exc:
            raise ValueError('Invalid schedule source URL') from exc
        if not valid_source:
            raise ValueError('Schedule source must be an HTTPS URL')


def build_exam_presets(today: date) -> list[dict]:
    """Project reviewed dates using the caller's single server-response date."""
    if type(today) is not date:
        raise ValueError('today must be a calendar date')
    validate_exam_schedules(EXAM_SCHEDULES)
    presets = []
    for record in EXAM_SCHEDULES:
        exam_date = _iso_date(record['exam_date'])
        if not record['enabled']:
            state = 'under_review'
        elif today > exam_date:
            state = 'ended'
        elif today > _iso_date(record['review_due']):
            state = 'needs_review'
        elif today == exam_date:
            state = 'today'
        else:
            state = 'upcoming'
        preset = dict(record)
        preset.update(
            d100_date=(exam_date - timedelta(days=100)).isoformat(),
            date_digits=exam_date.strftime('%Y%m%d'),
            state=state,
            can_fill=state in {'today', 'upcoming'},
        )
        presets.append(preset)
    return presets
