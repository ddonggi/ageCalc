(() => {
    const pileEl = document.getElementById('nim-pile');
    const statusEl = document.getElementById('nim-status');
    const resetBtn = document.getElementById('nim-reset');
    const takeButtons = Array.from(document.querySelectorAll('button[data-take]'));

    if (!pileEl || !statusEl || !resetBtn || takeButtons.length !== 3) return;

    let stones = 21;
    let gameOver = false;

    const updatePile = () => {
        pileEl.textContent = `남은 돌: ${stones}`;
    };

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const endGame = (winner) => {
        gameOver = true;
        setStatus(`${winner}가 마지막 돌을 가져갔습니다!`);
    };

    const cpuTurn = () => {
        if (gameOver) return;
        const maxTake = Math.min(3, stones);
        const take = Math.floor(Math.random() * maxTake) + 1;
        stones -= take;
        updatePile();

        if (stones === 0) {
            endGame('CPU');
            return;
        }

        setStatus(`CPU가 ${take}개 가져갔습니다. 내 차례입니다.`);
    };

    const handlePlayerMove = (take) => {
        if (gameOver) return;
        if (take > stones) {
            setStatus('남은 돌보다 많이 가져갈 수 없습니다.');
            return;
        }

        stones -= take;
        updatePile();

        if (stones === 0) {
            endGame('플레이어');
            return;
        }

        setStatus(`내가 ${take}개 가져갔습니다. CPU 차례...`);
        window.setTimeout(cpuTurn, 350);
    };

    const resetGame = () => {
        stones = 21;
        gameOver = false;
        updatePile();
        setStatus('내 차례입니다.');
    };

    takeButtons.forEach((button) => {
        button.addEventListener('click', () => {
            handlePlayerMove(Number(button.dataset.take));
        });
    });

    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
