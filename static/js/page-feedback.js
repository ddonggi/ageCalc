(() => {
    const root = document.querySelector('[data-page-feedback]');
    if (!root) return;

    const pagePath = root.getAttribute('data-page-feedback');
    const storageKey = `agecalc:feedback:${pagePath}`;
    const status = root.querySelector('.page-feedback-status');
    const buttons = Array.from(root.querySelectorAll('[data-feedback-vote]'));

    const setStatus = (message) => {
        if (status) status.textContent = message;
    };

    const disableButtons = () => {
        buttons.forEach((button) => {
            button.disabled = true;
            button.setAttribute('aria-disabled', 'true');
        });
    };

    try {
        if (window.localStorage.getItem(storageKey)) {
            disableButtons();
            setStatus('의견 감사합니다.');
            return;
        }
    } catch (error) {
        // localStorage access can fail in strict browser privacy modes.
    }

    buttons.forEach((button) => {
        button.addEventListener('click', async () => {
            const vote = button.getAttribute('data-feedback-vote');
            if (!vote) return;

            disableButtons();
            setStatus('의견을 저장하는 중입니다.');

            try {
                const response = await fetch('/page-feedback', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({page_path: pagePath, vote}),
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok || data.ok !== true) {
                    throw new Error('feedback failed');
                }
                try {
                    window.localStorage.setItem(storageKey, vote);
                } catch (error) {
                    // Server-side feedback was recorded; the browser marker is optional.
                }
                setStatus('의견 감사합니다.');
            } catch (error) {
                buttons.forEach((item) => {
                    item.disabled = false;
                    item.removeAttribute('aria-disabled');
                });
                setStatus('저장하지 못했습니다. 잠시 후 다시 시도해 주세요.');
            }
        });
    });
})();
