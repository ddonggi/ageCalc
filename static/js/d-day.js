class DDayCalculator {
    constructor() {
        this.labelInput = document.getElementById("dday-label");
        this.dateInput = document.getElementById("dday-date");
        this.modeInputs = Array.from(document.querySelectorAll('input[name="mode"]'));
        this.form = document.getElementById("dday-form");
        this.errorEl = document.getElementById("dday-error");
        this.resultContainer = document.getElementById("dday-result-container");
        this.resultContent = document.getElementById("dday-result-content");

        if (!this.dateInput || !this.resultContainer || !this.resultContent) {
            return;
        }

        this.bindEvents();
        this.bindPresets();
    }

    bindPresets() {
        this.presetButtons = Array.from(document.querySelectorAll('[data-dday-preset]'));
        this.presetStatus = document.getElementById('dday-preset-status');
        const allowedIds = new Set(['csat-academic-2027', 'csat-academic-2028']);
        let rows;
        try {
            rows = JSON.parse(document.getElementById('dday-exam-presets')?.textContent || '[]');
        } catch (_) {
            rows = [];
        }
        if (!Array.isArray(rows)) rows = [];
        const presets = new Map(rows.filter(row => row && allowedIds.has(row.id) && row.can_fill === true).map(row => [row.id, row]));
        this.presetButtons.forEach(button => {
            button.disabled = !presets.has(button.dataset.ddayPreset);
            button.addEventListener('click', () => {
                const preset = presets.get(button.dataset.ddayPreset);
                if (button.disabled || !preset || preset.can_fill !== true) return;
                this.clearPresetSelection();
                this.labelInput.value = preset.label;
                this.dateInput.value = preset.date_digits;
                this.modeInputs.forEach(input => {input.checked = input.value === 'until';});
                this.showError('');
                this.clearResult();
                button.setAttribute('aria-pressed', 'true');
                if (this.presetStatus) this.presetStatus.textContent = this.presetStatus.dataset.filledMessage || '';
                this.dateInput.focus();
                this.dateInput.scrollIntoView({block: 'center', behavior: 'instant'});
            });
        });
        [this.labelInput, this.dateInput, ...this.modeInputs].forEach(input => {
            if (!input) return;
            ['input', 'change'].forEach(type => input.addEventListener(type, () => this.clearPresetSelection()));
        });
    }

    clearPresetSelection() {
        this.presetButtons.forEach(button => button.setAttribute('aria-pressed', 'false'));
        if (this.presetStatus) this.presetStatus.textContent = '';
    }

    bindEvents() {
        [this.labelInput, this.dateInput].forEach((input) => {
            if (!input) return;
            ["input", "change"].forEach((eventName) => {
                input.addEventListener(eventName, () => {
                    this.normalizeInputs();
                    this.showError("");
                });
            });
        });

        this.modeInputs.forEach((input) => {
            input.addEventListener("change", () => this.showError(""));
        });
        this.form?.addEventListener("submit", (event) => {
            const validation = this.validate();
            if (!validation.valid) {
                event.preventDefault();
                this.showError(validation.message || "올바른 날짜를 입력해 주세요.");
            }
        });
    }

    normalizeInputs() {
        this.dateInput.value = AgeCalcDateRules.formatDateDigits(this.dateInput.value);
    }

    limitDigits(input, maxLength) {
        if (!input) return;
        const digits = String(input.value || "").replace(/\D/g, "").slice(0, maxLength);
        if (input.value !== digits) {
            input.value = digits;
        }
    }

    getMode() {
        return this.modeInputs.find((input) => input.checked)?.value || "until";
    }

    getEventName() {
        return this.labelInput?.value.trim() || "기념일";
    }

    validate() {
        const digits = String(this.dateInput.value || "").replace(/\D/g, "");
        if (digits.length < 8) return { valid: false, incomplete: true, message: "" };
        try {
            const parsed = AgeCalcDateRules.parseDateDigits(digits);
            const date = new Date(parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate());
            return { valid: true, date };
        } catch (error) {
            return { valid: false, message: "올바른 날짜를 입력해 주세요." };
        }
    }

    diffDays(targetDate) {
        const today = new Date();
        const todayUtc = Date.UTC(today.getFullYear(), today.getMonth(), today.getDate());
        const targetUtc = Date.UTC(targetDate.getFullYear(), targetDate.getMonth(), targetDate.getDate());
        return Math.round((targetUtc - todayUtc) / 86400000);
    }

    formatDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, "0");
        const day = String(date.getDate()).padStart(2, "0");
        return `${year}.${month}.${day}`;
    }

    buildPrimaryLabel(mode, diff) {
        if (diff === 0) {
            return { label: "D-Day", tone: "is-neutral", caption: "바로 오늘입니다." };
        }

        if (mode === "since") {
            if (diff < 0) {
                return {
                    label: `+${Math.abs(diff)}일`,
                    tone: "is-positive",
                    caption: `${Math.abs(diff)}일이 지났습니다.`,
                };
            }
            return {
                label: `D-${diff}`,
                tone: "",
                caption: `${diff}일 남았습니다.`,
            };
        }

        if (diff > 0) {
            return {
                label: `D-${diff}`,
                tone: "",
                caption: `${diff}일 남았습니다.`,
            };
        }

        return {
            label: `D+${Math.abs(diff)}`,
            tone: "is-positive",
            caption: `${Math.abs(diff)}일이 지났습니다.`,
        };
    }

    showError(message) {
        if (!this.errorEl) return;
        this.errorEl.textContent = message || "";
    }

    clearResult() {
        this.resultContent.innerHTML = "";
        this.resultContainer.classList.remove("show");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    new DDayCalculator();
});
