/* Server-rendered localized forms; only private result values are updated here. */
(function () {
    'use strict';
    const form = document.getElementById('global-calculator');
    const configElement = document.getElementById('calculator-config');
    if (!form || !configElement || !window.AgeCalcGlobalRules) return;
    const config = JSON.parse(configElement.textContent);
    const ui = config.ui;
    const rules = window.AgeCalcGlobalRules;
    const numbers = new Intl.NumberFormat(config.locale);
    const plurals = new Intl.PluralRules(config.locale);
    const dates = new Intl.DateTimeFormat(config.locale, {year: 'numeric', month: 'long', day: 'numeric', calendar: 'gregory', timeZone: 'UTC'});
    const datesWithWeekday = new Intl.DateTimeFormat(config.locale, {year: 'numeric', month: 'long', day: 'numeric', weekday: 'long', calendar: 'gregory', timeZone: 'UTC'});
    const errorElement = document.getElementById('calculator-error');
    const result = document.getElementById('global-result');
    const values = document.getElementById('result-values');
    const note = document.getElementById('result-note');

    function unit(n, kind) {
        const messages = kind === 'week' ? ui.unit_week : ui.units[kind];
        return (messages[plurals.select(n)] || messages.other).replace('{n}', numbers.format(n));
    }

    function formatDate(value) {
        return dates.format(new Date(`${value}T00:00:00Z`));
    }

    function formatDateWithWeekday(value) {
        return datesWithWeekday.format(new Date(`${value}T00:00:00Z`));
    }

    function readDate(name, withYear = true) {
        const group = form.querySelector(`[data-date="${name}"]`);
        const get = part => group.querySelector(`[data-part="${part}"]`).value.trim();
        const parts = {year: withYear ? get('year') : '2000', month: get('month'), day: get('day')};
        if (!parts.year || !parts.month || !parts.day) throw new Error('required');
        return {iso: rules.isoParts(parts.year, parts.month, parts.day), ...parts};
    }

    function row(label, value) {
        const wrapper = document.createElement('div');
        wrapper.className = 'global-result-row';
        wrapper.dataset.resultKey = label;
        const term = document.createElement('dt');
        const detail = document.createElement('dd');
        term.textContent = ui[label];
        detail.textContent = value;
        wrapper.append(term, detail);
        values.append(wrapper);
    }

    function daysStatus(days) {
        row(days < 0 ? 'days_elapsed' : 'days_remaining', unit(Math.abs(days), 'day'));
        if (days === 0) note.textContent = ui.same_day;
    }

    function syncReference() {
        const wrapper = document.getElementById('reference-fields');
        if (!wrapper) return;
        const specific = form.querySelector('[name="reference_mode"]:checked').value === 'specific';
        wrapper.hidden = !specific;
        wrapper.querySelector('fieldset').disabled = !specific;
    }

    form.addEventListener('change', () => {
        syncReference();
        errorElement.textContent = '';
        result.hidden = true;
    });
    form.addEventListener('input', () => {
        errorElement.textContent = '';
        result.hidden = true;
    });
    form.addEventListener('reset', () => {
        errorElement.textContent = '';
        result.hidden = true;
        values.replaceChildren();
        window.setTimeout(syncReference, 0);
    });
    document.getElementById('swap-dates')?.addEventListener('click', () => {
        for (const part of ['year', 'month', 'day']) {
            const start = document.getElementById(`start-${part}`);
            const end = document.getElementById(`end-${part}`);
            [start.value, end.value] = [end.value, start.value];
        }
        errorElement.textContent = '';
        result.hidden = true;
    });
    form.addEventListener('submit', event => {
        event.preventDefault();
        values.replaceChildren();
        note.textContent = '';
        result.hidden = true;
        errorElement.textContent = '';
        document.getElementById('result-event').textContent = '';
        document.getElementById('result-title').textContent = ui.result;
        try {
            const today = rules.today();
            let reference = today;
            if (config.kind === 'date_add_subtract') {
                const start = readDate('start').iso;
                const operation = form.querySelector('[name="operation"]:checked')?.value;
                const amountValue = document.getElementById('shift-amount').value.trim();
                if (!amountValue) throw new Error('required');
                const amount = Number(amountValue);
                const selectedUnit = document.getElementById('shift-unit').value;
                const answer = rules.dateShift(start, operation, amount, selectedUnit);
                row('result_date', formatDateWithWeekday(answer.date));
                row('start_date', formatDate(start));
                row('calendar_days_moved', unit(Math.abs(answer.days), 'day'));
                note.textContent = ['month', 'year'].includes(selectedUnit) ? ui.month_end_note : ui.fixed_days_note;
            } else if (config.kind === 'days_between_dates') {
                const start = readDate('start').iso;
                const end = readDate('end').iso;
                const inclusive = document.getElementById('include-end').checked;
                const answer = rules.dateRange(start, end, inclusive);
                row('range_days', unit(answer.days, 'day'));
                row('range_weeks', [unit(answer.weeks, 'week'), unit(answer.remainingDays, 'day')].join(ui.duration_separator));
                row('start_date', formatDate(start));
                row('end_date', formatDate(end));
                note.textContent = inclusive ? ui.inclusive_note : ui.exclusive_note;
            } else if (config.kind === 'age') {
                const birth = readDate('birth').iso;
                if (birth > today) throw new Error('future_birth');
                if (form.querySelector('[name="reference_mode"]:checked').value === 'specific') reference = readDate('reference').iso;
                const answer = rules.age(birth, reference);
                row('current_age', unit(answer.years, 'year'));
                row('exact_age', [unit(answer.years, 'year'), unit(answer.months, 'month'), unit(answer.days, 'day')].join(ui.duration_separator));
                row('total_months', unit(answer.totalMonths, 'month'));
                row('total_days', unit(answer.totalDays, 'day'));
                if (answer.next) {
                    row('next_birthday', formatDate(answer.next.nextDate));
                    row('days_until', unit(answer.next.days, 'day'));
                    if (answer.next.days === 0) note.textContent = ui.birthday_today;
                } else note.textContent = ui.date_range;
            } else if (config.kind === 'baby_months') {
                const birth = readDate('birth').iso;
                if (birth > today) throw new Error('future_birth');
                const answer = rules.baby(birth, today);
                row('total_months', unit(answer.months, 'month'));
                row('years_months', [unit(answer.years, 'year'), unit(answer.remainingMonths, 'month')].join(ui.duration_separator));
                row('total_days', unit(answer.days, 'day'));
            } else if (config.kind === 'birthday_dday_calculator') {
                const birth = readDate('birthday', false);
                const answer = rules.birthday(birth.month, birth.day, today);
                row('next_birthday', formatDate(answer.nextDate));
                row('days_until', unit(answer.days, 'day'));
                if (answer.days === 0) note.textContent = ui.birthday_today;
            } else if (config.kind === 'hundred_day_calculator') {
                const answer = rules.hundred(readDate('start').iso, today);
                row('hundredth_date', formatDate(answer.date));
                daysStatus(answer.days);
            } else if (config.kind === 'd_day') {
                document.getElementById('result-title').textContent = ui[form.querySelector('[name="mode"]:checked').value];
                const target = readDate('target').iso;
                row('target_date', formatDate(target));
                daysStatus(rules.daysBetween(today, target));
                document.getElementById('result-event').textContent = document.getElementById('event-label').value.trim();
            } else if (config.kind === 'age_gap_calculator') {
                row('year_gap', unit(rules.yearGap(document.getElementById('year_a').value, document.getElementById('year_b').value, today), 'year'));
            }
            if (!['days_between_dates', 'date_add_subtract'].includes(config.kind)) row('reference_label', formatDate(reference));
            result.hidden = false;
            result.focus({preventScroll: true});
            result.scrollIntoView({behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth', block: 'nearest'});
        } catch (error) {
            errorElement.textContent = ui[error.message] || ui.invalid_date;
        }
    });

    const currentYear = Number(rules.today().slice(0, 4));
    form.querySelectorAll('[data-birth-year]').forEach(select => {
        for (let year = currentYear; year >= Math.max(1900, currentYear - 100); year -= 1) {
            const option = document.createElement('option');
            option.value = String(year);
            option.textContent = String(year);
            select.append(option);
        }
    });
    document.getElementById('calculator-inputs').disabled = false;
    document.getElementById('calculator-unavailable').hidden = true;
    syncReference();
}());
