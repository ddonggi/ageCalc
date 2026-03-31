(() => {
    const size = 5;
    const shipCount = 3;
    const shipLength = 2;

    const gridEl = document.getElementById("bs-grid");
    const statusEl = document.getElementById("bs-status");
    const shotsEl = document.getElementById("bs-shots");
    const hitsEl = document.getElementById("bs-hits");
    const resetBtn = document.getElementById("bs-reset");

    if (!gridEl || !statusEl || !shotsEl || !hitsEl || !resetBtn) {
        return;
    }

    let ships = [];
    let hits = new Set();
    let misses = new Set();
    let shots = 0;
    let gameOver = false;

    function setStatus(message) {
        statusEl.textContent = message;
    }

    function toIndex(row, col) {
        return row * size + col;
    }

    function placeShips() {
        ships = [];
        const occupied = new Set();
        let attempts = 0;

        while (ships.length < shipCount && attempts < 500) {
            attempts += 1;
            const horizontal = Math.random() < 0.5;
            const startRow = Math.floor(Math.random() * size);
            const startCol = Math.floor(Math.random() * size);
            const cells = [];

            for (let i = 0; i < shipLength; i += 1) {
                const row = horizontal ? startRow : startRow + i;
                const col = horizontal ? startCol + i : startCol;
                if (row >= size || col >= size) {
                    cells.length = 0;
                    break;
                }
                cells.push(toIndex(row, col));
            }

            if (!cells.length || cells.some((cell) => occupied.has(cell))) {
                continue;
            }

            cells.forEach((cell) => occupied.add(cell));
            ships.push(cells);
        }
    }

    function isHit(index) {
        return ships.some((ship) => ship.includes(index));
    }

    function totalHitCount() {
        return hits.size;
    }

    function allShipsSunk() {
        return ships.every((ship) => ship.every((cell) => hits.has(cell)));
    }

    function render() {
        gridEl.innerHTML = "";

        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const index = toIndex(row, col);
                const button = document.createElement("button");
                button.type = "button";
                button.className = "bs-cell";
                button.setAttribute("role", "gridcell");
                button.dataset.index = String(index);
                button.setAttribute("aria-label", `${row + 1}행 ${col + 1}열`);

                if (hits.has(index)) {
                    button.classList.add("hit");
                    button.textContent = "명중";
                    button.disabled = true;
                } else if (misses.has(index)) {
                    button.classList.add("miss");
                    button.textContent = "빗나감";
                    button.disabled = true;
                }

                button.addEventListener("click", handleShot);
                gridEl.appendChild(button);
            }
        }

        shotsEl.textContent = `공격 횟수: ${shots}`;
        hitsEl.textContent = `명중: ${totalHitCount()} / ${shipCount * shipLength}`;
    }

    function handleShot(event) {
        if (gameOver) {
            setStatus("이미 모든 함선을 침몰시켰습니다. 다시 시작해 보세요.");
            return;
        }

        const index = Number(event.currentTarget.dataset.index);
        if (hits.has(index) || misses.has(index)) {
            setStatus("이미 공격한 칸입니다.");
            return;
        }

        shots += 1;
        if (isHit(index)) {
            hits.add(index);
            setStatus("명중했습니다.");
        } else {
            misses.add(index);
            setStatus("빗나갔습니다.");
        }

        if (allShipsSunk()) {
            gameOver = true;
            setStatus(`모든 함선을 ${shots}번 만에 침몰시켰습니다.`);
        }

        render();
    }

    function resetGame() {
        hits = new Set();
        misses = new Set();
        shots = 0;
        gameOver = false;
        placeShips();
        setStatus("숨겨진 함선 3척을 찾아보세요.");
        render();
    }

    resetBtn.addEventListener("click", resetGame);
    resetGame();
})();
