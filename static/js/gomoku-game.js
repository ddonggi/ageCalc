(() => {
    const size = 15;
    const boardEl = document.getElementById('gomoku-board');
    const statusEl = document.getElementById('gomoku-status');
    const resetBtn = document.getElementById('gomoku-reset');

    if (!boardEl || !statusEl || !resetBtn) return;

    let board = [];
    let currentPlayer = 'Black';
    let gameOver = false;
    let moves = 0;

    const updateStatus = (text) => {
        statusEl.textContent = text;
    };

    const stoneFor = (player) => (player === 'Black' ? '●' : '○');

    const inBounds = (row, col) => row >= 0 && row < size && col >= 0 && col < size;

    const countLine = (row, col, dr, dc, player) => {
        let count = 0;
        let r = row;
        let c = col;

        while (inBounds(r, c) && board[r][c] === player) {
            count += 1;
            r += dr;
            c += dc;
        }

        return count;
    };

    const checkWin = (row, col, player) => {
        const directions = [
            [1, 0],
            [0, 1],
            [1, 1],
            [1, -1]
        ];

        return directions.some(([dr, dc]) => {
            const forward = countLine(row, col, dr, dc, player);
            const backward = countLine(row, col, -dr, -dc, player);
            return forward + backward - 1 >= 5;
        });
    };

    const handleMove = (event) => {
        if (gameOver) return;

        const cell = event.currentTarget;
        const row = Number(cell.dataset.row);
        const col = Number(cell.dataset.col);
        if (board[row][col]) return;

        board[row][col] = currentPlayer;
        cell.textContent = stoneFor(currentPlayer);
        cell.disabled = true;
        moves += 1;

        if (checkWin(row, col, currentPlayer)) {
            gameOver = true;
            updateStatus(`${currentPlayer === 'Black' ? '흑' : '백'} 승리!`);
            return;
        }

        if (moves === size * size) {
            gameOver = true;
            updateStatus('무승부입니다.');
            return;
        }

        currentPlayer = currentPlayer === 'Black' ? 'White' : 'Black';
        updateStatus(`${currentPlayer === 'Black' ? '흑' : '백'} 차례입니다.`);
    };

    const createBoard = () => {
        boardEl.innerHTML = '';
        board = Array.from({ length: size }, () => Array(size).fill(''));

        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const cell = document.createElement('button');
                cell.type = 'button';
                cell.className = 'gomoku-cell';
                cell.dataset.row = String(row);
                cell.dataset.col = String(col);
                cell.setAttribute('aria-label', `${row + 1}행 ${col + 1}열`);
                cell.addEventListener('click', handleMove);
                boardEl.appendChild(cell);
            }
        }
    };

    const resetGame = () => {
        currentPlayer = 'Black';
        gameOver = false;
        moves = 0;
        updateStatus('흑 차례입니다.');
        createBoard();
    };

    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
