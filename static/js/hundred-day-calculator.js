class HundredDayCalculator {
    constructor() {
        this.form = document.getElementById('hundred-day-form');
        this.dateInput = document.getElementById('hundred-day-date');
        this.error = document.getElementById('hundred-day-error');
        this.result = document.getElementById('hundred-day-result');
        this.resultContent = document.getElementById('hundred-day-result-content');
        if (!this.form) return;
        this.bindEvents();
    }

    bindEvents() {
        this.form.addEventListener('submit', (event) => {
            if (!this.parseStartDate()) {
                event.preventDefault();
                this.error.textContent = '입력한 날짜를 다시 확인해 주세요. 존재하는 날짜만 계산할 수 있습니다.';
            }
        });
        this.dateInput.addEventListener('input', () => {
            this.dateInput.value = AgeCalcDateRules.formatDateDigits(this.dateInput.value);
            this.error.textContent = '';
        });
    }

    parseStartDate() {
        try {
            return AgeCalcDateRules.parseDateDigits(this.dateInput.value);
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

}

document.addEventListener('DOMContentLoaded', () => new HundredDayCalculator());
