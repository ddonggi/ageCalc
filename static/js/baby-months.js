class BabyMonthsCalculator {
    constructor() {
        this.yearInput = document.getElementById('baby-year');
        this.monthInput = document.getElementById('baby-month');
        this.dayInput = document.getElementById('baby-day');
        this.errorEl = document.getElementById('baby-error');
        this.resultContainer = document.getElementById('baby-result-container');
        this.resultContent = document.getElementById('baby-result-content');

        if (this.yearInput && this.monthInput && this.dayInput) {
            this.bindEvents();
            this.updateResult();
        }
    }

    bindEvents() {
        ['input', 'change'].forEach(evt => {
            this.yearInput.addEventListener(evt, () => {
                this.normalizeInputs();
                this.updateResult();
            });
            this.monthInput.addEventListener(evt, () => {
                this.normalizeInputs();
                this.updateResult();
            });
            this.dayInput.addEventListener(evt, () => {
                this.normalizeInputs();
                this.updateResult();
            });
        });
    }

    normalizeInputs() {
        this.limitDigits(this.yearInput, 4);
        this.limitDigits(this.monthInput, 2);
        this.limitDigits(this.dayInput, 2);
    }

    limitDigits(input, maxLength) {
        if (!input) return;
        const digits = String(input.value || '').replace(/\D/g, '').slice(0, maxLength);
        if (input.value !== digits) {
            input.value = digits;
        }
    }

    validate() {
        const yearText = String(this.yearInput.value || '');
        const monthText = String(this.monthInput.value || '');
        const dayText = String(this.dayInput.value || '');
        const y = Number(yearText || 0);
        const m = Number(monthText || 0);
        const d = Number(dayText || 0);

        if (!y || !m || !d) {
            return { valid: false, msg: '출생일을 모두 입력해 주세요.' };
        }
        if (yearText.length !== 4) {
            return { valid: false, msg: '연도는 4자리로 입력해 주세요.' };
        }
        if (monthText.length !== 2) {
            return { valid: false, msg: '월은 2자리로 입력해 주세요.' };
        }
        if (dayText.length !== 2) {
            return { valid: false, msg: '일은 2자리로 입력해 주세요.' };
        }
        if (m < 1 || m > 12) {
            return { valid: false, msg: '월은 1~12 사이로 입력해 주세요.' };
        }
        if (d < 1 || d > 31) {
            return { valid: false, msg: '일은 1~31 사이로 입력해 주세요.' };
        }
        const birth = new Date(y, m - 1, d);
        if (
            Number.isNaN(birth.getTime()) ||
            birth.getFullYear() !== y ||
            birth.getMonth() !== m - 1 ||
            birth.getDate() !== d
        ) {
            return { valid: false, msg: '올바른 날짜를 입력해 주세요.' };
        }
        return { valid: true, birth };
    }

    getToday() {
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }

    calculateMonths(birth) {
        const today = this.getToday();
        let months = (today.getFullYear() - birth.getFullYear()) * 12;
        months += today.getMonth() - birth.getMonth();
        if (today.getDate() < birth.getDate()) {
            months -= 1;
        }
        return Math.max(0, months);
    }

    calculateTotalDays(birth) {
        const today = this.getToday();
        const diffMs = today.getTime() - birth.getTime();
        return Math.max(0, Math.floor(diffMs / 86400000));
    }

    updateResult() {
        const v = this.validate();
        if (!v.valid) {
            this.showError(v.msg);
            this.clearResult();
            return;
        }

        this.showError('');
        const months = this.calculateMonths(v.birth);
        const totalDays = this.calculateTotalDays(v.birth);
        const years = Math.floor(months / 12);
        const remain = months % 12;

        this.resultContent.innerHTML = `
            <div class="result success">
                <p class="message">현재 개월 수</p>
                <div class="age-info">
                    <p class="age"><span class="age-number">${months}개월</span> <span class="small">(${totalDays}일)</span></p>
                </div>
                <p class="small">${years}년 ${remain}개월</p>
                <div class="result-section">
                    <h4>결과 해석</h4>
                    <p>출생일에서 오늘까지 완료된 달 수를 계산한 값입니다.</p>
                    <p class="small">날짜 계산 결과이며 발달 평가나 의료 진단이 아닙니다.</p>
                </div>
            </div>
        `;
        this.resultContainer.classList.add('show');
    }

    showError(msg) {
        if (!this.errorEl) return;
        this.errorEl.textContent = msg || '';
    }

    clearResult() {
        if (this.resultContent) this.resultContent.innerHTML = '';
        if (this.resultContainer) this.resultContainer.classList.remove('show');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new BabyMonthsCalculator();
});
