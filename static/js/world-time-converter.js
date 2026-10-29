(function () {
'use strict';
var inputs = document.getElementById('world-inputs');
var copyElement = document.getElementById('world-copy');
if (!inputs || !copyElement || !window.WorldTimeCalculations) return;
var copy = JSON.parse(copyElement.textContent);
var fields = {date: document.getElementById('world-date'), time: document.getElementById('world-time'), source: document.getElementById('world-source')};
var result = document.getElementById('world-result');
var body = document.getElementById('world-result-body');
var error = document.getElementById('world-error');
function node(tag, text) { var element = document.createElement(tag); element.textContent = String(text); return element; }
function invalidate() {
    result.hidden = true; body.replaceChildren(); error.textContent = '';
    document.getElementById('world-instant').textContent = '';
    document.getElementById('world-mismatch').hidden = true;
    Object.values(fields).forEach(function (field) { field.removeAttribute('aria-invalid'); });
}
function positionFocus(element) {
    var rect = element.getBoundingClientRect();
    var header = document.querySelector('.site-header');
    var top = header && header.getClientRects().length ? Math.max(8, header.getBoundingClientRect().bottom + 8) : 8;
    var bottom = window.innerHeight - 8;
    var delta = rect.bottom > bottom ? rect.bottom - bottom : rect.top < top ? rect.top - top : 0;
    if (delta) window.scrollBy({top: delta, behavior: 'instant'});
}
function focus(element) { element.focus({preventScroll: true}); element.scrollIntoView({block: 'center', inline: 'nearest', behavior: 'instant'}); positionFocus(element); }
function offset(minutes) { return 'UTC' + (minutes < 0 ? '−' : '+') + String(Math.floor(Math.abs(minutes) / 60)).padStart(2, '0') + ':' + String(Math.abs(minutes) % 60).padStart(2, '0'); }
function calculate() {
    invalidate();
    var value = window.WorldTimeCalculations.calculate({date: fields.date.value, time: fields.time.value, sourceOffsetMinutes: Number(fields.source.value)});
    if (!value.ok) {
        var code = value.code;
        error.textContent = copy.errors[code] || copy.errors.unsupported_intl;
        var field = code === 'invalid_date' ? fields.date : code === 'invalid_time' ? fields.time : code === 'invalid_source' ? fields.source : null;
        if (field) field.setAttribute('aria-invalid', 'true');
        focus(field || error); return;
    }
    value.rows.forEach(function (row) {
        var tr = document.createElement('tr'); var th = node('th', copy.zones[row.zone] || row.zone); th.scope = 'row'; th.appendChild(node('small', row.zone)); tr.appendChild(th);
        if (row.status !== 'ok') { var missing = node('td', copy.unsupported); missing.colSpan = 5; tr.appendChild(missing); }
        else {
            [row.date, copy.weekdays[row.weekday], row.time, offset(row.offsetMinutes), row.dayDelta < 0 ? copy.previous : row.dayDelta > 0 ? copy.next : copy.same].forEach(function (text) { tr.appendChild(node('td', text)); });
        }
        body.appendChild(tr);
    });
    document.getElementById('world-instant').textContent = copy.instant + ' ' + value.instant + ' · ' + copy.source + ' ' + offset(value.sourceOffsetMinutes);
    document.getElementById('world-mismatch').hidden = !value.seoulMismatch;
    result.hidden = false; focus(document.getElementById('world-result-title'));
}
function reset(moveFocus) { fields.date.value = ''; fields.time.value = ''; fields.source.value = '540'; invalidate(); if (moveFocus) focus(fields.date); }
inputs.addEventListener('input', invalidate);
inputs.addEventListener('change', invalidate);
inputs.addEventListener('keydown', function (event) { if (event.key === 'Enter' && !event.isComposing && event.target.tagName === 'INPUT') { event.preventDefault(); calculate(); } });
document.getElementById('world-calculate').addEventListener('click', calculate);
document.getElementById('world-reset').addEventListener('click', function () { reset(true); });
window.addEventListener('pagehide', function () { reset(false); });
window.addEventListener('pageshow', function (event) { if (event.persisted) reset(false); });
document.querySelector('main').addEventListener('focusin', function (event) { var target = event.target; window.requestAnimationFrame(function () { if (document.activeElement === target) positionFocus(target); }); });
reset(false); inputs.disabled = false; document.getElementById('world-unavailable').hidden = true;
}());
