(() => {
    const size = 4;
    const totalTiles = size * size;

    const boardEl = document.getElementById("fifteen-board");
    const statusEl = document.getElementById("fifteen-status");
    const movesEl = document.getElementById("fifteen-moves");
    const shuffleBtn = document.getElementById("fifteen-shuffle");

    if (!boardEl || !statusEl || !movesEl || !shuffleBtn) {
        return;
    }

    let board = [];
    let moves = 0;
    let solved = false;

    function createSolvedBoard() {
        return Array.from({ length: totalTiles }, (_, index) => (index + 1) % totalTiles);
    }

    function setStatus(message) {
        statusEl.textContent = message;
    }

    function getNeighbors(index) {
        const row = Math.floor(index / size);
        const col = index % size;
        const neighbors = [];
        if (row > 0) neighbors.push(index - size);
        if (row < size - 1) neighbors.push(index + size);
        if (col > 0) neighbors.push(index - 1);
        if (col < size - 1) neighbors.push(index + 1);
        return neighbors;
    }

    function swap(indexA, indexB) {
        const temp = board[indexA];
        board[indexA] = board[indexB];
        board[indexB] = temp;
    }

    function checkSolved() {
        for (let index = 0; index < totalTiles - 1; index += 1) {
            if (board[index] !== index + 1) {
                return false;
            }
        }
        return board[totalTiles - 1] === 0;
    }

    function render() {
        boardEl.innerHTML = "";
        board.forEach((value, index) => {
            const button = document.createElement("button");
            button.type = "button";
            button.className = "fifteen-cell";
            button.dataset.index = String(index);

            if (value === 0) {
                button.classList.add("blank");
                button.disabled = true;
                button.setAttribute("aria-label", "빈칸");
            } else {
                button.textContent = String(value);
                button.setAttribute("aria-label", `${value}번 타일`);
                button.disabled = solved;
            }

            button.addEventListener("click", () => handleMove(index));
            boardEl.appendChild(button);
        });

        movesEl.textContent = `이동 횟수: ${moves}`;
    }

    function handleMove(index) {
        if (solved) {
            return;
        }

        const blankIndex = board.indexOf(0);
        if (!getNeighbors(blankIndex).includes(index)) {
            return;
        }

        swap(blankIndex, index);
        moves += 1;
        solved = checkSolved();
        if (solved) {
            setStatus(`완성했습니다. 총 ${moves}번 이동했습니다.`);
        }
        render();
    }

    function shuffleBoard() {
        board = createSolvedBoard();
        let blankIndex = board.indexOf(0);

        for (let i = 0; i < 160; i += 1) {
            const neighbors = getNeighbors(blankIndex);
            const choice = neighbors[Math.floor(Math.random() * neighbors.length)];
            swap(blankIndex, choice);
            blankIndex = choice;
        }

        moves = 0;
        solved = false;
        setStatus("타일을 순서대로 정렬하세요.");
        render();
    }

    shuffleBtn.addEventListener("click", shuffleBoard);
    shuffleBoard();
})();
