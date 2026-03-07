(() => {
    const rows = 6;
    const cols = 7;
    const boardEl = document.getElementById('connect4-board');
    const statusEl = document.getElementById('connect4-status');
    const resetBtn = document.getElementById('connect4-reset');

    if (!boardEl || !statusEl || !resetBtn) return;

    let board = [];
    let cells = [];
    let currentPlayer = 'R';
    let gameOver = false;

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const buildBoard = () => {
        boardEl.innerHTML = '';
        board = Array.from({ length: rows }, () => Array(cols).fill(''));
        cells = Array.from({ length: rows }, () => Array(cols).fill(null));

        for (let r = 0; r < rows; r += 1) {
            for (let c = 0; c < cols; c += 1) {
                const cell = document.createElement('button');
                cell.className = 'connect4-cell';
                cell.type = 'button';
                cell.dataset.row = String(r);
                cell.dataset.col = String(c);
                boardEl.appendChild(cell);
                cells[r][c] = cell;
            }
        }
    };

    const findOpenRow = (col) => {
        for (let r = rows - 1; r >= 0; r -= 1) {
            if (!board[r][col]) return r;
        }
        return -1;
    };

    const countDirection = (row, col, dr, dc) => {
        const player = board[row][col];
        let count = 0;
        let r = row;
        let c = col;
        while (r >= 0 && r < rows && c >= 0 && c < cols && board[r][c] === player) {
            count += 1;
            r += dr;
            c += dc;
        }
        return count;
    };

    const checkWin = (row, col) => {
        const directions = [[0, 1], [1, 0], [1, 1], [1, -1]];
        return directions.some(([dr, dc]) => {
            const forward = countDirection(row, col, dr, dc);
            const backward = countDirection(row, col, -dr, -dc);
            return forward + backward - 1 >= 4;
        });
    };

    const handleMove = (col) => {
        if (gameOver) return;
        const row = findOpenRow(col);
        if (row === -1) return;

        board[row][col] = currentPlayer;
        cells[row][col].dataset.value = currentPlayer;

        if (checkWin(row, col)) {
            gameOver = true;
            setStatus(currentPlayer === 'R' ? '빨강 승리!' : '노랑 승리!');
            return;
        }

        if (board.every((line) => line.every((cell) => cell))) {
            gameOver = true;
            setStatus('무승부!');
            return;
        }

        currentPlayer = currentPlayer === 'R' ? 'Y' : 'R';
        setStatus(currentPlayer === 'R' ? '빨강 차례' : '노랑 차례');
    };

    const resetGame = () => {
        currentPlayer = 'R';
        gameOver = false;
        buildBoard();
        setStatus('빨강 차례');
    };

    boardEl.addEventListener('click', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement)) return;
        const cell = target.closest('.connect4-cell');
        if (!cell) return;
        handleMove(Number(cell.dataset.col));
    });

    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
