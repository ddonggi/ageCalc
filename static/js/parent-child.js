class ParentChildCalculator {
    constructor() {
        this.parents = [];
        this.children = [];
        this.maxParents = 2;
        this.maxChildren = 20;

        this.parentLines = document.getElementById('parent-lines');
        this.childLines = document.getElementById('child-lines');
        this.resultContainer = document.getElementById('parent-child-result-container');
        this.resultContent = document.getElementById('parent-child-result-content');
        this.errorEl = document.getElementById('parent-child-error');

        this.init();
    }

    init() {
        this.loadFromUrl().then(() => {
            if (this.parents.length === 0) this.addParentLine();
            if (this.children.length === 0) this.addChildLine();
            this.bindControls();
            this.updateResult();
        });
    }

    bindControls() {
        document.getElementById('add-parent-line')?.addEventListener('click', () => {
            if (this.parents.length >= this.maxParents) {
                alert('부모는 두 분까지 기록할 수 있어요.');
                return;
            }
            this.addParentLine();
        });
        document.getElementById('add-child-line')?.addEventListener('click', () => {
            if (this.children.length >= this.maxChildren) {
                alert('자녀는 최대 20명까지 추가할 수 있어요.');
                return;
            }
            this.addChildLine();
        });

        document.addEventListener('click', (e) => {
            const target = e.target;
            if (!(target instanceof HTMLElement)) return;
            if (!target.closest('.role-dropdown')) {
                this.closeAllDropdowns();
            }
            if (target.id === 'save-result-image') {
                e.preventDefault();
                this.saveResultAsImage();
            }
            if (target.id === 'copy-result-link') {
                e.preventDefault();
                this.copyLink();
            }
        });
    }

    addParentLine(data = {}) {
        const id = `p${Date.now()}${Math.floor(Math.random() * 1000)}`;
        this.parents.push({ id, role: data.role || '', birth: this.normalizeBirthValue(data) });
        this.renderLines('parent');
    }

    addChildLine(data = {}) {
        const id = `c${Date.now()}${Math.floor(Math.random() * 1000)}`;
        this.children.push({ id, role: data.role || '', birth: this.normalizeBirthValue(data) });
        this.renderLines('child');
    }

    removeLine(kind, id) {
        if (kind === 'parent') {
            if (this.parents.length <= 1) return;
            this.parents = this.parents.filter(p => p.id !== id);
            this.renderLines('parent');
        } else {
            if (this.children.length <= 1) return;
            this.children = this.children.filter(c => c.id !== id);
            this.renderLines('child');
        }
        this.updateResult();
    }

    renderLines(kind) {
        const list = kind === 'parent' ? this.parents : this.children;
        const container = kind === 'parent' ? this.parentLines : this.childLines;
        if (!container) return;
        container.innerHTML = '';

        list.forEach((item) => {
            const line = document.createElement('div');
            line.className = 'person-line';
            const roleOptions = kind === 'parent'
                ? [
                    { value: 'mother', label: '엄마' },
                    { value: 'father', label: '아빠' }
                ]
                : [
                    { value: 'daughter', label: '딸' },
                    { value: 'son', label: '아들' }
                ];
            const defaultLabel = kind === 'parent' ? '엄마/아빠 선택' : '딸/아들 선택';
            const selectedLabel = roleOptions.find(opt => opt.value === item.role)?.label || defaultLabel;

            line.innerHTML = `
                <div class="role-dropdown" data-kind="${kind}" data-id="${item.id}">
                    <button type="button" class="role-btn" aria-expanded="false">${selectedLabel}</button>
                    <ul class="role-menu" role="listbox" aria-label="${defaultLabel}">
                        ${roleOptions.map(opt => `
                            <li>
                                <button type="button" class="role-option" data-value="${opt.value}">${opt.label}</button>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <div class="date-inputs">
                    <label class="field-label" for="birth-${item.id}">${selectedLabel} 생년월일 8자리</label>
                    <input type="text" id="birth-${item.id}" data-kind="${kind}" data-id="${item.id}" data-field="birth" placeholder="1992.10.02" inputmode="numeric" pattern="[0-9.]*" maxlength="10" value="${AgeCalcDateRules.formatDateDigits(item.birth || '')}" aria-describedby="parent-child-error" data-clarity-mask="true">
                </div>
                <button type="button" class="line-remove" title="삭제">-</button>
            `;
            container.appendChild(line);

            const dropdown = line.querySelector('.role-dropdown');
            const button = line.querySelector('.role-btn');
            const menu = line.querySelector('.role-menu');
            button.addEventListener('click', () => {
                const expanded = button.getAttribute('aria-expanded') === 'true';
                this.closeAllDropdowns();
                button.setAttribute('aria-expanded', expanded ? 'false' : 'true');
                dropdown.classList.toggle('open', !expanded);
            });
            menu.querySelectorAll('.role-option').forEach(optionBtn => {
                optionBtn.addEventListener('click', () => {
                    const value = optionBtn.dataset.value;
                    item.role = value;
                    button.textContent = roleOptions.find(opt => opt.value === value)?.label || defaultLabel;
                    button.setAttribute('aria-expanded', 'false');
                    dropdown.classList.remove('open');
                    this.updateResult();
                });
            });

            line.querySelectorAll('input').forEach(input => {
                input.addEventListener('input', (e) => {
                    const field = e.target.dataset.field;
                    if (field === 'birth') e.target.value = AgeCalcDateRules.formatDateDigits(e.target.value);
                    item[field] = e.target.value;
                    this.updateResult();
                });
            });

            line.querySelector('.line-remove').addEventListener('click', () => this.removeLine(kind, item.id));
        });
    }
    
    closeAllDropdowns() {
        document.querySelectorAll('.role-dropdown.open').forEach((node) => {
            node.classList.remove('open');
            const btn = node.querySelector('.role-btn');
            if (btn) btn.setAttribute('aria-expanded', 'false');
        });
    }

    normalizeBirthValue(data) {
        if (!data) return '';
        if (data.birth || data.b) {
            const raw = data.birth || data.b;
            const digits = this.digitsOnly(raw);
            if (digits.length === 8) return digits;
            return String(raw);
        }
        if (data.y && data.m && data.d) {
            const yyyy = String(data.y).padStart(4, '0');
            const mm = String(data.m).padStart(2, '0');
            const dd = String(data.d).padStart(2, '0');
            return `${yyyy}${mm}${dd}`;
        }
        return '';
    }

    digitsOnly(value) {
        return String(value || '').replace(/\D/g, '');
    }

    validateBirth6(raw) {
        const digits = this.digitsOnly(raw);
        if (digits.length !== 8) {
            return { valid: false, msg: '생년월일 8자리(YYYYMMDD)를 입력해 주세요.' };
        }
        try {
            const parsed = AgeCalcDateRules.parseBirthDateDigits(digits);
            const date = new Date(parsed.getUTCFullYear(), parsed.getUTCMonth(), parsed.getUTCDate());
            return { valid: true, msg: '', date, digits };
        } catch (error) {
            const message = String(error && error.message || '');
            return {
                valid: false,
                msg: message.includes('future') ? '미래 날짜는 입력할 수 없습니다.' : '존재하지 않는 날짜입니다.'
            };
        }
    }

    calcAgeOn(date, birth) {
        let age = date.getFullYear() - birth.getFullYear();
        const beforeBirthday =
            date.getMonth() < birth.getMonth() ||
            (date.getMonth() === birth.getMonth() && date.getDate() < birth.getDate());
        if (beforeBirthday) age -= 1;
        return age;
    }

    childOrderLabel(index) {
        const labels = ['첫째', '둘째', '셋째', '넷째', '다섯째', '여섯째', '일곱째', '여덟째', '아홉째', '열째'];
        if (index < labels.length) return labels[index];
        return `${index + 1}째`;
    }

    buildResults() {
        const today = new Date();
        const milestones = [60, 70, 80, 90];
        const milestoneLabels = { 60: '환갑', 70: '칠순', 80: '팔순', 90: '구순' };

        const results = [];

        for (const parent of this.parents) {
            if (!parent.role) return { error: '부모의 역할(엄마/아빠)을 선택해 주세요.' };
            const parentBirthCheck = this.validateBirth6(parent.birth);
            if (!parentBirthCheck.valid) return { error: `부모 ${parentBirthCheck.msg}` };
            const parentBirth = parentBirthCheck.date;

            for (const [idx, child] of this.children.entries()) {
                if (!child.role) return { error: '자녀의 역할(딸/아들)을 선택해 주세요.' };
                const childBirthCheck = this.validateBirth6(child.birth);
                if (!childBirthCheck.valid) return { error: `자녀 ${childBirthCheck.msg}` };
                const childBirth = childBirthCheck.date;
                if (childBirth <= parentBirth) {
                    return { error: '자녀 생년월일이 부모보다 빠를 수 없습니다.' };
                }

                const parentAgeAtBirth = this.calcAgeOn(childBirth, parentBirth);
                const parentNow = this.calcAgeOn(today, parentBirth);
                const childNow = this.calcAgeOn(today, childBirth);
                const diff = parentNow - childNow;

                const parentLabel = parent.role === 'mother' ? '엄마' : '아빠';
                const childLabel = child.role === 'daughter' ? '딸' : '아들';
                const orderLabel = this.childOrderLabel(idx);
                const childBirthYear = childBirth.getFullYear();

                const milestoneHtml = milestones.map(age => {
                    const date = new Date(parentBirth.getFullYear() + age, parentBirth.getMonth(), parentBirth.getDate());
                    const childAge = this.calcAgeOn(date, childBirth);
                    return `
                        <div class="result-section">
                            <p>${date.getFullYear()}년에 ${parentLabel}는 ${milestoneLabels[age]}(${age})이고 ${orderLabel} ${childLabel}은 ${childAge}살이에요.</p>
                        </div>
                    `;
                }).join('');

                const parentIcon = parent.role === 'father'
                    ? '<video class="family-icon" src="/static/videos/father.mp4" autoplay loop muted playsinline></video>'
                    : parent.role === 'mother'
                    ? '<video class="family-icon" src="/static/videos/mother.mp4" autoplay loop muted playsinline></video>'
                    : '';
                const childIcon = child.role === 'son'
                    ? '<video class="family-icon" src="/static/videos/son.mp4" autoplay loop muted playsinline></video>'
                    : child.role === 'daughter'
                    ? '<video class="family-icon" src="/static/videos/daughter.mp4" autoplay loop muted playsinline></video>'
                    : '';

                results.push(`
                    <div class="result success">
                        <p class="message">${parentIcon}${parentLabel}와 ${childIcon}${orderLabel} ${childLabel}의 시간이 이렇게 이어졌어요.</p>
                        <div class="age-info">
                            <p class="age">출산 당시 ${parentLabel} 만 나이: <span class="age-number">${parentAgeAtBirth}세</span></p>
                            <p class="age">지금 두 사람의 만 나이 차이: <span class="age-number">${diff}세</span></p>
                        </div>
                        ${milestoneHtml}
                        <div class="result-section">
                            <h4>다음 가족 시점 확인</h4>
                            <div class="footer-links">
                                <a href="/guides/sixtieth-seventieth-eightieth-age-guide">환갑·칠순 기준 보기</a>
                                <a href="/school-grade-calculator?year=${childBirthYear}">자녀 학교 시점 보기</a>
                                <a href="/school-entry-year-table?year=${childBirthYear}">자녀 입학년도 보기</a>
                            </div>
                        </div>
                    </div>
                `);
            }
        }

        return { html: results.join('') };
    }

    updateResult() {
        const result = this.buildResults();
        if (result.error) {
            this.showError(result.error);
            this.clearResult();
            return;
        }

        this.showError('');
        this.resultContent.innerHTML = result.html;
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

    async buildShareLink() {
        return `${window.location.origin}${window.location.pathname}`;
    }

    async loadFromUrl() {
        if (window.location.search) {
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    async saveResultAsImage() {
        const content = document.getElementById('parent-child-result-content');
        if (!content || !content.innerHTML.trim()) return;
        if (typeof html2canvas !== 'function') return;
        const canvas = await html2canvas(content, { backgroundColor: null, scale: 2 });
        const link = document.createElement('a');
        link.download = 'parent-child-result.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    }

    async copyLink() {
        try {
            const link = await this.buildShareLink();
            await navigator.clipboard.writeText(link);
            alert('링크가 복사되었습니다.');
        } catch {
            alert('링크 복사에 실패했습니다.');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ParentChildCalculator();
});
