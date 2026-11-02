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

// Weekday-only interval: civil-date ordinal oracle, independent of JS Date.
function ordinal(value) {
    const [year, month, day] = value.split('-').map(Number);
    const prior = year - 1;
    const leap = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    const lengths = [31, leap ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
    return prior * 365 + Math.floor(prior / 4) - Math.floor(prior / 100) + Math.floor(prior / 400)
        + lengths.slice(0, month - 1).reduce((sum, count) => sum + count, 0) + day - 1;
}
function weekdayOracle(start, end, includeEnd = false) {
    let weekdays = 0;
    let weekendDays = 0;
    for (let day = ordinal(start); day < ordinal(end) + Number(includeEnd); day += 1) {
        if (day % 7 < 5) weekdays += 1;
        else weekendDays += 1;
    }
    return {weekdays, weekendDays};
}
assert.equal(typeof calc.weekdayRange, 'function', 'weekdayRange must be exported');
const weekdayExamples = [
    ['2027-01-01', '2027-12-31', true, {weekdays: 261, weekendDays: 104}],
    ['2027-05-01', '2027-05-03', true, {weekdays: 1, weekendDays: 2}],
    ['2027-01-01', '2027-01-04', false, {weekdays: 1, weekendDays: 2}],
    ['2027-01-01', '2027-01-04', true, {weekdays: 2, weekendDays: 2}],
    ['2024-02-28', '2024-03-01', true, {weekdays: 3, weekendDays: 0}]
];
for (const [start, end, inclusive, expected] of weekdayExamples) {
    assert.deepEqual(calc.weekdayRange(start, end, inclusive), expected);
}
// Every starting weekday and every remainder, with zero and multiple full weeks.
for (let offset = 0; offset < 7; offset += 1) {
    const start = calc.dateShift('2027-01-04', 'add', offset, 'day').date;
    for (let length = 0; length <= 27; length += 1) {
        const end = calc.dateShift(start, 'add', length, 'day').date;
        for (const inclusive of [false, true]) {
            const actual = calc.weekdayRange(start, end, inclusive);
            assert.deepEqual(actual, weekdayOracle(start, end, inclusive));
            assert.equal(actual.weekdays + actual.weekendDays, calc.dateRange(start, end, inclusive).days);
        }
    }
}
for (const [start, end] of [
    ['0001-01-01', '0001-01-08'], ['0099-12-28', '0100-01-05'],
    ['1900-02-26', '1900-03-03'], ['2000-02-26', '2000-03-03'],
    ['9999-12-31', '9999-12-31'], ['0001-01-01', '9999-12-31']
]) {
    for (const inclusive of [false, true]) {
        assert.deepEqual(calc.weekdayRange(start, end, inclusive), weekdayOracle(start, end, inclusive));
    }
}
let weekdaySeed = 20261102;
function nextWeekdayRandom() {
    weekdaySeed = (Math.imul(weekdaySeed, 1664525) + 1013904223) >>> 0;
    return weekdaySeed;
}
for (let sample = 0; sample < 400; sample += 1) {
    const start = calc.dateShift('0001-01-01', 'add', nextWeekdayRandom() % 3640000, 'day').date;
    const end = calc.dateShift(start, 'add', nextWeekdayRandom() % 3660, 'day').date;
    const inclusive = Boolean(nextWeekdayRandom() % 2);
    assert.deepEqual(calc.weekdayRange(start, end, inclusive), weekdayOracle(start, end, inclusive));
}
for (const invalid of ['', null, '0000-01-01', '10000-01-01', '1900-02-29', '2027-02-30']) {
    assert.throws(() => calc.weekdayRange(invalid, '2027-03-01'), /invalid_date/);
    assert.throws(() => calc.weekdayRange('0001-01-01', invalid), /invalid_date/);
}
assert.throws(() => calc.weekdayRange('2027-01-02', '2027-01-01'), /end_before_start/);
// Existing dateRange return shape remains exact.
assert.deepEqual(calc.dateRange('2027-01-01', '2027-01-04'), {days: 3, weeks: 0, remainingDays: 3});
console.log('Weekday contracts passed: 392 weekday/remainder cases, 400 seeded intervals, extreme years and full range');

// B2: calendar facts are supplied by the separately validated server snapshot.
const reviewedHolidays = [{"date": "2027-01-01", "label": "1월 1일", "type": "national"}, {"date": "2027-02-06", "label": "설날(연휴)", "type": "national"}, {"date": "2027-02-07", "label": "설날(연휴)", "type": "national"}, {"date": "2027-02-08", "label": "설날(연휴)", "type": "national"}, {"date": "2027-02-09", "label": "대체공휴일(설날)", "type": "substitute"}, {"date": "2027-03-01", "label": "3·1절", "type": "national"}, {"date": "2027-05-01", "label": "노동절", "type": "national"}, {"date": "2027-05-03", "label": "대체공휴일(노동절)", "type": "substitute"}, {"date": "2027-05-05", "label": "어린이날", "type": "national"}, {"date": "2027-05-13", "label": "부처님 오신 날", "type": "national"}, {"date": "2027-06-06", "label": "현충일", "type": "national"}, {"date": "2027-07-17", "label": "제헌절", "type": "national"}, {"date": "2027-07-19", "label": "대체공휴일(제헌절)", "type": "substitute"}, {"date": "2027-08-15", "label": "광복절", "type": "national"}, {"date": "2027-08-16", "label": "대체공휴일(광복절)", "type": "substitute"}, {"date": "2027-09-14", "label": "추석(연휴)", "type": "national"}, {"date": "2027-09-15", "label": "추석(연휴)", "type": "national"}, {"date": "2027-09-16", "label": "추석(연휴)", "type": "national"}, {"date": "2027-10-03", "label": "개천절", "type": "national"}, {"date": "2027-10-04", "label": "대체공휴일(개천절)", "type": "substitute"}, {"date": "2027-10-09", "label": "한글날", "type": "national"}, {"date": "2027-10-11", "label": "대체공휴일(한글날)", "type": "substitute"}, {"date": "2027-12-25", "label": "기독탄신일", "type": "national"}, {"date": "2027-12-27", "label": "대체공휴일(기독탄신일)", "type": "substitute"}];
assert.deepEqual(calc.holidayRange2027('2027-01-01', '2027-12-31', true, reviewedHolidays), {
    referenceDays:246, weekendDays:104, holidayDays:15,
    excludedHolidays: reviewedHolidays.filter(h => ![0,6].includes(new Date(h.date+'T00:00:00Z').getUTCDay())).map(({date,label})=>({date,label}))
});
assert.deepEqual(calc.holidayRange2027('2027-05-01','2027-05-03',true,reviewedHolidays), {referenceDays:0,weekendDays:2,holidayDays:1,excludedHolidays:[{date:'2027-05-03',label:'대체공휴일(노동절)'}]});
for (const [day,answer] of [['2027-05-11',1],['2027-06-06',0],['2027-06-07',1]]) {
    assert.equal(calc.holidayRange2027(day,day,true,reviewedHolidays).referenceDays,answer);
    assert.equal(calc.holidayRange2027(day,day,false,reviewedHolidays).referenceDays,0);
}
assert.throws(()=>calc.holidayRange2027('2026-12-31','2027-01-01',false,reviewedHolidays), /unsupported_year/);
assert.throws(()=>calc.holidayRange2027('2027-12-31','2028-01-01',false,reviewedHolidays), /unsupported_year/);
assert.throws(()=>calc.holidayRange2027('2027-02-02','2027-01-01',false,reviewedHolidays), /end_before_start/);
assert.throws(()=>calc.holidayRange2027('2027-02-29','2027-03-01',false,reviewedHolidays), /invalid_date/);
for(const bad of [null, [], [{date:'2027-01-01',label:'x',type:'local'}], [{date:'2026-01-01',label:'x',type:'national'}], [reviewedHolidays[0],reviewedHolidays[0]], [{date:'2027-02-30',label:'x',type:'national'}], [{date:'2027-01-01',label:'',type:'national'}]]) {
    assert.throws(()=>calc.holidayRange2027('2027-01-01','2027-01-01',true,bad), /invalid_holidays/);
}
// Independent daily enumeration instead of the production week's quotient/remainder.
const holidayDateSet = new Set(reviewedHolidays.map(h=>h.date));
let randomSeed=20261102;
for(let k=0;k<300;k++) {
    randomSeed=(randomSeed*1664525+1013904223)>>>0;const a=randomSeed%365;
    randomSeed=(randomSeed*1664525+1013904223)>>>0;const b=a+randomSeed%(365-a);
    const start=new Date(Date.UTC(2027,0,1+a)).toISOString().slice(0,10), end=new Date(Date.UTC(2027,0,1+b)).toISOString().slice(0,10);
    for(const include of [false,true]) {
        let ref=0,weekend=0,holiday=0;
        for(let n=a;n<b+(include?1:0);n++) {
            const d=new Date(Date.UTC(2027,0,1+n)),iso=d.toISOString().slice(0,10);
            if([0,6].includes(d.getUTCDay())) weekend++; else if(holidayDateSet.has(iso)) holiday++; else ref++;
        }
        const result=calc.holidayRange2027(start,end,include,reviewedHolidays);
        assert.equal(result.referenceDays,ref);assert.equal(result.weekendDays,weekend);assert.equal(result.holidayDays,holiday);
        assert.equal(ref+weekend+holiday,calc.dateRange(start,end,include).days);
        assert.deepEqual(Object.keys(result).sort(),['excludedHolidays','holidayDays','referenceDays','weekendDays']);
    }
}
const immutableFacts=JSON.stringify(reviewedHolidays);
calc.holidayRange2027('2027-01-01','2027-12-31',true,reviewedHolidays);
assert.equal(JSON.stringify(reviewedHolidays),immutableFacts);
