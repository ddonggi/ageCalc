(() => {
    const statusEl = document.getElementById('simon-status');
    const scoreEl = document.getElementById('simon-score');
    const pad = document.getElementById('simon-pad');
    const startBtn = document.getElementById('simon-start');
    const resetBtn = document.getElementById('simon-reset');

    if (!statusEl || !scoreEl || !pad || !startBtn || !resetBtn) return;

    const colors = ['green', 'red', 'yellow', 'blue'];

    let sequence = [];
    let inputIndex = 0;
    let accepting = false;

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const updateScore = () => {
        scoreEl.textContent = `점수: ${sequence.length ? sequence.length - 1 : 0}`;
    };

    const flash = (color) => {
        const button = pad.querySelector(`[data-color="${color}"]`);
        if (!button) return;
        button.classList.add('active');
        window.setTimeout(() => button.classList.remove('active'), 250);
    };

    const playSequence = () => {
        accepting = false;
        inputIndex = 0;
        setStatus('순서를 보세요.');
        sequence.forEach((color, index) => {
            window.setTimeout(() => flash(color), 500 * index + 400);
        });
        window.setTimeout(() => {
            accepting = true;
            setStatus('내 차례입니다.');
        }, 500 * sequence.length + 400);
    };

    const nextRound = () => {
        const nextColor = colors[Math.floor(Math.random() * colors.length)];
        sequence.push(nextColor);
        updateScore();
        playSequence();
    };

    const startGame = () => {
        if (sequence.length) return;
        sequence = [];
        updateScore();
        nextRound();
    };

    const resetGame = () => {
        sequence = [];
        inputIndex = 0;
        accepting = false;
        updateScore();
        setStatus('시작 버튼을 눌러 플레이하세요.');
    };

    const handleInput = (color) => {
        if (!accepting) return;

        flash(color);
        if (color !== sequence[inputIndex]) {
            accepting = false;
            setStatus(`게임 종료. 점수: ${sequence.length - 1}`);
            return;
        }

        inputIndex += 1;
        if (inputIndex === sequence.length) {
            accepting = false;
            setStatus('정답! 다음 라운드');
            window.setTimeout(nextRound, 500);
        }
    };

    pad.addEventListener('click', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLButtonElement)) return;
        handleInput(target.dataset.color);
    });

    startBtn.addEventListener('click', startGame);
    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
