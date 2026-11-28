(() => {
    const form = document.querySelector('#age-form');
    const birth = document.querySelector('#birth-input');
    const error = document.querySelector('#birth-error');
    const sheet = document.querySelector('#result-container');
    const savedResult = document.querySelector('.filled-result');
    const initialDate = birth.value;
    const initialCalendar = form.elements.calendar_type.value;
    const tools = [...document.querySelectorAll('.tool[data-clean]')];
    const initialLinks = tools.map(link => link.href);

    function validate() {
        if (birth.value.length !== 8) return '생년월일을 숫자 8자리로 입력해 주세요.';
        try {
            AgeCalcDateRules.parseBirthDateDigits(birth.value, form.dataset.today);
            return '';
        } catch (problem) {
            return problem.message.includes('future')
                ? '미래 날짜는 입력할 수 없어요.'
                : '존재하는 생년월일인지 확인해 주세요.';
        }
    }

    function showError(message) {
        error.textContent = message;
        birth.setAttribute('aria-invalid', message ? 'true' : 'false');
    }

    function updateInput() {
        birth.value = AgeCalcDateRules.formatDateDigits(birth.value);
        showError(birth.value.length === 8 ? validate() : '');
        if (!savedResult) return;
        const current = birth.value === initialDate && form.elements.calendar_type.value === initialCalendar;
        savedResult.hidden = !current;
        document.querySelector('.empty-result').hidden = current;
        tools.forEach((link, index) => { link.href = current ? initialLinks[index] : link.dataset.clean; });
    }

    form.noValidate = true;
    form.addEventListener('input', updateInput);
    form.addEventListener('submit', event => {
        const message = validate();
        if (message) {
            event.preventDefault();
            showError(message);
            birth.focus();
        }
    });
    if (location.hash === '#result-container') {
        if (savedResult) sheet.focus({ preventScroll: true });
        else if (birth.getAttribute('aria-invalid') === 'true') birth.focus();
    } else if (!location.hash && window.matchMedia('(hover: hover) and (pointer: fine)').matches) {
        birth.focus({ preventScroll: true });
    }

    if (!savedResult) return;
    const status = document.querySelector('#share-status');
    document.querySelector('#copy').addEventListener('click', async () => {
        const url = location.origin + location.pathname;
        try {
            await navigator.clipboard.writeText(url);
            status.textContent = '생년월일을 제외한 계산기 주소를 복사했어요.';
        } catch {
            status.textContent = '복사할 계산기 주소　' + url;
        }
    });
    document.querySelector('#save').addEventListener('click', () => {
        const canvas = document.createElement('canvas');
        canvas.width = 1000;
        canvas.height = 600;
        const ctx = canvas.getContext('2d');
        if (!ctx) {
            status.textContent = '이 브라우저에서는 결과 이미지를 만들 수 없어요.';
            return;
        }
        ctx.fillStyle = '#fff5cd';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.strokeStyle = '#332e31';
        ctx.lineWidth = 4;
        ctx.strokeRect(20, 20, 960, 560);
        ctx.fillStyle = '#332e31';
        ctx.textAlign = 'center';
        ctx.font = 'bold 45px sans-serif';
        ctx.fillText('AgeCalc · 만 나이 계산기', 500, 110);
        ctx.font = 'bold 120px sans-serif';
        ctx.fillText('만 ' + document.querySelector('#age-number').textContent + '세', 500, 277);
        ctx.font = '32px sans-serif';
        ctx.fillText(sheet.querySelector('time').textContent, 500, 356);
        const facts = sheet.querySelectorAll('.facts > div');
        ctx.fillText(facts[1].innerText.replace(/\s+/g, ' '), 500, 428);
        ctx.fillText(facts[2].innerText.replace(/\s+/g, ' '), 500, 491);
        canvas.toBlob(blob => {
            if (!blob) { status.textContent = '이미지를 저장할 수 없어요. 다시 시도해 주세요.'; return; }
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'AgeCalc-' + form.dataset.today + '.png';
            link.click();
            setTimeout(() => URL.revokeObjectURL(url), 30000);
            status.textContent = '결과 이미지를 만들었어요.';
        }, 'image/png');
    });
})();
