/* Download only the server-confirmed result; never persist inputs or send requests. */
(function () {
    'use strict';
    document.addEventListener('DOMContentLoaded', function () {
        const result = document.querySelector('[data-calendar-input]');
        if (!result) return;
        const birthday = result.id === 'birthday-dday-result-content';
        const form = document.getElementById(birthday ? 'birthday-dday-form' : 'hundred-day-form');
        const input = document.getElementById(birthday ? 'birthday-dday-input' : 'hundred-day-date');
        const month = document.getElementById('birthday-dday-month');
        const day = document.getElementById('birthday-dday-day');
        const status = document.getElementById('calendar-download-status');
        const expected = result.dataset.calendarInput;
        const expectedMonth = result.dataset.calendarMonth;
        const expectedDay = result.dataset.calendarDay;
        const records = Array.from(result.querySelectorAll('[data-calendar-kind]'), button => ({
            button, kind: button.dataset.calendarKind, date: button.dataset.calendarDate, event: null
        }));
        const available = Boolean(window.AnniversaryCalendar && window.crypto && typeof window.crypto.randomUUID === 'function' && typeof Blob === 'function' && typeof URL.createObjectURL === 'function' && typeof URL.revokeObjectURL === 'function');
        let invalidated = false;
        function matches() {
            return !invalidated && input.value === expected && (!birthday || (month.value === expectedMonth && day.value === expectedDay));
        }
        function invalidate() {
            invalidated = true;
            records.forEach(record => { record.event = null; record.button.disabled = true; });
            if (status) status.textContent = '입력값이 바뀌었습니다. 다시 계산한 뒤 일정 파일을 받아 주세요.';
        }
        form.addEventListener('input', invalidate);
        form.addEventListener('change', invalidate);
        window.addEventListener('pagehide', invalidate);
        window.addEventListener('pageshow', event => { if (event.persisted) invalidate(); });
        if (!available) {
            if (status) status.textContent = '이 브라우저에서는 일정 파일을 만들 수 없습니다.';
            return;
        }
        records.forEach(record => {
            record.button.disabled = !matches();
            record.button.addEventListener('click', function () {
                if (!matches()) { invalidate(); return; }
                let blobUrl;
                let link;
                try {
                    if (!record.event) {
                        const dtstamp = new Date().toISOString().replace(/[-:]/g, '').replace(/\.\d{3}Z$/, 'Z');
                        record.event = window.AnniversaryCalendar.buildEvent({kind: record.kind, date: record.date, uid: window.crypto.randomUUID(), dtstamp});
                    }
                    blobUrl = URL.createObjectURL(new Blob([record.event], {type: 'text/calendar;charset=utf-8'}));
                    link = document.createElement('a');
                    link.href = blobUrl;
                    link.download = 'agecalc-anniversary.ics';
                    link.hidden = true;
                    document.body.appendChild(link);
                    link.click();
                } catch {
                    if (status) status.textContent = '일정 파일을 만들지 못했습니다. 다시 시도해 주세요.';
                } finally {
                    if (link) link.remove();
                    if (blobUrl) window.setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
                }
            });
        });
        if (!matches()) invalidate();
    });
}());
