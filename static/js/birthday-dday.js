class BirthdayDDayCalculator {
    constructor() {
        this.form = document.getElementById('birthday-dday-form');
        this.input = document.getElementById('birthday-dday-input');
        this.error = document.getElementById('birthday-dday-error');
        this.result = document.getElementById('birthday-dday-result');
        this.resultContent = document.getElementById('birthday-dday-result-content');
        this.clearButton = document.getElementById('birthday-dday-clear');
        if (!this.form || !this.input) return;
        this.bindEvents();
    }

    bindEvents() {
        this.form.addEventListener('submit', (event) => event.preventDefault());
        this.input.addEventListener('input', () => {
            this.input.value = AgeCalcDateRules.formatMonthDayDigits(this.input.value);
            const digits = this.input.value.replace(/\D/g, '');
            if (digits.length < 4) {
                this.clearState();
                return;
            }
            this.calculate();
        });
        this.clearButton?.addEventListener('click', () => {
            this.input.value = '';
            this.clearState();
            this.input.focus();
            window.history.replaceState({}, document.title, window.location.pathname);
        });
    }

    clearState() {
        this.error.textContent = '';
        this.result.hidden = true;
        this.resultContent.innerHTML = '';
    }

    nextBirthday(month, day) {
        const now = new Date();
        const todayUtc = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
        let year = now.getFullYear();
        let candidate = new Date(Date.UTC(year, month - 1, day));
        while (candidate.getUTCMonth() + 1 !== month || candidate.getUTCDate() !== day || candidate.getTime() < todayUtc) {
            year += 1;
            candidate = new Date(Date.UTC(year, month - 1, day));
        }
        return { candidate, todayUtc };
    }

    calculate() {
        let parsed;
        try {
            parsed = AgeCalcDateRules.parseMonthDayDigits(this.input.value);
        } catch (error) {
            this.error.textContent = '존재하는 생일을 입력해 주세요.';
            this.result.hidden = true;
            return;
        }
        const { candidate, todayUtc } = this.nextBirthday(parsed.month, parsed.day);
        const days = Math.round((candidate.getTime() - todayUtc) / 86400000);
        const birthdayLabel = `${parsed.month}월 ${parsed.day}일`;
        const nextDate = `${candidate.getUTCFullYear()}.${String(parsed.month).padStart(2, '0')}.${String(parsed.day).padStart(2, '0')}`;
        const statusLabel = days === 0 ? 'D-Day' : `D-${days}`;
        const statusNote = days === 0 ? '바로 오늘이 생일입니다.' : `다음 생일까지 ${days}일 남았습니다.`;
        this.error.textContent = '';
        this.resultContent.innerHTML = `
            <p class="eyebrow">선택한 생일</p>
            <h2>${birthdayLabel}</h2>
            <p>${birthdayLabel}의 다음 생일은 ${nextDate}입니다.</p>
            <div class="summary-grid">
                <div class="summary-card"><strong>생일</strong><span>${birthdayLabel}</span></div>
                <div class="summary-card"><strong>다음 생일</strong><span>${nextDate}</span></div>
                <div class="summary-card"><strong>오늘 기준 상태</strong><span>${statusLabel}</span></div>
                <div class="summary-card"><strong>남은 기간</strong><span>${days}일</span></div>
            </div>
            <p class="small">${statusNote}</p>`;
        this.result.hidden = false;
    }
}

document.addEventListener('DOMContentLoaded', () => new BirthdayDDayCalculator());
