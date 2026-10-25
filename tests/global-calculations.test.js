const assert = require('node:assert/strict');
const fs = require('node:fs');
assert.ok(fs.existsSync('static/js/global-calculations.js'), 'global calculation module must exist');
const calc = require('../static/js/global-calculations.js');
assert.equal(calc.age('1992-10-02', '2026-10-01').years, 33);
assert.equal(calc.age('1992-10-02', '2026-10-02').years, 34);
assert.deepEqual(calc.duration('2025-01-31', '2025-02-28'), {years: 0, months: 1, days: 0});
assert.deepEqual(calc.duration('2000-02-29', '2026-02-28'), {years: 25, months: 11, days: 30});
assert.equal(calc.age('2000-02-29', '2026-02-28').totalMonths, 312);
assert.equal(calc.age('2000-02-29', '2026-03-01').years, 26);
assert.equal(calc.birthday(2, 29, '2026-02-28').nextDate, '2028-02-29');
assert.equal(calc.birthday(9, 9, '2026-09-09').days, 0);
assert.equal(calc.birthday(9, 8, '2026-09-09').nextDate, '2027-09-08');
assert.equal(calc.hundred('2026-01-01', '2026-01-01').date, '2026-04-10');
assert.equal(calc.hundred('2024-01-01', '2024-01-01').date, '2024-04-09');
assert.equal(calc.daysBetween('2026-03-07', '2026-03-09'), 2);
assert.equal(calc.daysBetween('2026-11-01', '2026-11-02'), 1);
assert.equal(calc.baby('2025-01-31', '2025-02-28').months, 1);
assert.equal(calc.baby('2025-01-31', '2025-02-28').days, 28);
assert.equal(calc.yearGap('2000', '1995', '2026-09-09'), 5);
assert.equal(calc.yearGap('1995', '2000', '2026-09-09'), 5);
assert.equal(calc.yearGap('2000', '2000', '2026-09-09'), 0);
assert.throws(() => calc.yearGap('', '2000', '2026-09-09'), /invalid_year/);
assert.throws(() => calc.yearGap('1899', '2000', '2026-09-09'), /invalid_year/);
assert.throws(() => calc.age('2026-09-10', '2026-09-09'), /reference_before_birth/);
assert.throws(() => calc.birthday(2, 30, '2026-09-09'), /invalid_date/);
assert.throws(() => calc.hundred('9999-12-31', '2026-09-09'), /date_range/);
assert.throws(() => calc.isoParts('2026', '2', '30'), /invalid_date/);
assert.throws(() => calc.isoParts('0000', '2', '1'), /invalid_date/);
assert.equal(calc.isoParts('1900', '2', '28'), '1900-02-28');
assert.equal(calc.isoParts('0001', '1', '1'), '0001-01-01');
console.log('Global calendar contracts passed');
assert.deepEqual(calc.dateRange('2026-09-01', '2026-09-10'), {days: 9, weeks: 1, remainingDays: 2});
assert.deepEqual(calc.dateRange('2026-09-01', '2026-09-10', true), {days: 10, weeks: 1, remainingDays: 3});
assert.equal(calc.dateRange('2026-09-10', '2026-09-10').days, 0);
assert.equal(calc.dateRange('2026-09-10', '2026-09-10', true).days, 1);
assert.equal(calc.dateRange('2024-02-28', '2024-03-01').days, 2);
assert.equal(calc.dateRange('2025-02-28', '2025-03-01').days, 1);
assert.equal(calc.dateRange('2026-03-07', '2026-03-09').days, 2);
assert.equal(calc.dateRange('2026-12-31', '2027-01-01').days, 1);
assert.equal(calc.dateRange('0001-01-01', '9999-12-31').days, 3652058);
assert.throws(() => calc.dateRange('2026-09-10', '2026-09-01'), /end_before_start/);
assert.throws(() => calc.dateRange('2026-02-30', '2026-03-01'), /invalid_date/);
console.log('Date range contracts passed');

assert.equal(calc.dateShift('2026-09-10', 'add', 30, 'day').date, '2026-10-10');
assert.equal(calc.dateShift('2026-09-10', 'subtract', 2, 'week').date, '2026-08-27');
assert.equal(calc.dateShift('2025-01-31', 'add', 1, 'month').date, '2025-02-28');
assert.equal(calc.dateShift('2024-01-31', 'add', 1, 'month').date, '2024-02-29');
assert.equal(calc.dateShift('2024-02-29', 'add', 1, 'year').date, '2025-02-28');
assert.equal(calc.dateShift('2025-02-28', 'subtract', 1, 'year').date, '2024-02-28');
assert.equal(calc.dateShift('2026-09-10', 'add', 0, 'day').date, '2026-09-10');
assert.throws(() => calc.dateShift('2026-09-10', 'multiply', 1, 'day'), /invalid_operation/);
assert.throws(() => calc.dateShift('2026-09-10', 'add', -1, 'day'), /invalid_amount/);
assert.throws(() => calc.dateShift('2026-09-10', 'add', 1.5, 'day'), /invalid_amount/);
assert.throws(() => calc.dateShift('2026-09-10', 'add', null, 'day'), /invalid_amount/);
assert.throws(() => calc.dateShift('2026-09-10', 'add', false, 'day'), /invalid_amount/);
assert.throws(() => calc.dateShift('2026-09-10', 'add', 1e308, 'day'), /invalid_amount/);
assert.throws(() => calc.dateShift('2026-09-10', 'add', Number.MAX_SAFE_INTEGER, 'day'), /date_range/);
assert.throws(() => calc.dateShift('0001-01-01', 'subtract', 1, 'day'), /date_range/);
assert.throws(() => calc.dateShift('9999-12-31', 'add', 1, 'day'), /date_range/);
assert.throws(() => calc.dateShift('9999-12-31', 'add', 1, 'month'), /date_range/);
assert.throws(() => calc.dateShift('9999-12-31', 'add', 1, 'year'), /date_range/);
console.log('Date shift contracts passed');

// Independent datetime.isocalendar expectations captured during B3 Phase 1.
const calendarCases = [
  {
    "date": "0001-01-01",
    "weekday": 1,
    "iso_year": 1,
    "iso_week": 1,
    "day_of_year": 1,
    "elapsed_days": 0,
    "year_days": 365,
    "progress_percent": "0.00"
  },
  {
    "date": "0099-12-31",
    "weekday": 4,
    "iso_year": 99,
    "iso_week": 53,
    "day_of_year": 365,
    "elapsed_days": 364,
    "year_days": 365,
    "progress_percent": "99.73"
  },
  {
    "date": "0100-01-01",
    "weekday": 5,
    "iso_year": 99,
    "iso_week": 53,
    "day_of_year": 1,
    "elapsed_days": 0,
    "year_days": 365,
    "progress_percent": "0.00"
  },
  {
    "date": "1900-02-28",
    "weekday": 3,
    "iso_year": 1900,
    "iso_week": 9,
    "day_of_year": 59,
    "elapsed_days": 58,
    "year_days": 365,
    "progress_percent": "15.89"
  },
  {
    "date": "1900-03-01",
    "weekday": 4,
    "iso_year": 1900,
    "iso_week": 9,
    "day_of_year": 60,
    "elapsed_days": 59,
    "year_days": 365,
    "progress_percent": "16.16"
  },
  {
    "date": "2000-02-29",
    "weekday": 2,
    "iso_year": 2000,
    "iso_week": 9,
    "day_of_year": 60,
    "elapsed_days": 59,
    "year_days": 366,
    "progress_percent": "16.12"
  },
  {
    "date": "2015-12-31",
    "weekday": 4,
    "iso_year": 2015,
    "iso_week": 53,
    "day_of_year": 365,
    "elapsed_days": 364,
    "year_days": 365,
    "progress_percent": "99.73"
  },
  {
    "date": "2016-01-01",
    "weekday": 5,
    "iso_year": 2015,
    "iso_week": 53,
    "day_of_year": 1,
    "elapsed_days": 0,
    "year_days": 366,
    "progress_percent": "0.00"
  },
  {
    "date": "2016-01-04",
    "weekday": 1,
    "iso_year": 2016,
    "iso_week": 1,
    "day_of_year": 4,
    "elapsed_days": 3,
    "year_days": 366,
    "progress_percent": "0.82"
  },
  {
    "date": "2020-12-31",
    "weekday": 4,
    "iso_year": 2020,
    "iso_week": 53,
    "day_of_year": 366,
    "elapsed_days": 365,
    "year_days": 366,
    "progress_percent": "99.73"
  },
  {
    "date": "2021-01-01",
    "weekday": 5,
    "iso_year": 2020,
    "iso_week": 53,
    "day_of_year": 1,
    "elapsed_days": 0,
    "year_days": 365,
    "progress_percent": "0.00"
  },
  {
    "date": "2021-01-04",
    "weekday": 1,
    "iso_year": 2021,
    "iso_week": 1,
    "day_of_year": 4,
    "elapsed_days": 3,
    "year_days": 365,
    "progress_percent": "0.82"
  },
  {
    "date": "2024-01-01",
    "weekday": 1,
    "iso_year": 2024,
    "iso_week": 1,
    "day_of_year": 1,
    "elapsed_days": 0,
    "year_days": 366,
    "progress_percent": "0.00"
  },
  {
    "date": "2024-02-29",
    "weekday": 4,
    "iso_year": 2024,
    "iso_week": 9,
    "day_of_year": 60,
    "elapsed_days": 59,
    "year_days": 366,
    "progress_percent": "16.12"
  },
  {
    "date": "2024-12-30",
    "weekday": 1,
    "iso_year": 2025,
    "iso_week": 1,
    "day_of_year": 365,
    "elapsed_days": 364,
    "year_days": 366,
    "progress_percent": "99.45"
  },
  {
    "date": "2024-12-31",
    "weekday": 2,
    "iso_year": 2025,
    "iso_week": 1,
    "day_of_year": 366,
    "elapsed_days": 365,
    "year_days": 366,
    "progress_percent": "99.73"
  },
  {
    "date": "2025-01-01",
    "weekday": 3,
    "iso_year": 2025,
    "iso_week": 1,
    "day_of_year": 1,
    "elapsed_days": 0,
    "year_days": 365,
    "progress_percent": "0.00"
  },
  {
    "date": "2025-12-31",
    "weekday": 3,
    "iso_year": 2026,
    "iso_week": 1,
    "day_of_year": 365,
    "elapsed_days": 364,
    "year_days": 365,
    "progress_percent": "99.73"
  },
  {
    "date": "9999-12-31",
    "weekday": 5,
    "iso_year": 9999,
    "iso_week": 52,
    "day_of_year": 365,
    "elapsed_days": 364,
    "year_days": 365,
    "progress_percent": "99.73"
  }
];
for (const example of calendarCases) {
    const actual = calc.calendarInfo(example.date);
    assert.deepEqual(actual, {
        isoYear: example.iso_year, isoWeek: example.iso_week,
        elapsedDays: example.elapsed_days, yearDays: example.year_days,
        yearProgress: example.elapsed_days / example.year_days
    }, example.date);
    assert.equal((actual.yearProgress * 100).toFixed(2), example.progress_percent);
}
for (const invalid of ['0000-01-01', '10000-01-01', '1900-02-29', '2025-02-29', '', null]) {
    assert.throws(() => calc.calendarInfo(invalid), /invalid_date/);
}
// Every public year: Jan 4 is always ISO week 1, and Dec 28 always its final ISO week.
for (let year = 1; year <= 9999; year += 1) {
    const prefix = String(year).padStart(4, '0');
    const jan4 = calc.calendarInfo(`${prefix}-01-04`);
    assert.equal(jan4.isoYear, year);
    assert.equal(jan4.isoWeek, 1);
    assert.equal(jan4.elapsedDays, 3);
    const dec28 = calc.calendarInfo(`${prefix}-12-28`);
    assert.equal(dec28.isoYear, year);
    assert.ok([52, 53].includes(dec28.isoWeek));
    assert.equal(calc.calendarInfo(`${prefix}-01-01`).yearProgress, 0);
    const last = calc.calendarInfo(`${prefix}-12-31`);
    assert.equal(last.elapsedDays, last.yearDays - 1);
    assert.ok(last.yearProgress < 1);
}
assert.deepEqual(calc.dateShift('2024-12-30', 'add', 1, 'day'), {date: '2024-12-31', days: 1});
console.log('Calendar info contracts passed: 19 independent fixtures and every public year');
