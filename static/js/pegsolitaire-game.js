(() => {
    const boardEl = document.getElementById("peg-board");
    const statusEl = document.getElementById("peg-status");
    const movesEl = document.getElementById("peg-moves");
    const resetBtn = document.getElementById("peg-reset");

    if (!boardEl || !statusEl || !movesEl || !resetBtn) {
        return;
    }

    const size = 7;
    const invalid = -1;
    const peg = 1;
    const empty = 0;

    let board = [];
    let selected = null;
    let moves = 0;

    function setStatus(message) {
        statusEl.textContent = message;
    }

    function isInvalidCell(row, col) {
        const outer = row < 2 || row > 4;
        const side = col < 2 || col > 4;
        return outer && side;
    }

    function countPegs() {
        return board.flat().filter((cell) => cell === peg).length;
    }

    function hasMoves() {
        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                if (board[row][col] !== peg) {
                    continue;
                }

                const candidates = [
                    { row: row + 2, col },
                    { row: row - 2, col },
                    { row, col: col + 2 },
                    { row, col: col - 2 },
                ];

                for (const target of candidates) {
                    if (target.row < 0 || target.row >= size || target.col < 0 || target.col >= size) {
                        continue;
                    }
                    const midRow = (row + target.row) / 2;
                    const midCol = (col + target.col) / 2;
                    if (board[target.row][target.col] === empty && board[midRow][midCol] === peg) {
                        return true;
                    }
                }
            }
        }
        return false;
    }

    function render() {
        boardEl.innerHTML = "";

        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const button = document.createElement("button");
                button.type = "button";
                button.className = "peg-hole";
                button.dataset.row = String(row);
                button.dataset.col = String(col);

                const cell = board[row][col];
                if (cell === invalid) {
                    button.classList.add("invalid");
                } else {
                    if (cell === peg) {
                        button.classList.add("peg");
                    } else {
                        button.classList.add("empty");
                    }
                    if (selected && selected.row === row && selected.col === col) {
                        button.classList.add("selected");
                    }
                    button.setAttribute("aria-label", `${row + 1}행 ${col + 1}열`);
                    button.addEventListener("click", handleClick);
                }

                boardEl.appendChild(button);
            }
        }

        movesEl.textContent = `이동 횟수: ${moves}`;
    }

    function tryMove(from, to) {
        const dr = to.row - from.row;
        const dc = to.col - from.col;
        const isOrthogonal = (Math.abs(dr) === 2 && dc === 0) || (Math.abs(dc) === 2 && dr === 0);
        if (!isOrthogonal) {
            return false;
        }

        const midRow = from.row + dr / 2;
        const midCol = from.col + dc / 2;
        if (board[midRow][midCol] !== peg || board[to.row][to.col] !== empty) {
            return false;
        }

        board[from.row][from.col] = empty;
        board[midRow][midCol] = empty;
        board[to.row][to.col] = peg;
        moves += 1;

        if (countPegs() === 1) {
            setStatus(`성공했습니다. ${moves}번 만에 핀 하나만 남겼습니다.`);
        } else if (!hasMoves()) {
            setStatus("더 이상 움직일 수 없습니다. 다시 시작해 보세요.");
        } else {
            setStatus("좋습니다. 다음 점프를 이어가세요.");
        }

        return true;
    }

    function handleClick(event) {
        const row = Number(event.currentTarget.dataset.row);
        const col = Number(event.currentTarget.dataset.col);
        const cell = board[row][col];

        if (cell === peg) {
            selected = { row, col };
            setStatus("두 칸 떨어진 빈 구멍을 선택하세요.");
            render();
            return;
        }

        if (cell === empty && selected) {
            if (tryMove(selected, { row, col })) {
                selected = null;
                render();
                return;
            }
            setStatus("잘못된 이동입니다. 핀 하나를 넘어 직선으로 이동해야 합니다.");
            return;
        }

        if (cell === empty) {
            setStatus("먼저 이동할 핀을 선택하세요.");
        }
    }

    function resetGame() {
        board = Array.from({ length: size }, (_, row) =>
            Array.from({ length: size }, (_, col) => (isInvalidCell(row, col) ? invalid : peg))
        );
        board[3][3] = empty;
        selected = null;
        moves = 0;
        setStatus("핀을 선택한 뒤 두 칸 떨어진 빈 구멍을 선택하세요.");
        render();
    }

    resetBtn.addEventListener("click", resetGame);
    resetGame();
})();
