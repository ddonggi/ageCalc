(() => {
    const words = [
        'COMET',
        'ORBIT',
        'ROCKET',
        'GALAXY',
        'ASTRAL',
        'PILOT',
        'PLANET',
        'METEOR',
        'COSMOS',
        'VOYAGE'
    ];

    const wordEl = document.getElementById('hangman-word');
    const statusEl = document.getElementById('hangman-status');
    const guessesEl = document.getElementById('hangman-guesses');
    const form = document.getElementById('hangman-form');
    const input = document.getElementById('hangman-input');
    const resetBtn = document.getElementById('hangman-reset');

    if (!wordEl || !statusEl || !guessesEl || !form || !input || !resetBtn) return;

    let secret = '';
    let revealed = new Set();
    let wrong = new Set();
    let remaining = 6;
    let gameOver = false;

    const pickWord = () => {
        secret = words[Math.floor(Math.random() * words.length)];
    };

    const renderWord = () => {
        const text = secret
            .split('')
            .map((ch) => (revealed.has(ch) ? ch : '_'))
            .join(' ');
        wordEl.textContent = text;
    };

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const renderGuesses = () => {
        const wrongList = Array.from(wrong).sort().join(', ');
        guessesEl.textContent = `오답 (${remaining}회 남음): ${wrongList || '없음'}`;
    };

    const updateControls = () => {
        input.disabled = gameOver;
    };

    const checkWin = () => {
        for (const ch of secret) {
            if (!revealed.has(ch)) return false;
        }
        return true;
    };

    const resetGame = () => {
        pickWord();
        revealed = new Set();
        wrong = new Set();
        remaining = 6;
        gameOver = false;
        renderWord();
        setStatus('알파벳을 입력해 단어를 맞춰보세요.');
        renderGuesses();
        updateControls();
        input.value = '';
        input.focus();
    };

    const handleGuess = (letter) => {
        if (gameOver) return;
        if (!/^[A-Z]$/.test(letter)) {
            setStatus('A-Z 알파벳 한 글자만 입력할 수 있습니다.');
            return;
        }

        if (revealed.has(letter) || wrong.has(letter)) {
            setStatus('이미 시도한 글자입니다.');
            return;
        }

        if (secret.includes(letter)) {
            revealed.add(letter);
            renderWord();
            if (checkWin()) {
                gameOver = true;
                setStatus(`정답! 단어는 ${secret} 입니다.`);
            } else {
                setStatus('정답 글자입니다. 계속 진행하세요.');
            }
        } else {
            wrong.add(letter);
            remaining -= 1;
            if (remaining === 0) {
                gameOver = true;
                setStatus(`게임 종료! 정답은 ${secret} 입니다.`);
            } else {
                setStatus('틀렸습니다. 다른 글자를 시도하세요.');
            }
        }

        renderGuesses();
        updateControls();
    };

    form.addEventListener('submit', (event) => {
        event.preventDefault();
        const letter = input.value.trim().toUpperCase();
        input.value = '';
        handleGuess(letter);
    });

    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
