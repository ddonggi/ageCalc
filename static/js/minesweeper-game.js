(() => {
    const boardEl = document.getElementById('minesweeper-board');
    const statusEl = document.getElementById('minesweeper-status');
    const resetBtn = document.getElementById('minesweeper-reset');

    if (!boardEl || !statusEl || !resetBtn) return;

    const size = 8;
    const minesCount = 10;

    let cells = [];
    let gameOver = false;
    let revealedCount = 0;

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const indexFrom = (row, col) => row * size + col;

    const neighbors = (row, col) => {
        const list = [];
        for (let r = row - 1; r <= row + 1; r += 1) {
            for (let c = col - 1; c <= col + 1; c += 1) {
                if (r === row && c === col) continue;
                if (r < 0 || c < 0 || r >= size || c >= size) continue;
                list.push({ row: r, col: c, index: indexFrom(r, c) });
            }
        }
        return list;
    };

    const placeMines = () => {
        const positions = new Set();
        while (positions.size < minesCount) {
            positions.add(Math.floor(Math.random() * size * size));
        }
        positions.forEach((pos) => {
            cells[pos].mine = true;
        });
    };

    const computeCounts = () => {
        cells.forEach((cell) => {
            if (cell.mine) return;
            cell.count = neighbors(cell.row, cell.col).reduce((sum, neighbor) => {
                return sum + (cells[neighbor.index].mine ? 1 : 0);
            }, 0);
        });
    };

    const endGame = (won) => {
        gameOver = true;
        if (won) {
            setStatus('지뢰밭 클리어 성공!');
            return;
        }

        setStatus('펑! 다시 도전해보세요.');
        cells.forEach((cell) => {
            if (cell.mine) {
                cell.el.textContent = '*';
                cell.el.classList.add('revealed');
            }
        });
    };

    const checkWin = () => {
        const safeTiles = size * size - minesCount;
        if (revealedCount >= safeTiles) endGame(true);
    };

    const revealCell = (index) => {
        const cell = cells[index];
        if (cell.revealed || cell.flagged || gameOver) return;

        cell.revealed = true;
        revealedCount += 1;
        cell.el.classList.add('revealed');

        if (cell.mine) {
            cell.el.textContent = '*';
            endGame(false);
            return;
        }

        cell.el.textContent = cell.count ? String(cell.count) : '';
        if (cell.count === 0) {
            neighbors(cell.row, cell.col).forEach((neighbor) => revealCell(neighbor.index));
        }

        checkWin();
    };

    const toggleFlag = (index) => {
        const cell = cells[index];
        if (cell.revealed || gameOver) return;
        cell.flagged = !cell.flagged;
        cell.el.classList.toggle('flagged', cell.flagged);
        cell.el.textContent = cell.flagged ? '!' : '';
    };

    const buildBoard = () => {
        boardEl.innerHTML = '';
        cells = [];
        gameOver = false;
        revealedCount = 0;

        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const index = indexFrom(row, col);
                const button = document.createElement('button');
                button.className = 'minesweeper-cell';
                button.type = 'button';

                button.addEventListener('click', () => revealCell(index));
                button.addEventListener('contextmenu', (event) => {
                    event.preventDefault();
                    toggleFlag(index);
                });

                boardEl.appendChild(button);
                cells.push({
                    row,
                    col,
                    mine: false,
                    count: 0,
                    revealed: false,
                    flagged: false,
                    el: button
                });
            }
        }

        placeMines();
        computeCounts();
        setStatus('안전한 칸을 모두 찾으세요.');
    };

    resetBtn.addEventListener('click', buildBoard);
    buildBoard();
})();
