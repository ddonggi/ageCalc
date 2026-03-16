class DDayCalculator {
    constructor() {
        this.labelInput = document.getElementById("dday-label");
        this.yearInput = document.getElementById("dday-year");
        this.monthInput = document.getElementById("dday-month");
        this.dayInput = document.getElementById("dday-day");
        this.modeInputs = Array.from(document.querySelectorAll('input[name="dday-mode"]'));
        this.errorEl = document.getElementById("dday-error");
        this.resultContainer = document.getElementById("dday-result-container");
        this.resultContent = document.getElementById("dday-result-content");

        if (!this.yearInput || !this.monthInput || !this.dayInput || !this.resultContainer || !this.resultContent) {
            return;
        }

        this.bindEvents();
        this.updateResult();
    }

    bindEvents() {
        [this.labelInput, this.yearInput, this.monthInput, this.dayInput].forEach((input) => {
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
        this.limitDigits(this.yearInput, 4);
        this.limitDigits(this.monthInput, 2);
        this.limitDigits(this.dayInput, 2);
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
        const yearText = String(this.yearInput.value || "");
        const monthText = String(this.monthInput.value || "");
        const dayText = String(this.dayInput.value || "");
        const year = Number(yearText || 0);
        const month = Number(monthText || 0);
        const day = Number(dayText || 0);

        if (!year || !month || !day) {
            return { valid: false, message: "연, 월, 일을 모두 입력해 주세요." };
        }
        if (yearText.length !== 4) {
            return { valid: false, message: "연도는 4자리로 입력해 주세요." };
        }
        if (monthText.length !== 2) {
            return { valid: false, message: "월은 2자리로 입력해 주세요." };
        }
        if (dayText.length !== 2) {
            return { valid: false, message: "일은 2자리로 입력해 주세요." };
        }
        if (month < 1 || month > 12) {
            return { valid: false, message: "월은 1~12 사이로 입력해 주세요." };
        }
        if (day < 1 || day > 31) {
            return { valid: false, message: "일은 1~31 사이로 입력해 주세요." };
        }

        const date = new Date(year, month - 1, day);
        if (
            Number.isNaN(date.getTime()) ||
            date.getFullYear() !== year ||
            date.getMonth() !== month - 1 ||
            date.getDate() !== day
        ) {
            return { valid: false, message: "올바른 날짜를 입력해 주세요." };
        }

        return { valid: true, date };
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
            this.showError(validation.message);
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
                <p class="result-kicker">${mode === "since" ? "Elapsed Date" : "Countdown"}</p>
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
