(() => {
    const input = document.getElementById('guess-input');
    const submitBtn = document.getElementById('guess-submit');
    const resetBtn = document.getElementById('guess-reset');
    const statusEl = document.getElementById('guess-status');
    const triesEl = document.getElementById('guess-tries');

    if (!input || !submitBtn || !resetBtn || !statusEl || !triesEl) return;

    let answer = Math.floor(Math.random() * 100) + 1;
    let tries = 0;
    let done = false;

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const updateTries = () => {
        triesEl.textContent = `시도 횟수: ${tries}`;
    };

    const checkGuess = () => {
        if (done) return;

        const value = Number(input.value);
        if (!Number.isInteger(value) || value < 1 || value > 100) {
            setStatus('1부터 100 사이 정수를 입력하세요.');
            return;
        }

        tries += 1;
        updateTries();

        if (value < answer) {
            setStatus('더 큰 숫자입니다.');
        } else if (value > answer) {
            setStatus('더 작은 숫자입니다.');
        } else {
            done = true;
            setStatus(`정답! ${tries}번 만에 맞췄습니다.`);
        }
    };

    const resetGame = () => {
        answer = Math.floor(Math.random() * 100) + 1;
        tries = 0;
        done = false;
        input.value = '';
        setStatus('숫자를 입력하세요.');
        updateTries();
    };

    submitBtn.addEventListener('click', checkGuess);
    input.addEventListener('keydown', (event) => {
        if (event.key === 'Enter') checkGuess();
    });
    resetBtn.addEventListener('click', resetGame);
})();
