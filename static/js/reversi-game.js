(() => {
    const boardEl = document.getElementById('reversi-board');
    const statusEl = document.getElementById('reversi-status');
    const resetBtn = document.getElementById('reversi-reset');

    if (!boardEl || !statusEl || !resetBtn) return;

    const size = 8;
    const directions = [
        [-1, -1], [-1, 0], [-1, 1],
        [0, -1],           [0, 1],
        [1, -1],  [1, 0],  [1, 1]
    ];

    let board = [];
    let currentPlayer = 'B';
    let gameOver = false;

    const indexToRowCol = (index) => [Math.floor(index / size), index % size];
    const rowColToIndex = (row, col) => row * size + col;
    const inBounds = (row, col) => row >= 0 && row < size && col >= 0 && col < size;

    const updateStatus = (message) => {
        statusEl.textContent = message;
    };

    const getFlips = (index, player) => {
        if (board[index]) return [];

        const opponent = player === 'B' ? 'W' : 'B';
        const [startRow, startCol] = indexToRowCol(index);
        const flips = [];

        directions.forEach(([dr, dc]) => {
            let row = startRow + dr;
            let col = startCol + dc;
            const line = [];

            while (inBounds(row, col)) {
                const piece = board[rowColToIndex(row, col)];
                if (piece === opponent) {
                    line.push(rowColToIndex(row, col));
                } else if (piece === player) {
                    if (line.length) flips.push(...line);
                    return;
                } else {
                    return;
                }
                row += dr;
                col += dc;
            }
        });

        return flips;
    };

    const hasValidMove = (player) => board.some((cell, idx) => !cell && getFlips(idx, player).length);

    const countPieces = () => board.reduce((acc, piece) => {
        if (piece === 'B') acc.black += 1;
        if (piece === 'W') acc.white += 1;
        return acc;
    }, { black: 0, white: 0 });

    const renderBoard = () => {
        const cells = boardEl.querySelectorAll('.reversi-cell');
        cells.forEach((cell, index) => {
            cell.textContent = board[index] || '';
        });
    };

    const endGame = () => {
        const { black, white } = countPieces();
        if (black === white) {
            updateStatus(`게임 종료. 무승부 ${black}-${white}`);
        } else if (black > white) {
            updateStatus(`게임 종료. 흑 승리 ${black}-${white}`);
        } else {
            updateStatus(`게임 종료. 백 승리 ${white}-${black}`);
        }
        gameOver = true;
    };

    const switchPlayer = () => {
        currentPlayer = currentPlayer === 'B' ? 'W' : 'B';
    };

    const handleMove = (index) => {
        if (gameOver) return;

        const flips = getFlips(index, currentPlayer);
        if (!flips.length) {
            updateStatus('유효하지 않은 위치입니다.');
            return;
        }

        board[index] = currentPlayer;
        flips.forEach((flipIndex) => {
            board[flipIndex] = currentPlayer;
        });

        renderBoard();
        switchPlayer();

        if (!hasValidMove(currentPlayer)) {
            switchPlayer();
            if (!hasValidMove(currentPlayer)) {
                endGame();
                return;
            }
            updateStatus(`${currentPlayer === 'B' ? '흑' : '백'}이 다시 둡니다. 상대가 둘 곳이 없습니다.`);
            return;
        }

        updateStatus(`${currentPlayer === 'B' ? '흑' : '백'} 차례입니다.`);
    };

    const setupBoard = () => {
        board = Array(size * size).fill('');
        const mid = size / 2;
        board[rowColToIndex(mid - 1, mid - 1)] = 'W';
        board[rowColToIndex(mid, mid)] = 'W';
        board[rowColToIndex(mid - 1, mid)] = 'B';
        board[rowColToIndex(mid, mid - 1)] = 'B';

        boardEl.innerHTML = '';
        for (let i = 0; i < size * size; i += 1) {
            const button = document.createElement('button');
            button.className = 'reversi-cell';
            button.type = 'button';
            button.dataset.index = String(i);
            const row = Math.floor(i / size) + 1;
            const col = (i % size) + 1;
            button.setAttribute('aria-label', `${row}행 ${col}열`);
            button.addEventListener('click', () => handleMove(i));
            boardEl.appendChild(button);
        }

        renderBoard();
        currentPlayer = 'B';
        gameOver = false;
        updateStatus('흑 차례입니다.');
    };

    resetBtn.addEventListener('click', setupBoard);
    setupBoard();
})();
