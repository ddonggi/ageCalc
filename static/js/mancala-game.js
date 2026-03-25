(() => {
    const statusEl = document.getElementById('mancala-status');
    const rowP1 = document.getElementById('mancala-row-p1');
    const rowP2 = document.getElementById('mancala-row-p2');
    const storeP1 = document.getElementById('mancala-store-p1');
    const storeP2 = document.getElementById('mancala-store-p2');
    const resetBtn = document.getElementById('mancala-reset');
    if (!statusEl || !rowP1 || !rowP2 || !storeP1 || !storeP2 || !resetBtn) return;

    const P1_PITS = [0, 1, 2, 3, 4, 5];
    const P2_PITS = [7, 8, 9, 10, 11, 12];
    const P1_STORE = 6;
    const P2_STORE = 13;

    let board = [];
    let currentPlayer = 1;
    let gameOver = false;
    let pits = new Map();

    const updateStatus = (message) => {
        statusEl.textContent = message;
    };

    const isPlayersPit = (index, player) => player === 1 ? P1_PITS.includes(index) : P2_PITS.includes(index);
    const checkGameEnd = () => P1_PITS.every((i) => board[i] === 0) || P2_PITS.every((i) => board[i] === 0);

    const render = () => {
        pits.forEach((btn, index) => {
            btn.textContent = String(board[index]);
            const enabled = !gameOver && isPlayersPit(index, currentPlayer) && board[index] > 0;
            btn.disabled = !enabled;
        });
        storeP1.textContent = String(board[P1_STORE]);
        storeP2.textContent = String(board[P2_STORE]);
    };

    const finalizeGame = () => {
        const p1Remaining = P1_PITS.reduce((sum, i) => sum + board[i], 0);
        const p2Remaining = P2_PITS.reduce((sum, i) => sum + board[i], 0);
        P1_PITS.forEach((i) => { board[i] = 0; });
        P2_PITS.forEach((i) => { board[i] = 0; });
        board[P1_STORE] += p1Remaining;
        board[P2_STORE] += p2Remaining;
        gameOver = true;
        render();

        if (board[P1_STORE] > board[P2_STORE]) updateStatus('플레이어 1 승리!');
        else if (board[P2_STORE] > board[P1_STORE]) updateStatus('플레이어 2 승리!');
        else updateStatus('무승부입니다.');
    };

    const handleMove = (index) => {
        if (gameOver || !isPlayersPit(index, currentPlayer) || board[index] === 0) return;

        let stones = board[index];
        board[index] = 0;
        let cursor = index;

        while (stones > 0) {
            cursor = (cursor + 1) % 14;
            if (currentPlayer === 1 && cursor === P2_STORE) continue;
            if (currentPlayer === 2 && cursor === P1_STORE) continue;
            board[cursor] += 1;
            stones -= 1;
        }

        const landedInStore = (currentPlayer === 1 && cursor === P1_STORE) || (currentPlayer === 2 && cursor === P2_STORE);

        if (!landedInStore && isPlayersPit(cursor, currentPlayer) && board[cursor] === 1) {
            const opposite = 12 - cursor;
            if (board[opposite] > 0) {
                const captured = board[opposite] + board[cursor];
                board[opposite] = 0;
                board[cursor] = 0;
                const storeIndex = currentPlayer === 1 ? P1_STORE : P2_STORE;
                board[storeIndex] += captured;
            }
        }

        if (checkGameEnd()) {
            finalizeGame();
            return;
        }

        if (landedInStore) updateStatus(`플레이어 ${currentPlayer}가 한 번 더 둡니다.`);
        else {
            currentPlayer = currentPlayer === 1 ? 2 : 1;
            updateStatus(`플레이어 ${currentPlayer} 차례입니다.`);
        }

        render();
    };

    const buildBoard = () => {
        rowP1.innerHTML = '';
        rowP2.innerHTML = '';
        pits.clear();

        P2_PITS.slice().reverse().forEach((index) => {
            const btn = document.createElement('button');
            btn.className = 'mancala-pit';
            btn.dataset.index = String(index);
            btn.setAttribute('aria-label', `플레이어 2 구멍 ${12 - index + 1}`);
            rowP2.appendChild(btn);
            pits.set(index, btn);
        });

        P1_PITS.forEach((index) => {
            const btn = document.createElement('button');
            btn.className = 'mancala-pit';
            btn.dataset.index = String(index);
            btn.setAttribute('aria-label', `플레이어 1 구멍 ${index + 1}`);
            rowP1.appendChild(btn);
            pits.set(index, btn);
        });

        pits.forEach((btn, index) => {
            btn.addEventListener('click', () => handleMove(index));
        });
    };

    const resetGame = () => {
        board = Array(14).fill(4);
        board[P1_STORE] = 0;
        board[P2_STORE] = 0;
        currentPlayer = 1;
        gameOver = false;
        updateStatus('플레이어 1이 먼저 시작합니다.');
        render();
    };

    buildBoard();
    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
