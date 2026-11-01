"""Reviewed 2027 Korean government-office holiday facts.

Dates and names were independently transcribed from notice 2026-0078,
page 4; Sundays use standard calendar arithmetic. No external I/O occurs.
This module does not infer holidays, working days or future-year rules.
"""
from collections.abc import Mapping
from datetime import date, timedelta
from types import MappingProxyType


SOURCE_INFO = MappingProxyType({
    'year': 2027,
    'source_id': 'kasa-2026-0078',
    'notice_number': '우주항공청공고 제2026-0078호',
    'published_on': '2026-06-29',
    'source_url': 'https://www.gwanbo.go.kr/ezpdf/customLayout.jsp?contentId=I0000000000000001782374733940000&tocId=I0000000000000001782199865342000&isTocOrder=N',
    'source_sha256': '10412c8632ab2e8e9937cbd3a8fa6ee184e08cbd9aa541dd4d44229cb11a67b3',
    'verified_on': '2026-11-01',
    'next_review': '2026-11-08',
    'reviewer': 'Phase1 독립 QA(공식 원표 전 행 대조)',
    'maintenance_role': '9급 주무관',
    'version': '2027.20261101.1',
    'active': True,
})
HOLIDAY_METADATA = MappingProxyType(dict(SOURCE_INFO))

# Own date records; original publication layout and assets are not reproduced.
# Preserve original U+2219 in source names; only display labels use U+00B7.
_NATIONAL_FACTS = (
    ('01-01', '1월 1일', 'national'),
    ('02-06', '설날(연휴)', 'national'),
    ('02-07', '설날(연휴)', 'national'),
    ('02-08', '설날(연휴)', 'national'),
    ('02-09', '대체공휴일(설날)', 'substitute'),
    ('03-01', '3∙1절', 'national'),
    ('05-01', '노동절', 'national'),
    ('05-03', '대체공휴일(노동절)', 'substitute'),
    ('05-05', '어린이날', 'national'),
    ('05-13', '부처님 오신 날', 'national'),
    ('06-06', '현충일', 'national'),
    ('07-17', '제헌절', 'national'),
    ('07-19', '대체공휴일(제헌절)', 'substitute'),
    ('08-15', '광복절', 'national'),
    ('08-16', '대체공휴일(광복절)', 'substitute'),
    ('09-14', '추석(연휴)', 'national'),
    ('09-15', '추석(연휴)', 'national'),
    ('09-16', '추석(연휴)', 'national'),
    ('10-03', '개천절', 'national'),
    ('10-04', '대체공휴일(개천절)', 'substitute'),
    ('10-09', '한글날', 'national'),
    ('10-11', '대체공휴일(한글날)', 'substitute'),
    ('12-25', '기독탄신일', 'national'),
    ('12-27', '대체공휴일(기독탄신일)', 'substitute'),
)
_LOCAL_FACTS = (
    ('04-03', '4∙3희생자 추념일', '제주특별자치도'),
    ('05-11', '동학농민혁명 기념일', '전북특별자치도 정읍시'),
    ('05-18', '5∙18민주화운동 기념일', '광주광역시'),
)
NATIONAL_HOLIDAYS = tuple(MappingProxyType({
    'id': f'kr-2027-{day}', 'date': f'2027-{day}',
    'original_label': label, 'label': label.replace('∙', '·'), 'type': kind,
    'scope': 'national', 'source_page': 4, 'source_id': SOURCE_INFO['source_id'],
}) for day, label, kind in _NATIONAL_FACTS)
LOCAL_HOLIDAYS = tuple(MappingProxyType({
    'id': f'kr-local-2027-{day}', 'date': f'2027-{day}',
    'original_label': label, 'label': label.replace('∙', '·'), 'type': 'local',
    'scope': 'local', 'jurisdiction': jurisdiction,
    'source_page': 4, 'source_id': SOURCE_INFO['source_id'],
}) for day, label, jurisdiction in _LOCAL_FACTS)


def _iso_date(value):
    if not isinstance(value, str):
        raise ValueError('Date must be an ISO string')
    try:
        parsed = date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError('Invalid date') from exc
    if parsed.isoformat() != value:
        raise ValueError('Date must use YYYY-MM-DD')
    return parsed


def validate_holiday_data(metadata, national, local):
    """Reject missing, malformed or source-inconsistent data, without I/O."""
    if not isinstance(metadata, Mapping):
        raise ValueError('Missing metadata')
    for key in ('year', 'source_id', 'notice_number', 'published_on', 'source_url', 'source_sha256'):
        if metadata.get(key) != SOURCE_INFO[key] or type(metadata.get(key)) is not type(SOURCE_INFO[key]):
            raise ValueError('Source metadata does not match reviewed notice')
    for key in ('reviewer', 'maintenance_role', 'version'):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError('Missing review metadata')
    if type(metadata.get('active')) is not bool:
        raise ValueError('Active must be a boolean')
    verified = _iso_date(metadata.get('verified_on'))
    review = _iso_date(metadata.get('next_review'))
    if verified < _iso_date(metadata['published_on']) or review != verified + timedelta(days=7):
        raise ValueError('Invalid review interval')
    ids, dates = set(), set()
    for records, facts, is_local in ((national, _NATIONAL_FACTS, False), (local, _LOCAL_FACTS, True)):
        if not isinstance(records, (tuple, list)) or len(records) != len(facts):
            raise ValueError('Incomplete official facts')
        expected = {f'2027-{row[0]}': row for row in facts}
        for row in records:
            if not isinstance(row, Mapping):
                raise ValueError('Invalid holiday record')
            for key in ('id', 'date', 'original_label', 'label', 'type', 'scope', 'source_id'):
                if not isinstance(row.get(key), str) or not row[key].strip():
                    raise ValueError('Missing holiday field')
            parsed = _iso_date(row['date'])
            if parsed.year != metadata['year'] or row['date'] not in expected:
                raise ValueError('Unsupported official date')
            if row['date'] in dates or row['id'] in ids:
                raise ValueError('Duplicate date or identifier')
            dates.add(row['date'])
            ids.add(row['id'])
            fact = expected[row['date']]
            prefix = 'kr-local-2027-' if is_local else 'kr-2027-'
            kind = 'local' if is_local else fact[2]
            scope = 'local' if is_local else 'national'
            if (row['id'] != prefix + fact[0] or row['original_label'] != fact[1]
                    or row['label'] != fact[1].replace('∙', '·') or row['type'] != kind or row['scope'] != scope
                    or row['source_id'] != metadata['source_id']
                    or type(row.get('source_page')) is not int or row['source_page'] != 4):
                raise ValueError('Holiday differs from reviewed official fact')
            if is_local and row.get('jurisdiction') != fact[2]:
                raise ValueError('Incorrect local jurisdiction')


def build_holiday_calendar(today):
    """Build a detached display snapshot; unavailable data never escapes."""
    if type(today) is not date:
        raise TypeError('today must be a datetime.date')
    result = {'metadata': dict(SOURCE_INFO), 'today': today.isoformat(),
              'available': False, 'state': 'invalid', 'months': [],
              'local_holidays': [], 'counts': None}
    try:
        validate_holiday_data(HOLIDAY_METADATA, NATIONAL_HOLIDAYS, LOCAL_HOLIDAYS)
    except ValueError:
        return result
    result['metadata'] = dict(HOLIDAY_METADATA)
    if not HOLIDAY_METADATA['active']:
        result['state'] = 'disabled'
        return result
    if today < _iso_date(HOLIDAY_METADATA['verified_on']) or today > _iso_date(HOLIDAY_METADATA['next_review']):
        result['state'] = 'needs_review'
        return result
    sundays = set()
    cursor = date(2027, 1, 1)
    while cursor.year == 2027:
        if cursor.weekday() == 6:
            sundays.add(cursor.isoformat())
        cursor += timedelta(days=1)
    named = {row['date'] for row in NATIONAL_HOLIDAYS}
    records = [dict(row, weekday=_iso_date(row['date']).weekday()) for row in NATIONAL_HOLIDAYS]
    result.update(available=True, state='current', months=[{
        'month': month,
        'holidays': sorted((row for row in records if _iso_date(row['date']).month == month), key=lambda row: row['date']),
        'sundays': sorted(day for day in sundays if _iso_date(day).month == month),
    } for month in range(1, 13)],
        local_holidays=[dict(row, weekday=_iso_date(row['date']).weekday()) for row in LOCAL_HOLIDAYS],
        counts={'named': len(named), 'substitute': sum(row['type'] == 'substitute' for row in records),
                'sundays': len(sundays), 'overlap': len(named & sundays), 'total': len(named | sundays)})
    return result


def holiday_calendar_available(today):
    """Use exactly the display snapshot's validity decision for navigation."""
    return build_holiday_calendar(today)['available']
