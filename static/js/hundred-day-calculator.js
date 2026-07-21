class HundredDayCalculator {
    constructor() {
        this.form = document.getElementById('hundred-day-form');
        this.yearInput = document.getElementById('hundred-day-year');
        this.monthInput = document.getElementById('hundred-day-month');
        this.dayInput = document.getElementById('hundred-day-day');
        this.error = document.getElementById('hundred-day-error');
        this.result = document.getElementById('hundred-day-result');
        this.resultContent = document.getElementById('hundred-day-result-content');
        this.clearButton = document.getElementById('hundred-day-clear');
        if (!this.form) return;
        this.bindEvents();
    }

    bindEvents() {
        this.form.addEventListener('submit', (event) => {
            event.preventDefault();
            this.calculate();
        });
        this.clearButton.addEventListener('click', () => {
            [this.yearInput, this.monthInput, this.dayInput].forEach((input) => { input.value = ''; });
            this.error.textContent = '';
            this.result.hidden = true;
            this.resultContent.innerHTML = '';
            this.yearInput.focus();
        });
        [this.yearInput, this.monthInput, this.dayInput].forEach((input) => {
            input.addEventListener('input', () => {
                input.value = input.value.replace(/\D/g, '').slice(0, input.maxLength);
            });
        });
    }

    parseStartDate() {
        const year = Number(this.yearInput.value);
        const month = Number(this.monthInput.value);
        const day = Number(this.dayInput.value);
        if (!year || !month || !day) return null;
        try {
            return AgeCalcDateRules.parseIsoDate(
                `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
            );
        } catch {
            return null;
        }
    }

    addUtcDays(value, days) {
        return AgeCalcDateRules.addUtcDays(value, days);
    }

    todayUtc() {
        const today = new Date();
        return new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
    }

    format(value) {
        return `${value.getUTCFullYear()}.${String(value.getUTCMonth() + 1).padStart(2, '0')}.${String(value.getUTCDate()).padStart(2, '0')}`;
    }

    calculate() {
        const startDate = this.parseStartDate();
        if (!startDate) {
            this.error.textContent = '입력한 날짜를 다시 확인해 주세요. 존재하는 날짜만 계산할 수 있습니다.';
            this.result.hidden = true;
            return;
        }

        const hundredthDate = this.addUtcDays(startDate, 99);
        const today = this.todayUtc();
        const dayMs = 86400000;
        const remaining = Math.round((hundredthDate - today) / dayMs);
        const elapsed = Math.round((today - startDate) / dayMs) + 1;
        const statusLabel = remaining > 0 ? `D-${remaining}` : remaining < 0 ? `D+${Math.abs(remaining)}` : 'D-Day';
        const statusNote = remaining > 0
            ? `100일째까지 ${remaining}일 남았습니다.`
            : remaining < 0
                ? `100일째가 지난 지 ${Math.abs(remaining)}일 되었습니다.`
                : '바로 오늘이 100일째입니다.';
        const elapsedLabel = elapsed < 1 ? '시작일 전' : `${elapsed}일째`;

        this.error.textContent = '';
        this.resultContent.innerHTML = `
            <p class="eyebrow">선택한 시작일</p>
            <h2>${this.format(startDate)} 기준 100일 안내</h2>
            <p>시작일을 1일째로 계산해 99일을 더한 날짜를 100일째로 안내합니다.</p>
            <div class="summary-grid">
                <div class="summary-card"><strong>시작일</strong><span>${this.format(startDate)}</span></div>
                <div class="summary-card"><strong>100일째 날짜</strong><span>${this.format(hundredthDate)}</span></div>
                <div class="summary-card"><strong>오늘 기준 상태</strong><span>${statusLabel}</span></div>
                <div class="summary-card"><strong>현재 기준 경과</strong><span>${elapsedLabel}</span></div>
            </div>
            <p class="small">${statusNote}</p>`;
        this.result.hidden = false;
    }
}

document.addEventListener('DOMContentLoaded', () => new HundredDayCalculator());
