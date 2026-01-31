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
            this.yearInput.addEventListener(evt, () => this.updateResult());
            this.monthInput.addEventListener(evt, () => this.updateResult());
            this.dayInput.addEventListener(evt, () => this.updateResult());
        });
    }

    validate() {
        const y = Number(this.yearInput.value || 0);
        const m = Number(this.monthInput.value || 0);
        const d = Number(this.dayInput.value || 0);

        if (!y || !m || !d) {
            return { valid: false, msg: '출생일을 모두 입력해 주세요.' };
        }
        if (m < 1 || m > 12) {
            return { valid: false, msg: '월은 1~12 사이로 입력해 주세요.' };
        }
        if (d < 1 || d > 31) {
            return { valid: false, msg: '일은 1~31 사이로 입력해 주세요.' };
        }
        const birth = new Date(y, m - 1, d);
        if (Number.isNaN(birth.getTime())) {
            return { valid: false, msg: '올바른 날짜를 입력해 주세요.' };
        }
        return { valid: true, birth };
    }

    calculateMonths(birth) {
        const today = new Date();
        let months = (today.getFullYear() - birth.getFullYear()) * 12;
        months += today.getMonth() - birth.getMonth();
        if (today.getDate() < birth.getDate()) {
            months -= 1;
        }
        return Math.max(0, months);
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
        const years = Math.floor(months / 12);
        const remain = months % 12;
        const vaccineTips = this.getVaccineTips(months);
        const milestoneTips = this.getMilestoneTips(months);

        this.resultContent.innerHTML = `
            <div class="result success">
                <p class="message">현재 개월 수</p>
                <div class="age-info">
                    <p class="age"><span class="age-number">${months}개월</span></p>
                </div>
                <p class="small">${years}년 ${remain}개월</p>
                <p class="small">* 예방접종/발달 단계 확인에 활용해 보세요.</p>
                <div class="result-section">
                    <h4>예방접종 참고</h4>
                    <p>${vaccineTips}</p>
                </div>
                <div class="result-section">
                    <h4>발달 단계 참고</h4>
                    <p>${milestoneTips}</p>
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

    getVaccineTips(months) {
        if (months < 1) {
            return '미국 일정 예시: 출생 직후 B형간염 1차가 안내될 수 있습니다. 병원 지침을 확인하세요.';
        }
        if (months < 3) {
            return '2개월 전후에 DTaP, Hib, IPV, 폐구균(PCV), 로타바이러스 등 기본 접종이 시작됩니다.';
        }
        if (months < 5) {
            return '4개월 전후 기본 접종이 이어집니다. 접종 간격은 의료진과 상의하세요.';
        }
        if (months < 7) {
            return '6개월 전후 기본 접종이 이어집니다. 독감은 생후 6개월부터 매년 접종이 권장됩니다.';
        }
        if (months < 12) {
            return '기본 접종 유지 구간입니다. 독감은 매년 시즌에 맞춰 진행합니다.';
        }
        if (months < 16) {
            return '12~15개월 구간에서 MMR/수두, Hib·폐구균 부스터 등이 안내될 수 있습니다.';
        }
        if (months < 19) {
            return '15~18개월 구간에서 DTaP 추가 접종 등이 안내될 수 있습니다.';
        }
        if (months < 24) {
            return '12~23개월 구간에 A형간염 2회 접종이 안내될 수 있습니다.';
        }
        return '접종 일정은 국가/병원 지침에 따라 달라집니다. 최신 일정은 소아과 상담을 권장합니다.';
    }

    getMilestoneTips(months) {
        if (months < 3) {
            return '2개월 무렵: 웃기, 얼굴 보기, 다른 소리 내기, 엎드렸을 때 머리 들기 등이 나타납니다.';
        }
        if (months < 5) {
            return '4개월 무렵: 웃거나 킥킥거리기, 옹알이, 소리에 고개 돌리기, 머리 고정 등이 늘어납니다.';
        }
        if (months < 7) {
            return '6개월 무렵: 웃기, “라즈베리” 소리, 장난감 잡기, 배→등 굴리기 등이 보입니다.';
        }
        if (months < 10) {
            return '9개월 무렵: 혼자 앉기, 옹알이 반복 소리, 손가락으로 먹기, 물건을 찾기 등이 나타납니다.';
        }
        if (months < 13) {
            return '12개월 무렵: “바이바이” 손흔들기, 간단한 말 이해, 가구 잡고 서기/걷기 등이 관찰됩니다.';
        }
        if (months < 16) {
            return '15개월 무렵: 혼자 몇 걸음 걷기, 간단한 지시 이해, 손으로 먹기 등이 늘어납니다.';
        }
        if (months < 19) {
            return '18개월 무렵: 3단어 이상 말하기 시도, 간단한 지시 따르기, 혼자 걷기 등이 보입니다.';
        }
        return '발달은 개인차가 큽니다. 걱정되는 부분이 있으면 소아과 상담을 권장합니다.';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new BabyMonthsCalculator();
});
