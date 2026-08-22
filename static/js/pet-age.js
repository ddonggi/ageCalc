function getPetModeUiState(mode, petType) {
    const isDog = petType === 'dog';
    const isAdoptionDate = mode === 'adoption-date';
    return {
        showSizeOptions: isDog,
        disableSizeOptions: isDog && isAdoptionDate,
        showSizeExplanation: isDog && isAdoptionDate
    };
}

class PetAgeCalculator {
    constructor() {
        this.form = document.getElementById('pet-age-form');
        this.yearsInput = document.getElementById('pet-years');
        this.monthsInput = document.getElementById('pet-months');
        this.birthDateInput = document.getElementById('pet-birth-date');
        this.adoptionDateInput = document.getElementById('pet-adoption-date');
        this.modeInputs = Array.from(document.querySelectorAll('input[name="pet-age-mode"]'));
        this.inputPanels = Array.from(document.querySelectorAll('[data-pet-panel]'));
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
        }
    }

    bindEvents() {
        ['input', 'change'].forEach(evt => {
            this.yearsInput?.addEventListener(evt, () => {
                this.normalizeInputs();
                this.updateResult();
            });
            this.monthsInput?.addEventListener(evt, () => {
                this.normalizeInputs();
                this.updateResult();
            });
        });

        [this.birthDateInput, this.adoptionDateInput].forEach(input => {
            input?.addEventListener('input', () => {
                input.value = AgeCalcDateRules.formatDateDigits(input.value);
                this.updateResult();
            });
        });

        this.modeInputs.forEach(input => {
            input.addEventListener('change', () => {
                this.updateModeUI();
                this.updateResult();
            });
        });

        this.sizeRadios.forEach(radio => {
            radio.addEventListener('change', () => {
                this.updateSizeUI();
                this.updateResult();
            });
        });

        this.updateSizeUI();
        this.updateModeUI();
    }

    normalizeInputs() {
        this.limitDigits(this.yearsInput, 2);
        this.limitDigits(this.monthsInput, 2);
    }

    limitDigits(input, maxLength) {
        if (!input) return;
        const digits = String(input.value || '').replace(/\D/g, '').slice(0, maxLength);
        if (input.value !== digits) {
            input.value = digits;
        }
    }

    getAgeInYears() {
        const years = Number(this.yearsInput.value || 0);
        const months = Number(this.monthsInput.value || 0);
        return years + months / 12;
    }

    getMode() {
        return this.modeInputs.find(input => input.checked)?.value || 'birth-date';
    }

    todayUtc() {
        const today = new Date();
        return new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate()));
    }

    completedMonthsFromDate(input) {
        const date = AgeCalcDateRules.parseDateDigits(input.value);
        const today = this.todayUtc();
        if (date > today) throw new Error('future');
        const months = AgeCalcDateRules.calculateCompletedMonths(
            AgeCalcDateRules.formatIsoDate(date),
            AgeCalcDateRules.formatIsoDate(today)
        );
        return { date, months };
    }

    validate() {
        const mode = this.getMode();
        if (mode === 'birth-date' || mode === 'adoption-date') {
            const input = mode === 'birth-date' ? this.birthDateInput : this.adoptionDateInput;
            const digits = String(input?.value || '').replace(/\D/g, '');
            if (digits.length < 8) return { valid: false, incomplete: true };
            try {
                const value = this.completedMonthsFromDate(input);
                return { valid: true, mode, ...value, ageYears: value.months / 12 };
            } catch (error) {
                return {
                    valid: false,
                    msg: String(error?.message || '').includes('future')
                        ? '미래 날짜는 입력할 수 없습니다.'
                        : '존재하는 날짜를 입력해 주세요.'
                };
            }
        }
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
        if (String(this.yearsInput.value || '') === '' && String(this.monthsInput.value || '') === '') {
            return { valid: false, incomplete: true };
        }
        if (years === 0 && months === 0) {
            return { valid: false, msg: '0개월보다 큰 나이를 입력해 주세요.' };
        }
        if (years > 30) {
            return { valid: false, msg: '30세 이하로 입력해 주세요.' };
        }
        return { valid: true, mode, ageYears: years + months / 12 };
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
            this.showError(v.incomplete ? '' : v.msg);
            this.clearResult();
            return;
        }

        this.showError('');
        if (v.mode === 'adoption-date') {
            const years = Math.floor(v.months / 12);
            const months = v.months % 12;
            const label = years > 0 ? `${years}년 ${months}개월` : `${months}개월`;
            this.resultContent.innerHTML = `
                <div class="result success">
                    <p class="message">오늘까지 함께한 기간</p>
                    <div class="age-info"><p class="age"><span class="age-number">${label}</span></p></div>
                    <p class="small">데려온 날부터 오늘까지 완료된 달 수입니다. 실제 나이나 사람 나이 환산값은 아닙니다.</p>
                </div>`;
            this.resultContainer.classList.add('show');
            return;
        }
        const ageYears = v.ageYears;
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
                <p class="small">환산 나이는 건강 상태나 기대수명을 판정하지 않습니다.</p>
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
            this.activeInput()?.classList.add('error');
        } else {
            [this.yearsInput, this.birthDateInput, this.adoptionDateInput].forEach(input => input?.classList.remove('error'));
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

    activeInput() {
        const mode = this.getMode();
        if (mode === 'birth-date') return this.birthDateInput;
        if (mode === 'adoption-date') return this.adoptionDateInput;
        return this.yearsInput;
    }

    updateModeUI() {
        const mode = this.getMode();
        const uiState = getPetModeUiState(mode, this.petType);
        this.inputPanels.forEach(panel => {
            panel.hidden = panel.getAttribute('data-pet-panel') !== mode;
        });
        const sizeOptions = document.getElementById('pet-size-options');
        const sizeExplanation = document.getElementById('pet-size-explanation');
        if (sizeOptions) {
            sizeOptions.hidden = !uiState.showSizeOptions;
            sizeOptions.classList.toggle('is-disabled', uiState.disableSizeOptions);
            sizeOptions.setAttribute('aria-disabled', String(uiState.disableSizeOptions));
        }
        this.sizeRadios.forEach(radio => {
            radio.disabled = uiState.disableSizeOptions;
        });
        if (sizeExplanation) {
            sizeExplanation.hidden = !uiState.showSizeExplanation;
        }
        this.modeInputs.forEach(input => {
            input.closest('label')?.classList.toggle('active', input.checked);
        });
        this.showError('');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new PetAgeCalculator();
});

if (typeof module !== 'undefined' && module.exports) {
    module.exports = { getPetModeUiState };
}
