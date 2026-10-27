(function () {
'use strict';
var copy = {"result_title": "주간 시간 계산 결과", "invalid_print": "확정된 주간 결과가 없습니다. 화면에서 입력을 확인하고 다시 계산하세요.", "days": ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"], "empty": "미입력(합계 제외)", "valid": "입력 완료", "same_day": "당일", "following_day": "익일", "total": "합계", "columns": ["요일", "상태", "시작", "종료", "종료일", "전체분", "휴게분", "순분", "순소수시간"], "rounding": "합계는 정수 분을 더한 뒤 60으로 나누어 소수 둘째 자리까지 표시합니다. 월 1분과 화 1분의 합은 2분, 0.03시간입니다. 각 행의 표시값 0.02시간을 더한 0.04시간으로 계산하지 않습니다. 7행의 전체 시간 상한은 10080분, 168.00시간입니다.", "result_note": "익일 구간은 시작한 요일에 전부 합산합니다. 일요일 익일은 다음 주 월요일이며 표의 첫 월요일과 겹치는 것으로 보지 않습니다. 다음 주로 넘어간 시간도 포함할 수 있습니다.", "limits": "실제 날짜·시간대·일광절약시간(DST)·공휴일은 반영하지 않습니다. 급여·법정 근로시간·야간 가산·휴게 적법성을 판단하는 계산기가 아닙니다.", "boundary_note": "일요일 입력에 다음 주 월요일로 넘어가는 시간이 포함되어 있습니다.", "errors": {"empty_week": "계산할 요일의 시작 시각과 종료 시각을 입력해 주세요.", "invalid_week": "입력 행을 확인하고 다시 계산해 주세요.", "overlap": "전체 시간 구간이 겹칩니다. 두 요일의 시작·종료 시각을 확인해 주세요.", "invalid_time": "시작·종료 시각을 00:00~23:59 범위로 입력해 주세요.", "invalid_day": "익일 선택을 확인해 주세요.", "invalid_break": "휴게를 0~1440 사이 정수 분으로 입력해 주세요. 빈값·음수·소수·지수 표기는 사용할 수 없습니다.", "end_before_start": "당일 종료 시각이 시작보다 이릅니다. 자정을 넘었다면 익일을 선택해 주세요.", "duration_too_long": "한 행의 전체 시간은 최대 24시간입니다. 종료 시각과 익일 선택을 확인해 주세요.", "break_exceeds_duration": "휴게가 전체 시간보다 깁니다. 휴게 분을 확인해 주세요."}};
var inputs = document.getElementById('weekly-inputs');
if (!inputs || !window.TimeCalculations || !window.WeeklyTimeCalculations) return;
var engine = window.WeeklyTimeCalculations;
var result = document.getElementById('weekly-result');
var error = document.getElementById('weekly-error');
var download = document.getElementById('weekly-download');
var printButton = document.getElementById('weekly-print');
var printReport = document.getElementById('weekly-print-report');
var calculatedSnapshot = null;
var fields = Array.from({length: 7}, function (_, i) {
    return {start: document.getElementById('weekly-start-' + i), end: document.getElementById('weekly-end-' + i), nextDay: document.getElementById('weekly-next-day-' + i), breakMinutes: document.getElementById('weekly-break-' + i)};
});
function rows() {
    return fields.map(function (row) { return {start: row.start.value, end: row.end.value, nextDay: row.nextDay.checked, breakMinutes: row.breakMinutes.value}; });
}
function snapshot(value) { return JSON.stringify(value); }
function node(tag, text) { var item = document.createElement(tag); if (text !== undefined) item.textContent = text; return item; }
function printInvalid() { printReport.replaceChildren(node('h2', copy.result_title), node('p', copy.invalid_print)); }
function invalidate() {
    calculatedSnapshot = null;
    result.hidden = true;
    download.disabled = true;
    printButton.disabled = true;
    error.textContent = '';
    document.getElementById('weekly-result-body').replaceChildren();
    document.getElementById('weekly-result-totals').replaceChildren();
    fields.forEach(function (row) { Object.values(row).forEach(function (input) { input.removeAttribute('aria-invalid'); }); });
    printInvalid();
}
function positionFocus(element) {
    var r = element.getBoundingClientRect();
    var top = 8;
    var bottom = window.innerHeight - 8;
    ['.site-header', '#cookie-banner'].forEach(function (selector) {
        var overlay = document.querySelector(selector);
        if (!overlay || !overlay.getClientRects().length) return;
        var css = window.getComputedStyle(overlay);
        if (css.visibility === 'hidden' || css.display === 'none' || Number(css.opacity) === 0) return;
        var bounds = overlay.getBoundingClientRect();
        if (selector === '.site-header' && bounds.bottom > 0) top = Math.max(top, bounds.bottom + 8);
        if (selector === '#cookie-banner' && bounds.top < window.innerHeight) bottom = Math.min(bottom, bounds.top - 8);
    });
    var delta = r.bottom > bottom ? r.bottom - bottom : r.top < top ? r.top - top : 0;
    if (delta) window.scrollBy({top: delta, behavior: 'instant'});
}
function focus(element) { element.focus({preventScroll: true}); element.scrollIntoView({block: 'center', inline: 'nearest', behavior: 'instant'}); positionFocus(element); }
function dayCells(day) {
    if (day.status === 'empty') return [copy.days[day.index], copy.empty, '', '', '', '', '', '', ''];
    return [copy.days[day.index], copy.valid, day.start, day.end, day.nextDay ? copy.following_day : copy.same_day, day.grossMinutes, day.breakMinutes, day.netMinutes, day.decimalHours];
}
function appendRow(parent, cells, header) {
    var tr = node('tr');
    cells.forEach(function (text, i) { var cell = node(header || i === 0 ? 'th' : 'td', String(text)); if (header || i === 0) cell.scope = header ? 'col' : 'row'; tr.appendChild(cell); });
    parent.appendChild(tr);
}
function totalCells(value) { return [copy.total, '', '', '', '', value.grossMinutes, value.breakMinutes, value.netMinutes, value.decimalHours]; }
function renderPrint(value) {
    var table = node('table'); table.className = 'weekly-table';
    var head = node('thead'); appendRow(head, copy.columns, true);
    var body = node('tbody'); value.days.forEach(function (day) { appendRow(body, dayCells(day)); });
    var foot = node('tfoot'); appendRow(foot, totalCells(value.totals));
    table.append(head, body, foot);
    printReport.replaceChildren(node('h2', copy.result_title), table, node('p', copy.rounding), node('p', copy.result_note), node('p', copy.limits));
    if (value.crossesWeekBoundary) printReport.appendChild(node('p', copy.boundary_note));
}
function calculate() {
    invalidate();
    var current = rows(); var value = engine.calculateWeek(current);
    if (!value.ok) {
        var first = null;
        error.textContent = value.errors.map(function (issue) {
            var index = Number.isInteger(issue.row) ? issue.row : null;
            var row = index !== null ? fields[index] : null;
            var field = row ? row[issue.field] || row.start : fields[0].start;
            field.setAttribute('aria-invalid', 'true');
            if (first === null) first = field;
            var prefix = index !== null ? copy.days[index] + (Number.isInteger(issue.relatedRow) ? ' · ' + copy.days[issue.relatedRow] : '') + ': ' : '';
            return prefix + (copy.errors[issue.code] || copy.errors.invalid_week);
        }).join(' ');
        focus(first || fields[0].start); return;
    }
    value.days.forEach(function (day) { appendRow(document.getElementById('weekly-result-body'), dayCells(day)); });
    appendRow(document.getElementById('weekly-result-totals'), totalCells(value.totals));
    document.getElementById('weekly-boundary').hidden = !value.crossesWeekBoundary;
    calculatedSnapshot = snapshot(current);
    result.hidden = false; download.disabled = false; printButton.disabled = false;
    renderPrint(value);
    focus(document.getElementById('weekly-result-title'));
}
function latest() {
    var current = rows();
    if (calculatedSnapshot === null || calculatedSnapshot !== snapshot(current)) { invalidate(); return null; }
    var value = engine.calculateWeek(current);
    if (!value.ok) { invalidate(); return null; }
    return {rows: current, value: value};
}
function reset(moveFocus) {
    fields.forEach(function (row) { row.start.value = ''; row.end.value = ''; row.nextDay.checked = false; row.breakMinutes.value = '0'; });
    invalidate(); if (moveFocus) focus(fields[0].start);
}
inputs.addEventListener('input', invalidate);
inputs.addEventListener('change', invalidate);
inputs.addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.isComposing && event.target.tagName === 'INPUT' && event.target.type !== 'checkbox') { event.preventDefault(); calculate(); }
});
document.getElementById('weekly-calculate').addEventListener('click', calculate);
document.getElementById('weekly-reset').addEventListener('click', function () { reset(true); });
download.addEventListener('click', function () {
    var current = latest(); if (!current) return;
    var value = engine.createCsv(current.rows); if (!value.ok) { invalidate(); return; }
    var url = URL.createObjectURL(new Blob([value.csv], {type: 'text/csv;charset=utf-8'}));
    var anchor = node('a'); anchor.href = url; anchor.download = 'agecalc-weekly-time.csv';
    document.body.appendChild(anchor); anchor.click(); anchor.remove();
    window.setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
});
printButton.addEventListener('click', function () { var current = latest(); if (!current) return; renderPrint(current.value); window.print(); });
window.addEventListener('beforeprint', function () { var current = latest(); if (current) renderPrint(current.value); else printInvalid(); });
window.addEventListener('pagehide', function () { reset(false); });
window.addEventListener('pageshow', function (event) { if (event.persisted) reset(false); });
// Keep keyboard focus clear of the fixed header and consent banner.
document.querySelector('main').addEventListener('focusin', function (event) {
    var target = event.target;
    window.requestAnimationFrame(function () { if (document.activeElement === target) positionFocus(target); });
});
reset(false);
inputs.disabled = false;
document.getElementById('weekly-unavailable').hidden = true;
}());
