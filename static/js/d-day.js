class DDayCalculator {
    constructor() {
        this.labelInput = document.getElementById("dday-label");
        this.dateInput = document.getElementById("dday-date");
        this.modeInputs = Array.from(document.querySelectorAll('input[name="dday-mode"]'));
        this.errorEl = document.getElementById("dday-error");
        this.resultContainer = document.getElementById("dday-result-container");
        this.resultContent = document.getElementById("dday-result-content");

        if (!this.dateInput || !this.resultContainer || !this.resultContent) {
            return;
        }

        this.bindEvents();
    }

    bindEvents() {
        [this.labelInput, this.dateInput].forEach((input) => {
            if (!input) return;
            ["input", "change"].forEach((eventName) => {
                input.addEventListener(eventName, () => {
                    this.normalizeInputs();
                    this.updateResult();
                });
            });
        });

        this.modeInputs.forEach((input) => {
            input.addEventListener("change", () => this.updateResult());
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

    updateResult() {
        const validation = this.validate();
        if (!validation.valid) {
            this.showError(validation.incomplete ? "" : validation.message);
            this.clearResult();
            return;
        }

        const mode = this.getMode();
        const eventName = this.getEventName();
        const diff = this.diffDays(validation.date);
        const primary = this.buildPrimaryLabel(mode, diff);
        const absDiff = Math.abs(diff);

        this.showError("");
        this.resultContent.innerHTML = `
            <div class="result success">
                <p class="message">${eventName}</p>
                <div class="count-pill ${primary.tone}">${primary.label}</div>
                <p class="result-kicker">${mode === "since" ? "경과 일수" : "남은 일수"}</p>
                <p>${this.formatDate(validation.date)} 기준으로 ${primary.caption}</p>
                <div class="summary-grid">
                    <div class="summary-card">
                        <strong>기준 날짜</strong>
                        <span>${this.formatDate(validation.date)}</span>
                    </div>
                    <div class="summary-card">
                        <strong>오늘 기준 차이</strong>
                        <span>${absDiff}일</span>
                    </div>
                    <div class="summary-card">
                        <strong>표시 방식</strong>
                        <span>${mode === "since" ? "지난 날부터" : "다가오는 날"}</span>
                    </div>
                </div>
                <p class="small">오늘 제외 기준입니다. 같은 날짜면 D-Day로 표시합니다.</p>
            </div>
        `;
        this.resultContainer.classList.add("show");
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
