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
        this.parents.push({ id, role: data.role || '', y: data.y || '', m: data.m || '', d: data.d || '' });
        this.renderLines('parent');
    }

    addChildLine(data = {}) {
        const id = `c${Date.now()}${Math.floor(Math.random() * 1000)}`;
        this.children.push({ id, role: data.role || '', y: data.y || '', m: data.m || '', d: data.d || '' });
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
                ? '<option value="" disabled selected>엄마/아빠 선택</option><option value="mother">엄마</option><option value="father">아빠</option>'
                : '<option value="" disabled selected>딸/아들 선택</option><option value="daughter">딸</option><option value="son">아들</option>';

            line.innerHTML = `
                <select class="role-select" data-kind="${kind}" data-id="${item.id}" required>
                    ${roleOptions}
                </select>
                <div class="date-inputs">
                    <input type="number" data-kind="${kind}" data-id="${item.id}" data-field="y" min="1900" max="2100" placeholder="년" inputmode="numeric" value="${item.y}">
                    <input type="number" data-kind="${kind}" data-id="${item.id}" data-field="m" min="1" max="12" placeholder="월" inputmode="numeric" value="${item.m}">
                    <input type="number" data-kind="${kind}" data-id="${item.id}" data-field="d" min="1" max="31" placeholder="일" inputmode="numeric" value="${item.d}">
                </div>
                <button type="button" class="line-remove" title="삭제">-</button>
            `;
            container.appendChild(line);

            const select = line.querySelector('select');
            if (item.role) select.value = item.role;
            select.addEventListener('change', (e) => {
                item.role = e.target.value;
                this.updateResult();
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

    parseDate(y, m, d) {
        const yy = Number(y); const mm = Number(m); const dd = Number(d);
        if (!yy || !mm || !dd) return null;
        const date = new Date(yy, mm - 1, dd);
        if (Number.isNaN(date.getTime())) return null;
        if (date.getFullYear() !== yy || date.getMonth() !== mm - 1 || date.getDate() !== dd) return null;
        return date;
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
            const parentBirth = this.parseDate(parent.y, parent.m, parent.d);
            if (!parentBirth) return { error: '부모 생년월일을 모두 입력해 주세요.' };

            for (const [idx, child] of this.children.entries()) {
                if (!child.role) return { error: '자녀의 역할(딸/아들)을 선택해 주세요.' };
                const childBirth = this.parseDate(child.y, child.m, child.d);
                if (!childBirth) return { error: '자녀 생년월일을 모두 입력해 주세요.' };
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
            params.set(`p${idx + 1}y`, p.y);
            params.set(`p${idx + 1}m`, p.m);
            params.set(`p${idx + 1}d`, p.d);
        });
        this.children.forEach((c, idx) => {
            params.set(`c${idx + 1}r`, c.role);
            params.set(`c${idx + 1}y`, c.y);
            params.set(`c${idx + 1}m`, c.m);
            params.set(`c${idx + 1}d`, c.d);
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
            const y = params.get(`p${i}y`);
            const m = params.get(`p${i}m`);
            const d = params.get(`p${i}d`);
            if (role || y || m || d) parents.push({ role, y, m, d });
        }

        for (let i = 1; i <= this.maxChildren; i += 1) {
            const role = params.get(`c${i}r`);
            const y = params.get(`c${i}y`);
            const m = params.get(`c${i}m`);
            const d = params.get(`c${i}d`);
            if (role || y || m || d) children.push({ role, y, m, d });
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
