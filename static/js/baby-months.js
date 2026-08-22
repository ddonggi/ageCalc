class BabyMonthsCalculator {
    constructor() {
        this.birthInput = document.getElementById('baby-birth-input');
        this.errorEl = document.getElementById('baby-error');
        this.resultContainer = document.getElementById('baby-result-container');
        this.resultContent = document.getElementById('baby-result-content');

        if (this.birthInput) {
            this.bindEvents();
        }
    }

    bindEvents() {
        ['input', 'change'].forEach(evt => {
            this.birthInput.addEventListener(evt, () => {
                this.normalizeInputs();
                this.updateResult();
            });
        });
    }

    normalizeInputs() {
        this.birthInput.value = AgeCalcDateRules.formatDateDigits(this.birthInput.value);
    }

    limitDigits(input, maxLength) {
        if (!input) return;
        const digits = String(input.value || '').replace(/\D/g, '').slice(0, maxLength);
        if (input.value !== digits) {
            input.value = digits;
        }
    }

    validate() {
        const digits = String(this.birthInput.value || '').replace(/\D/g, '');

        if (digits.length !== 8) {
            return { valid: false, msg: '출생일 8자리(YYYYMMDD)를 입력해 주세요.' };
        }
        try {
            const parsed = AgeCalcDateRules.parseBirthDateDigits(digits);
            const birth = new Date(parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate());
            return { valid: true, birth };
        } catch (error) {
            const message = String(error && error.message || '');
            return {
                valid: false,
                msg: message.includes('future') ? '미래 날짜는 입력할 수 없습니다.' : '올바른 날짜를 입력해 주세요.'
            };
        }
    }

    getToday() {
        const now = new Date();
        return new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }

    calculateMonths(birth) {
        const today = this.getToday();
        const birthIso = `${birth.getFullYear()}-${String(birth.getMonth() + 1).padStart(2, '0')}-${String(birth.getDate()).padStart(2, '0')}`;
        const todayIso = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
        return AgeCalcDateRules.calculateCompletedMonths(birthIso, todayIso);
    }

    calculateTotalDays(birth) {
        const today = this.getToday();
        const diffMs = today.getTime() - birth.getTime();
        return Math.max(0, Math.floor(diffMs / 86400000));
    }

    updateResult() {
        const digits = String(this.birthInput.value || '').replace(/\D/g, '');
        if (digits.length < 8) {
            this.showError('');
            this.clearResult();
            return;
        }
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
