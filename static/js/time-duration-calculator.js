(function () {
    'use strict';
    var form = document.getElementById('time-duration-form');
    if (!form || !window.TimeCalculations) return;
    var start = document.getElementById('start-time');
    var end = document.getElementById('end-time');
    var nextDay = document.getElementById('next-day');
    var rest = document.getElementById('break-minutes');
    var error = document.getElementById('time-error');
    var result = document.getElementById('time-result');
    var values = document.getElementById('time-result-values');
    var fields = { start: start, end: end, nextDay: nextDay, breakMinutes: rest };
    var calculatedInput = null;
    function currentInput() { return [start.value, end.value, nextDay.checked, rest.value].join('|'); }
    var messages = {
        invalid_time: '시작 시각과 종료 시각을 00:00~23:59 범위의 시·분으로 입력해 주세요.',
        invalid_day: '종료일 선택을 확인해 주세요.',
        invalid_break: '휴게시간을 0~1440 사이 정수 분으로 입력해 주세요. 빈값·음수·소수·지수 표기는 사용할 수 없습니다.',
        end_before_start: '같은 날의 종료 시각이 시작보다 이릅니다. 자정을 넘는 구간이면 다음 날을 선택해 주세요.',
        duration_too_long: '전체 시간은 최대 24시간입니다. 종료 시각과 다음 날 선택을 확인해 주세요.',
        break_exceeds_duration: '휴게시간이 전체 시간보다 깁니다. 휴게시간을 확인해 주세요.'
    };
    function clearState() {
        calculatedInput = null;
        error.textContent = '';
        result.hidden = true;
        values.replaceChildren();
        Object.keys(fields).forEach(function (key) { fields[key].removeAttribute('aria-invalid'); });
    }
    function duration(minutes) { return Math.floor(minutes / 60) + '시간 ' + (minutes % 60) + '분 (' + minutes + '분)'; }
    function row(label, value) {
        var wrapper = document.createElement('div');
        wrapper.className = 'global-result-row';
        var term = document.createElement('dt');
        term.textContent = label;
        var description = document.createElement('dd');
        description.textContent = value;
        wrapper.append(term, description);
        values.appendChild(wrapper);
    }
    function focusInView(element) {
        // Native focus scrolling can place a field behind the fixed header.
        element.focus({ preventScroll: true });
        element.scrollIntoView({ block: 'center', inline: 'nearest', behavior: 'instant' });
    }
    function calculate() {
        clearState();
        var calculation = window.TimeCalculations.calculateDuration({ start: start.value, end: end.value, nextDay: nextDay.checked, breakMinutes: rest.value });
        if (!calculation.ok) {
            error.textContent = messages[calculation.code];
            fields[calculation.field].setAttribute('aria-invalid', 'true');
            focusInView(fields[calculation.field]);
            return;
        }
        row('순시간', duration(calculation.netMinutes));
        row('전체 시간', duration(calculation.grossMinutes));
        row('휴게시간', duration(calculation.breakMinutes));
        row('순 소수시간', calculation.decimalHours + '시간');
        calculatedInput = currentInput();
        result.hidden = false;
        focusInView(document.getElementById('time-result-title'));
    }
    function reset() {
        form.reset();
        start.value = '';
        end.value = '';
        nextDay.checked = false;
        rest.value = '0';
        clearState();
        focusInView(start);
    }
    form.addEventListener('submit', function (event) { event.preventDefault(); });
    form.addEventListener('keydown', function (event) {
        if (event.key === 'Enter' && event.target.tagName === 'INPUT') { event.preventDefault(); calculate(); }
    });
    function inputChanged() {
        if (calculatedInput !== null && calculatedInput === currentInput()) return;
        clearState();
    }
    form.addEventListener('input', inputChanged);
    form.addEventListener('change', inputChanged);
    document.getElementById('calculate-time').addEventListener('click', calculate);
    document.getElementById('reset-time').addEventListener('click', reset);
    document.getElementById('time-inputs').disabled = false;
    document.getElementById('time-unavailable').hidden = true;
    start.value = '';
    end.value = '';
    nextDay.checked = false;
    rest.value = '0';
    clearState();
    window.addEventListener('pageshow', function (event) { if (event.persisted) reset(); });
}());
