class PetAgeCalculator {
    constructor() {
        this.form = document.getElementById('pet-age-form');
        this.yearsInput = document.getElementById('pet-years');
        this.monthsInput = document.getElementById('pet-months');
        this.errorEl = document.getElementById('pet-error');
        this.resultContainer = document.getElementById('pet-result-container');
        this.resultContent = document.getElementById('pet-result-content');
        this.petType = this.form ? this.form.getAttribute('data-pet') : 'dog';
        this.sizeOptions = document.querySelectorAll('.pet-size-option');
        this.sizeRadios = document.querySelectorAll('input[name="pet-size"]');
        this.dogAgeTable = {
            small: [15, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64, 68, 72, 76, 80],
            medium: [15, 24, 28, 32, 36, 42, 47, 51, 56, 60, 65, 69, 74, 78, 83, 87],
            large: [15, 24, 28, 32, 36, 45, 50, 55, 61, 66, 72, 77, 82, 88, 93, 99],
            giant: [12, 22, 31, 38, 45, 49, 56, 64, 71, 79, 86, 93, 100, 107, 114, 121]
        };

        if (this.form) {
            this.bindEvents();
            this.updateResult();
        }
    }

    bindEvents() {
        ['input', 'change'].forEach(evt => {
            this.yearsInput.addEventListener(evt, () => this.updateResult());
            this.monthsInput.addEventListener(evt, () => this.updateResult());
        });

        this.sizeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateSizeUI();
                this.updateResult();
            });
        });

        this.updateSizeUI();
    }

    getAgeInYears() {
        const years = Number(this.yearsInput.value || 0);
        const months = Number(this.monthsInput.value || 0);
        return years + months / 12;
    }

    validate() {
        const years = Number(this.yearsInput.value || 0);
        const months = Number(this.monthsInput.value || 0);

        if (Number.isNaN(years) || Number.isNaN(months)) {
            return { valid: false, msg: '숫자만 입력해 주세요.' };
        }
        if (years < 0 || months < 0) {
            return { valid: false, msg: '0 이상의 값을 입력해 주세요.' };
        }
        if (months >= 12) {
            return { valid: false, msg: '개월은 0~11 사이로 입력해 주세요.' };
        }
        if (years === 0 && months === 0) {
            return { valid: false, msg: '나이를 입력해 주세요.' };
        }
        if (years > 30) {
            return { valid: false, msg: '30세 이하로 입력해 주세요.' };
        }
        return { valid: true };
    }

    calculateHumanAge(ageYears) {
        if (this.petType === 'cat') {
            return this.calcCat(ageYears);
        }
        return this.calcDog(ageYears);
    }

    calcDog(ageYears) {
        if (ageYears <= 0) return 0;
        const size = this.getDogSize();
        const table = this.dogAgeTable[size] || this.dogAgeTable.small;

        if (ageYears <= 1) {
            return 15 * ageYears;
        }
        if (ageYears <= 2) {
            return 15 + (24 - 15) * (ageYears - 1);
        }

        const whole = Math.floor(ageYears);
        const frac = ageYears - whole;
        const lastIndex = table.length;

        if (whole >= lastIndex) {
            const last = table[lastIndex - 1];
            const prev = table[lastIndex - 2] || last;
            const step = last - prev || 4;
            return last + step * (ageYears - lastIndex);
        }

        const base = table[whole - 1];
        const next = table[whole] ?? base;
        return base + (next - base) * frac;
    }

    calcCat(ageYears) {
        if (ageYears <= 0) return 0;
        if (ageYears <= 1) return 15 * ageYears;
        if (ageYears <= 2) return 15 + 9 * (ageYears - 1);
        return 24 + 4 * (ageYears - 2);
    }

    updateResult() {
        const v = this.validate();
        if (!v.valid) {
            this.showError(v.msg);
            this.clearResult();
            return;
        }

        this.showError('');
        const ageYears = this.getAgeInYears();
        const humanAge = this.calculateHumanAge(ageYears);
        const rounded = Math.round(humanAge);

        const petLabel = this.petType === 'cat' ? '고양이' : '강아지';
        const ageLabel = this.formatAgeLabel(ageYears);
        const sizeLabel = this.petType === 'dog' ? this.getDogSizeLabel() : '';

        this.resultContent.innerHTML = `
            <div class="result success">
                <p class="message">${petLabel} 나이 ${ageLabel} 기준 ${sizeLabel}</p>
                <div class="age-info">
                    <p class="age">사람 나이 환산: <span class="age-number">${rounded}세</span></p>
                </div>
                <p class="small">* 참고용 환산입니다. 개체 특성에 따라 차이가 있을 수 있습니다.</p>
            </div>
        `;
        this.resultContainer.classList.add('show');
    }

    formatAgeLabel(ageYears) {
        const totalMonths = Math.round(ageYears * 12);
        const years = Math.floor(totalMonths / 12);
        const months = totalMonths % 12;
        if (years > 0 && months > 0) return `${years}년 ${months}개월`;
        if (years > 0) return `${years}년`;
        return `${months}개월`;
    }

    showError(msg) {
        if (!this.errorEl) return;
        this.errorEl.textContent = msg || '';
        if (msg) {
            this.yearsInput.classList.add('error');
        } else {
            this.yearsInput.classList.remove('error');
        }
    }

    clearResult() {
        if (this.resultContent) this.resultContent.innerHTML = '';
        if (this.resultContainer) this.resultContainer.classList.remove('show');
    }

    getDogSize() {
        const selected = document.querySelector('input[name="pet-size"]:checked');
        return selected ? selected.value : 'small';
    }

    getDogSizeLabel() {
        const selected = document.querySelector('input[name="pet-size"]:checked');
        if (!selected) return '';
        if (selected.value === 'large') return '(대형견)';
        if (selected.value === 'giant') return '(초대형견)';
        if (selected.value === 'medium') return '(중형견)';
        return '(소형견)';
    }

    updateSizeUI() {
        this.sizeOptions.forEach(option => {
            const input = option.querySelector('input');
            option.classList.toggle('active', input && input.checked);
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new PetAgeCalculator();
});
