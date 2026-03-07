(() => {
    const size = 5;
    const boardEl = document.getElementById('lightsout-board');
    const statusEl = document.getElementById('lightsout-status');
    const newBtn = document.getElementById('lightsout-new');

    if (!boardEl || !statusEl || !newBtn) return;

    let board = Array.from({ length: size }, () => Array(size).fill(false));
    let moves = 0;
    let won = false;

    const inBounds = (row, col) => row >= 0 && row < size && col >= 0 && col < size;

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const toggleCell = (row, col) => {
        if (!inBounds(row, col)) return;
        board[row][col] = !board[row][col];
    };

    const render = () => {
        const buttons = boardEl.querySelectorAll('.lightsout-cell');
        buttons.forEach((button, index) => {
            const row = Math.floor(index / size);
            const col = index % size;
            button.classList.toggle('on', board[row][col]);
        });
    };

    const checkWin = () => {
        if (board.every((row) => row.every((cell) => !cell))) {
            won = true;
            setStatus(`${moves}번 만에 클리어!`);
        } else {
            setStatus(`이동 횟수: ${moves}`);
        }
    };

    const applyMove = (row, col) => {
        if (won) return;
        toggleCell(row, col);
        toggleCell(row - 1, col);
        toggleCell(row + 1, col);
        toggleCell(row, col - 1);
        toggleCell(row, col + 1);
        moves += 1;
        render();
        checkWin();
    };

    const scramble = () => {
        board = Array.from({ length: size }, () => Array(size).fill(false));
        moves = 0;
        won = false;
        const taps = 12 + Math.floor(Math.random() * 6);
        for (let i = 0; i < taps; i += 1) {
            const row = Math.floor(Math.random() * size);
            const col = Math.floor(Math.random() * size);
            toggleCell(row, col);
            toggleCell(row - 1, col);
            toggleCell(row + 1, col);
            toggleCell(row, col - 1);
            toggleCell(row, col + 1);
        }
        render();
        setStatus('이동 횟수: 0');
    };

    const buildBoard = () => {
        boardEl.innerHTML = '';
        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const button = document.createElement('button');
                button.className = 'lightsout-cell';
                button.type = 'button';
                button.addEventListener('click', () => applyMove(row, col));
                boardEl.appendChild(button);
            }
        }
    };

    buildBoard();
    scramble();
    newBtn.addEventListener('click', scramble);
})();
