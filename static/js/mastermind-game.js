(() => {
    const colors = [
        { name: '빨강', value: '#d44c3b' },
        { name: '파랑', value: '#3b6ed4' },
        { name: '초록', value: '#3c8d5a' },
        { name: '노랑', value: '#e2b13c' },
        { name: '보라', value: '#7d4aa7' },
        { name: '주황', value: '#e07a32' }
    ];

    const statusEl = document.getElementById('mastermind-status');
    const guessSlotsEl = document.getElementById('mastermind-slots');
    const paletteEl = document.getElementById('mastermind-palette');
    const historyEl = document.getElementById('mastermind-history');
    const submitBtn = document.getElementById('mastermind-submit');
    const clearBtn = document.getElementById('mastermind-clear');
    const newGameBtn = document.getElementById('mastermind-new');
    const secretRevealEl = document.getElementById('mastermind-secret');
    if (!statusEl || !guessSlotsEl || !paletteEl || !historyEl || !submitBtn || !clearBtn || !newGameBtn || !secretRevealEl) return;

    let secret = [];
    let currentGuess = [];
    let attempts = 0;
    let gameOver = false;
    const maxAttempts = 10;

    const buildPalette = () => {
        paletteEl.innerHTML = '';
        colors.forEach((color, index) => {
            const btn = document.createElement('button');
            btn.className = 'mastermind-color-btn';
            btn.style.background = color.value;
            btn.setAttribute('aria-label', color.name);
            btn.addEventListener('click', () => addColor(index));
            paletteEl.appendChild(btn);
        });
    };

    const buildSlots = () => {
        guessSlotsEl.innerHTML = '';
        for (let i = 0; i < 4; i += 1) {
            const slot = document.createElement('div');
            slot.className = 'mastermind-slot';
            const colorIndex = currentGuess[i];
            if (colorIndex !== undefined) {
                slot.style.background = colors[colorIndex].value;
                slot.setAttribute('aria-label', `${i + 1}번 슬롯: ${colors[colorIndex].name}`);
            } else {
                slot.setAttribute('aria-label', `${i + 1}번 슬롯: 비어 있음`);
            }
            guessSlotsEl.appendChild(slot);
        }
        submitBtn.disabled = currentGuess.length !== 4 || gameOver;
        clearBtn.disabled = currentGuess.length === 0 || gameOver;
    };

    const addColor = (index) => {
        if (gameOver || currentGuess.length >= 4) return;
        currentGuess.push(index);
        buildSlots();
    };

    const clearGuess = () => {
        if (gameOver) return;
        currentGuess = [];
        buildSlots();
    };

    const scoreGuess = (guess, code) => {
        let exact = 0;
        const guessCounts = Array(colors.length).fill(0);
        const codeCounts = Array(colors.length).fill(0);

        for (let i = 0; i < 4; i += 1) {
            if (guess[i] === code[i]) exact += 1;
            else {
                guessCounts[guess[i]] += 1;
                codeCounts[code[i]] += 1;
            }
        }

        let colorOnly = 0;
        for (let i = 0; i < colors.length; i += 1) {
            colorOnly += Math.min(guessCounts[i], codeCounts[i]);
        }

        return { exact, colorOnly };
    };

    const renderHistoryRow = (guess, result) => {
        const row = document.createElement('li');
        row.className = 'mastermind-row';

        const pegs = document.createElement('div');
        pegs.className = 'mastermind-pegs';
        guess.forEach((colorIndex) => {
            const peg = document.createElement('div');
            peg.className = 'mastermind-peg';
            peg.style.background = colors[colorIndex].value;
            pegs.appendChild(peg);
        });

        const feedback = document.createElement('div');
        feedback.className = 'mastermind-feedback';
        feedback.textContent = `위치 일치 ${result.exact}, 색상 일치 ${result.colorOnly}`;

        row.appendChild(pegs);
        row.appendChild(feedback);
        historyEl.prepend(row);
    };

    const endGame = (message) => {
        gameOver = true;
        statusEl.textContent = message;
        submitBtn.disabled = true;
        clearBtn.disabled = true;
        secretRevealEl.textContent = `정답: ${secret.map((idx) => colors[idx].name).join(', ')}`;
    };

    const submitGuess = () => {
        if (gameOver || currentGuess.length !== 4) return;
        attempts += 1;
        const result = scoreGuess(currentGuess, secret);
        renderHistoryRow(currentGuess, result);

        if (result.exact === 4) endGame(`${attempts}번 만에 정답을 맞혔습니다!`);
        else if (attempts >= maxAttempts) endGame('기회를 모두 사용했습니다.');
        else statusEl.textContent = `${attempts}/${maxAttempts}번째 시도입니다.`;

        currentGuess = [];
        buildSlots();
    };

    const newGame = () => {
        secret = Array.from({ length: 4 }, () => Math.floor(Math.random() * colors.length));
        currentGuess = [];
        attempts = 0;
        gameOver = false;
        statusEl.textContent = '10번 안에 숨은 조합을 맞혀보세요.';
        historyEl.innerHTML = '';
        secretRevealEl.textContent = '';
        buildSlots();
    };

    submitBtn.addEventListener('click', submitGuess);
    clearBtn.addEventListener('click', clearGuess);
    newGameBtn.addEventListener('click', newGame);

    buildPalette();
    newGame();
})();
