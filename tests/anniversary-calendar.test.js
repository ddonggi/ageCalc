'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const modulePath = require.resolve('../static/js/weekly-time-calculations.js').replace('weekly-time-calculations.js', 'anniversary-calendar.js');
const exists = fs.existsSync(modulePath);
test('anniversary calendar module exists', () => assert.equal(exists, true));
const calendar = exists ? require(modulePath) : null;
const options = {kind: 'hundredth', date: '20240229', uid: '123e4567-e89b-42d3-a456-426614174000', dtstamp: '20261028T012345Z'};
const build = (overrides = {}) => calendar.buildEvent({...options, ...overrides});
if (calendar) {
  test('one all-day event has exact required fields and no sensitive metadata', () => {
    assert.equal(build(), ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//AgeCalc//Anniversary Calendar//KO', 'BEGIN:VEVENT', `UID:${options.uid}`, 'DTSTAMP:20261028T012345Z', 'DTSTART;VALUE=DATE:20240229', 'DTEND;VALUE=DATE:20240301', 'SUMMARY:100일째', 'END:VEVENT', 'END:VCALENDAR', ''].join('\r\n'));
  });
  for (const [date, end] of [['00010101','00010102'], ['00991231','01000101'], ['19000228','19000301'], ['20000228','20000229'], ['20000229','20000301'], ['20251231','20260101'], ['99991230','99991231']]) {
    test(`exclusive next date ${date}`, () => assert.ok(build({date}).includes(`DTEND;VALUE=DATE:${end}\r\n`)));
  }
  for (const date of ['', null, 20240229, '00000101', '100000101', '20230229', '19000229', '20241301', '20240431', '99991231', ' 20240229', '20240229\n', '2024-02-29']) {
    test(`reject invalid or unexportable date ${JSON.stringify(date)}`, () => assert.throws(() => build({date})));
  }
  for (const [kind, summary] of [['hundredth','100일째'], ['first-anniversary','첫돌(1주년)'], ['thousandth','1000일째'], ['birthday','다음 생일']]) {
    test(`whitelisted summary ${kind}`, () => assert.ok(build({kind}).includes(`SUMMARY:${summary}\r\n`)));
  }
  for (const kind of ['constructor', '__proto__', 'birthday\r\nURL:evil', '', null]) {
    test(`reject kind ${JSON.stringify(kind)}`, () => assert.throws(() => build({kind})));
  }
  for (const uid of ['', '20240229', '123e4567-e89b-12d3-a456-426614174000', '123e4567-e89b-42d3-7456-426614174000', `${options.uid}\r\nURL:evil`]) {
    test(`reject non-v4 UUID ${JSON.stringify(uid)}`, () => assert.throws(() => build({uid})));
  }
  for (const dtstamp of ['20260229T012345Z', '00000101T000000Z', '20261028T240000Z', '20261028T016000Z', '20261028T012360Z', '20261028T012345+0000', '20261028T012345Z\n', '', null]) {
    test(`reject invalid UTC timestamp ${JSON.stringify(dtstamp)}`, () => assert.throws(() => build({dtstamp})));
  }
  test('valid leap UTC timestamp and upper-case v4 UUID accepted', () => assert.ok(build({dtstamp:'20000229T235959Z', uid: options.uid.toUpperCase()}).includes('DTSTAMP:20000229T235959Z')));
  test('missing event rejected', () => assert.throws(() => calendar.buildEvent()));
  test('TEXT escaping protects punctuation and newlines', () => assert.equal(calendar.escapeText('가\\나;다,라\r\n마\n바\r사'), '가\\\\나\\;다\\,라\\n마\\n바\\n사'));
  test('UTF-8 folding respects 75 octets including continuation whitespace', () => {
    const line = 'SUMMARY:' + '한글😀'.repeat(40);
    const folded = calendar.foldLine(line);
    assert.equal(folded.replace(/\r\n /g, ''), line);
    for (const physical of folded.split('\r\n')) {
      assert.ok(Buffer.byteLength(physical, 'utf8') <= 75);
      assert.equal(new TextDecoder('utf-8', {fatal:true}).decode(Buffer.from(physical)), physical);
    }
    assert.ok(folded.includes('\r\n '));
  });
  test('boundary folding does not split ASCII or Unicode', () => {
    for (const line of ['a'.repeat(75), 'a'.repeat(76), 'a'.repeat(74)+'가', '😀'.repeat(70)]) {
      const folded = calendar.foldLine(line);
      assert.equal(folded.replace(/\r\n /g,''), line);
      assert.ok(folded.split('\r\n').every(part => Buffer.byteLength(part) <= 75));
    }
  });
  test('browser global runs without DOM, storage, crypto or network', () => {
    const scope = {};
    vm.runInNewContext(fs.readFileSync(modulePath, 'utf8'), scope);
    assert.equal(scope.AnniversaryCalendar.buildEvent(options), build());
  });
  test('UTF-8 no BOM, CRLF only and prohibited properties absent', () => {
    const value = build();
    assert.notEqual(value.charCodeAt(0), 0xfeff);
    assert.ok(value.endsWith('\r\n'));
    assert.ok(!value.replace(/\r\n/g,'').match(/[\r\n]/));
    assert.ok(!/(RRULE|VALARM|URL|ATTENDEE|ORGANIZER|LOCATION|DESCRIPTION|METHOD|TZID|ATTACH):/.test(value));
    assert.equal(value.match(/BEGIN:VEVENT/g).length, 1);
  });
}
