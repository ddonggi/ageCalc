function buildBirthdayResultHTML({ birthdayLabel, nextDate, statusLabel, days, statusNote }) {
    return `
        <p class="eyebrow">선택한 생일</p>
        <h2>${birthdayLabel}</h2>
        <p>${birthdayLabel}의 다음 생일은 ${nextDate}입니다.</p>
        <div class="summary-grid">
            <div class="summary-card"><strong>생일</strong><span>${birthdayLabel}</span></div>
            <div class="summary-card"><strong>다음 생일</strong><span>${nextDate}</span></div>
            <div class="summary-card"><strong>오늘 기준 상태</strong><span>${statusLabel}</span></div>
            <div class="summary-card"><strong>남은 기간</strong><span>${days}일</span></div>
        </div>
        <p class="small">${statusNote}</p>
        <div class="result-next">
            <h3>이어서 확인하기</h3>
            <div class="result-next-links">
                <a href="/age">현재 만나이 확인</a>
                <a href="/d-day">다른 기념일 계산</a>
                <a href="/life-timeline">생애 타임라인 보기</a>
            </div>
            <p class="small">저장에 동의한 생년월일이 있으면 다음 계산기에서 자동으로 불러옵니다.</p>
        </div>`;
}

class BirthdayDDayCalculator {
    constructor() {
        this.form = document.getElementById('birthday-dday-form');
        this.input = document.getElementById('birthday-dday-input');
        this.error = document.getElementById('birthday-dday-error');
        this.result = document.getElementById('birthday-dday-result');
        this.resultContent = document.getElementById('birthday-dday-result-content');
        this.monthInput = document.getElementById('birthday-dday-month');
        this.dayInput = document.getElementById('birthday-dday-day');
        if (!this.form || !this.input) return;
        this.bindEvents();
    }

    bindEvents() {
        this.form.addEventListener('submit', (event) => {
            try {
                const parsed = AgeCalcDateRules.parseMonthDayDigits(this.input.value);
                this.monthInput.value = parsed.month;
                this.dayInput.value = parsed.day;
            } catch {
                event.preventDefault();
                this.error.textContent = '존재하는 생일을 입력해 주세요.';
            }
        });
        this.input.addEventListener('input', () => {
            this.input.value = AgeCalcDateRules.formatMonthDayDigits(this.input.value);
            this.error.textContent = '';
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

}

document.addEventListener('DOMContentLoaded', () => new BirthdayDDayCalculator());

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BirthdayDDayCalculator, buildBirthdayResultHTML };
}
