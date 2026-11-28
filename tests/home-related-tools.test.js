const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const test = require('node:test');
const vm = require('node:vm');

const script = fs.readFileSync(path.join(__dirname, '../static/js/home-age-calculator.js'), 'utf8');
const gradePath = '/school-grade-calculator';

function renderHome(today) {
    const input = new EventTarget();
    input.focus = () => { input.focused = true; };
    input.setAttribute = input.removeAttribute = () => {};
    const form = new EventTarget();
    form.getAttribute = () => today;
    const cardOrder = [];
    const gradeLink = {
        getAttribute: () => gradePath,
        closest: () => ({
            prepend: () => cardOrder.push('school-first'),
            append: () => cardOrder.push('birthday-first')
        })
    };
    const output = {};
    const elements = {
        'home-age-form': form,
        'home-birth-input': input,
        'home-birth-error': {},
        'home-age-result': output,
        'home-age-value': {},
        'home-grade-link': gradeLink
    };
    const document = new EventTarget();
    document.getElementById = id => elements[id];
    const completions = [];
    document.addEventListener('agecalc:result-completed', () => {
        completions.push([cardOrder.at(-1), gradeLink.href, output.hidden]);
    });
    vm.runInNewContext(script, {document, Event});
    document.dispatchEvent(new Event('DOMContentLoaded'));

    return {
        calculate(birth) {
            input.value = birth;
            input.dispatchEvent(new Event('input'));
            assert.equal(output.hidden, true);
            assert.equal(gradeLink.href, gradePath);
            form.dispatchEvent(new Event('submit', {cancelable: true}));
            return completions.at(-1);
        },
        input,
        completions
    };
}

test('school recommendations follow the school-year boundary and include preschool', () => {
    for (const [today, birth, order] of [
        ['2026-01-01', '20071201', 'school-first'],
        ['2026-02-28', '20071201', 'school-first'],
        ['2026-03-01', '20071201', 'birthday-first'],
        ['2026-03-01', '20080101', 'school-first'],
        ['2026-03-01', '20260228', 'school-first']
    ]) {
        assert.deepEqual(renderHome(today).calculate(birth), [order, gradePath + '?year=' + birth.slice(0, 4), false]);
    }
});

test('only supported school years are reused, and invalid edits clear the earlier result', () => {
    const home = renderHome('2026-11-22');
    assert.deepEqual(home.calculate('19260101'), ['birthday-first', gradePath + '?year=1926', false]);
    assert.deepEqual(home.calculate('19251231'), ['birthday-first', gradePath, false]);
    home.calculate('20260230');
    assert.equal(home.completions.length, 2);
    assert.equal(home.input.focused, true);
});
