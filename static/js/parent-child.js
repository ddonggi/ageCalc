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
                    <input type="text" data-kind="${kind}" data-id="${item.id}" data-field="birth" placeholder="921002" inputmode="numeric" pattern="[0-9]*" maxlength="6" value="${item.birth || ''}">
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
            if (digits.length === 6) return digits;
            if (digits.length === 8) {
                return `${digits.slice(2, 4)}${digits.slice(4, 6)}${digits.slice(6, 8)}`;
            }
            return String(raw);
        }
        if (data.y && data.m && data.d) {
            const yy = String(data.y).slice(-2).padStart(2, '0');
            const mm = String(data.m).padStart(2, '0');
            const dd = String(data.d).padStart(2, '0');
            return `${yy}${mm}${dd}`;
        }
        return '';
    }

    digitsOnly(value) {
        return String(value || '').replace(/\D/g, '');
    }

    convertYYtoYYYY(yy) {
        const num = parseInt(yy, 10);
        if (Number.isNaN(num)) return null;
        const currentYY = new Date().getFullYear() % 100;
        if (num <= currentYY) return 2000 + num;
        return 1900 + num;
    }

    validateBirth6(raw) {
        const digits = this.digitsOnly(raw);
        if (digits.length !== 6) {
            return { valid: false, msg: '생년월일 6자리(YYMMDD)를 입력해 주세요.' };
        }

        const yy = digits.slice(0, 2);
        const mm = digits.slice(2, 4);
        const dd = digits.slice(4, 6);

        const year = this.convertYYtoYYYY(yy);
        const month = parseInt(mm, 10);
        const day = parseInt(dd, 10);

        if (!year) {
            return { valid: false, msg: '연도를 다시 확인해 주세요.' };
        }
        if (month < 1 || month > 12) {
            return { valid: false, msg: '월은 1~12 사이여야 합니다.' };
        }
        if (day < 1 || day > 31) {
            return { valid: false, msg: '일을 다시 확인해 주세요.' };
        }

        const date = new Date(year, month - 1, day);
        if (
            date.getFullYear() !== year ||
            date.getMonth() + 1 !== month ||
            date.getDate() !== day
        ) {
            return { valid: false, msg: '존재하지 않는 날짜입니다.' };
        }

        const now = new Date();
        if (date > now) {
            return { valid: false, msg: '미래 날짜는 입력할 수 없습니다.' };
        }

        return { valid: true, msg: '', date, digits };
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
        const params = new URLSearchParams();
        if (typeof ShareCodec !== 'undefined') {
            const payload = { parents: this.parents, children: this.children };
            const encoded = await ShareCodec.encode(payload);
            params.set('s', encoded);
            return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
        }
        this.parents.forEach((p, idx) => {
            params.set(`p${idx + 1}r`, p.role);
            params.set(`p${idx + 1}b`, this.digitsOnly(p.birth));
        });
        this.children.forEach((c, idx) => {
            params.set(`c${idx + 1}r`, c.role);
            params.set(`c${idx + 1}b`, this.digitsOnly(c.birth));
        });
        return `${window.location.origin}${window.location.pathname}?${params.toString()}`;
    }

    async loadFromUrl() {
        const params = new URLSearchParams(window.location.search);
        const packed = params.get('s');
        if (packed && typeof ShareCodec !== 'undefined') {
            try {
                const decoded = await ShareCodec.decode(packed);
                const parents = Array.isArray(decoded.parents) ? decoded.parents : [];
                const children = Array.isArray(decoded.children) ? decoded.children : [];
                this.parents = [];
                this.children = [];
                parents.slice(0, this.maxParents).forEach(p => this.addParentLine(p));
                children.slice(0, this.maxChildren).forEach(c => this.addChildLine(c));
                return;
            } catch {
                // fallback below
            }
        }
        const parents = [];
        const children = [];

        for (let i = 1; i <= this.maxParents; i += 1) {
            const role = params.get(`p${i}r`);
            const birth = params.get(`p${i}b`);
            const y = params.get(`p${i}y`);
            const m = params.get(`p${i}m`);
            const d = params.get(`p${i}d`);
            if (role || birth || y || m || d) parents.push({ role, birth, y, m, d });
        }

        for (let i = 1; i <= this.maxChildren; i += 1) {
            const role = params.get(`c${i}r`);
            const birth = params.get(`c${i}b`);
            const y = params.get(`c${i}y`);
            const m = params.get(`c${i}m`);
            const d = params.get(`c${i}d`);
            if (role || birth || y || m || d) children.push({ role, birth, y, m, d });
        }

        this.parents = [];
        this.children = [];
        parents.forEach(p => this.addParentLine(p));
        children.forEach(c => this.addChildLine(c));
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
