(() => {
    const statusEl = document.getElementById('ttt-status');
    const cells = Array.from(document.querySelectorAll('.ttt-cell'));
    const resetBtn = document.getElementById('ttt-reset');
    const swapBtn = document.getElementById('ttt-swap');

    if (!statusEl || cells.length !== 9 || !resetBtn || !swapBtn) return;

    let board = Array(9).fill('');
    let currentPlayer = 'X';
    let starter = 'X';
    let gameOver = false;

    const lines = [
        [0, 1, 2],
        [3, 4, 5],
        [6, 7, 8],
        [0, 3, 6],
        [1, 4, 7],
        [2, 5, 8],
        [0, 4, 8],
        [2, 4, 6]
    ];

    const updateStatus = (message) => {
        statusEl.textContent = message;
    };

    const checkWinner = () => {
        for (const [a, b, c] of lines) {
            if (board[a] && board[a] === board[b] && board[a] === board[c]) {
                return board[a];
            }
        }
        if (board.every((cell) => cell)) return 'draw';
        return null;
    };

    const updateCell = (index, value) => {
        const cell = cells[index];
        cell.textContent = value;
        cell.setAttribute('aria-label', `${index + 1}번 칸 ${value || '비어 있음'}`);
    };

    const handleMove = (index) => {
        if (gameOver || board[index]) return;

        board[index] = currentPlayer;
        updateCell(index, currentPlayer);

        const outcome = checkWinner();
        if (outcome) {
            gameOver = true;
            if (outcome === 'draw') {
                updateStatus('무승부! 다시 시작 버튼으로 새 게임을 시작하세요.');
            } else {
                updateStatus(`플레이어 ${outcome} 승리!`);
            }
            return;
        }

        currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
        updateStatus(`플레이어 ${currentPlayer} 차례`);
    };

    const resetGame = () => {
        board = Array(9).fill('');
        gameOver = false;
        currentPlayer = starter;
        cells.forEach((_, idx) => updateCell(idx, ''));
        updateStatus(`플레이어 ${currentPlayer} 차례`);
    };

    const swapStarter = () => {
        starter = starter === 'X' ? 'O' : 'X';
        resetGame();
    };

    cells.forEach((cell) => {
        cell.addEventListener('click', () => {
            handleMove(Number(cell.dataset.index));
        });
    });

    resetBtn.addEventListener('click', resetGame);
    swapBtn.addEventListener('click', swapStarter);

    resetGame();
})();
