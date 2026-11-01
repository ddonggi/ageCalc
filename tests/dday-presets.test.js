'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const script = fs.readFileSync(require.resolve('../static/js/d-day.js'), 'utf8');
const rules = require('../static/js/date-rules.js');

function element(value = '') {
    const listeners = {};
    const classes = new Set(['show']);
    return {value, textContent: '', innerHTML: 'old result', disabled: true, checked: false,
        dataset: {}, attributes: {}, listeners,
        classList: {add: x => classes.add(x), remove: x => classes.delete(x), contains: x => classes.has(x)},
        addEventListener(type, fn) {(listeners[type] ||= []).push(fn);},
        setAttribute(k, v) {this.attributes[k] = v;},
        removeAttribute(k) {delete this.attributes[k];},
        focus() {this.focused = true;}, scrollIntoView() {},
        emit(type) {const event = {preventDefault() {this.prevented = true;}}; for (const fn of listeners[type] || []) fn(event); return event;}
    };
}
const presets = [2027, 2028].map((year, i) => ({id: `csat-academic-${year}`, label: `${year} test`, date_digits: i ? '20271118' : '20261119', can_fill: true}));
// Literal projection captured from build_exam_presets(date(2026, 10, 31)); no Flask/DB import.
const serverFixture = [
  {
    "id": "csat-academic-2027",
    "academic_year": 2027,
    "execution_year": 2026,
    "exam_date": "2026-11-19",
    "label": "2027학년도 수능 (2026년 시행)",
    "source_url": "https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=100526&lev=0&m=020402&s=moe",
    "source_title": "2027학년도 대학수학능력시험은 2026년 11월 19일(목)에 시행됩니다",
    "published_on": "2024-08-16",
    "verified_on": "2026-10-31",
    "review_due": "2026-11-12",
    "enabled": true,
    "d100_date": "2026-08-11",
    "date_digits": "20261119",
    "state": "upcoming",
    "can_fill": true
  },
  {
    "id": "csat-academic-2028",
    "academic_year": 2028,
    "execution_year": 2027,
    "exam_date": "2027-11-18",
    "label": "2028학년도 수능 (2027년 시행)",
    "source_url": "https://www.moe.go.kr/boardCnts/viewRenew.do?boardID=294&boardSeq=103512&lev=0&m=020402&s=moe",
    "source_title": "2028학년도 대학수학능력시험은 2027년 11월 18일(목)에 시행됩니다",
    "published_on": "2025-06-01",
    "verified_on": "2026-10-31",
    "review_due": "2027-03-31",
    "enabled": true,
    "d100_date": "2027-08-10",
    "date_digits": "20271118",
    "state": "upcoming",
    "can_fill": true
  }
];
function setup(rows = presets) {
    const els = Object.fromEntries(['dday-label','dday-date','dday-form','dday-error','dday-result-container','dday-result-content','dday-exam-presets','dday-preset-status'].map(id => [id, element()]));
    els['dday-label'].value = 'restored'; els['dday-date'].value = '20240229';
    els['dday-exam-presets'].textContent = JSON.stringify(rows);
    els['dday-preset-status'].dataset.filledMessage = 'Filled; calculate to continue.';
    const modes = ['until','since'].map(value => Object.assign(element(value), {checked: value === 'since'}));
    const buttons = [...presets.map(row => row.id), 'unknown'].map(id => Object.assign(element(), {dataset: {ddayPreset: id}}));
    const document = {getElementById: id => els[id] || null, querySelectorAll: selector => selector === 'input[name="mode"]' ? modes : selector === '[data-dday-preset]' ? buttons : [], addEventListener: (type, fn) => {if (type === 'DOMContentLoaded') fn();}};
    vm.runInNewContext(script, {document, AgeCalcDateRules: rules});
    return {els, modes, buttons};
}
test('initialization preserves restored fields, results and mode; enables only known permitted presets', () => {
    const {els, modes, buttons} = setup();
    assert.equal(els['dday-label'].value, 'restored'); assert.equal(els['dday-date'].value, '20240229'); assert.equal(modes[1].checked, true);
    assert.equal(els['dday-result-content'].innerHTML, 'old result');
    assert.deepEqual(buttons.map(b => b.disabled), [false, false, true]);
});
for (const index of [0, 1]) test(`preset ${index + 1} fills fields, clears stale result and error, announces and focuses without submission`, () => {
    const {els, modes, buttons} = setup(); els['dday-error'].textContent = 'old error';
    buttons[index].emit('click');
    assert.equal(els['dday-label'].value, presets[index].label); assert.equal(els['dday-date'].value, presets[index].date_digits);
    assert.deepEqual(modes.map(m => m.checked), [true, false]);
    assert.equal(els['dday-result-content'].innerHTML, ''); assert.equal(els['dday-result-container'].classList.contains('show'), false);
    assert.equal(els['dday-error'].textContent, ''); assert.ok(els['dday-preset-status'].textContent); assert.equal(els['dday-date'].focused, true);
    assert.equal(buttons[index].attributes['aria-pressed'], 'true');
});
for (const can_fill of [false, 'true', null]) test(`strict can_fill ${JSON.stringify(can_fill)} rejects programmatic selection`, () => {
    const {els, buttons} = setup([{...presets[0], can_fill}]);
    buttons[0].emit('click'); buttons[2].emit('click');
    assert.equal(els['dday-label'].value, 'restored'); assert.equal(els['dday-result-content'].innerHTML, 'old result'); assert.equal(buttons[0].disabled, true);
});
test('manual edit clears selection mark while preserving existing manual result behavior', () => {
    const {els, buttons} = setup(); buttons[0].emit('click');
    assert.equal(buttons[0].attributes['aria-pressed'], 'true');
    els['dday-result-content'].innerHTML = 'manual existing result';
    els['dday-date'].value = '2027-11-18'; els['dday-date'].emit('input');
    assert.equal(els['dday-date'].value, '20271118'); assert.notEqual(buttons[0].attributes['aria-pressed'], 'true');
    assert.equal(els['dday-result-content'].innerHTML, 'manual existing result');
});
test('a button disabled after initialization refuses a programmatic click', () => {
    const {els, buttons} = setup();
    buttons[0].disabled = true; buttons[0].emit('click');
    assert.equal(els['dday-label'].value, 'restored');
});
test('missing or malformed preset JSON preserves normal GET form behavior', () => {
    for (const rows of [null, {}, []]) {
        const {els, buttons} = setup(rows);
        assert.equal(els['dday-label'].value, 'restored');
        assert.ok(buttons.every(button => button.disabled));
        assert.notEqual(els['dday-form'].emit('submit').prevented, true);
    }
});
test('existing valid GET submission proceeds and invalid date blocks', () => {
    const {els} = setup();
    assert.notEqual(els['dday-form'].emit('submit').prevented, true);
    els['dday-date'].value = '20230229'; assert.equal(els['dday-form'].emit('submit').prevented, true);
});
test('real server projection fills the literal eight-digit dates for both academic years', () => {
    for (const [index, expected] of [[0, '20261119'], [1, '20271118']]) {
        const {els, buttons} = setup(serverFixture);
        buttons[index].emit('click');
        assert.equal(els['dday-date'].value, expected);
        assert.notEqual(els['dday-form'].emit('submit').prevented, true);
    }
});
