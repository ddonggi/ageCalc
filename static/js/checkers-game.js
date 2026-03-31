(() => {
    const boardEl = document.getElementById("checkers-board");
    const statusEl = document.getElementById("checkers-status");
    const resetBtn = document.getElementById("checkers-reset");

    if (!boardEl || !statusEl || !resetBtn) {
        return;
    }

    const size = 8;
    const playerName = {
        red: "빨강",
        black: "검정",
    };

    let board = [];
    let currentPlayer = "black";
    let selected = null;
    let forcedChain = null;
    let gameOver = false;

    function inBounds(row, col) {
        return row >= 0 && row < size && col >= 0 && col < size;
    }

    function pieceAt(row, col) {
        return board[row][col];
    }

    function ownerOf(piece) {
        if (!piece) {
            return null;
        }
        return piece.toLowerCase() === "r" ? "red" : "black";
    }

    function isKing(piece) {
        return piece === "R" || piece === "B";
    }

    function setStatus(message) {
        statusEl.textContent = message;
    }

    function initBoard() {
        board = Array.from({ length: size }, () => Array(size).fill(""));
        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                if ((row + col) % 2 !== 1) {
                    continue;
                }
                if (row < 3) {
                    board[row][col] = "b";
                }
                if (row > 4) {
                    board[row][col] = "r";
                }
            }
        }
    }

    function getMoveDirections(piece) {
        if (isKing(piece)) {
            return [-1, 1];
        }
        return ownerOf(piece) === "red" ? [-1] : [1];
    }

    function getMovesForPiece(row, col, captureOnly) {
        const piece = pieceAt(row, col);
        if (!piece) {
            return [];
        }

        const moves = [];
        const directions = getMoveDirections(piece);
        const opponent = ownerOf(piece) === "red" ? "black" : "red";

        directions.forEach((dr) => {
            [-1, 1].forEach((dc) => {
                const stepRow = row + dr;
                const stepCol = col + dc;
                const jumpRow = row + dr * 2;
                const jumpCol = col + dc * 2;

                if (!captureOnly && inBounds(stepRow, stepCol) && !pieceAt(stepRow, stepCol)) {
                    moves.push({ toRow: stepRow, toCol: stepCol, capture: null });
                }

                if (
                    inBounds(jumpRow, jumpCol) &&
                    pieceAt(stepRow, stepCol) &&
                    ownerOf(pieceAt(stepRow, stepCol)) === opponent &&
                    !pieceAt(jumpRow, jumpCol)
                ) {
                    moves.push({
                        toRow: jumpRow,
                        toCol: jumpCol,
                        capture: { row: stepRow, col: stepCol },
                    });
                }
            });
        });

        return moves;
    }

    function getAllCaptures(player) {
        const captures = [];
        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const piece = pieceAt(row, col);
                if (!piece || ownerOf(piece) !== player) {
                    continue;
                }
                const moves = getMovesForPiece(row, col, true).filter((move) => move.capture);
                if (moves.length) {
                    captures.push({ row, col, moves });
                }
            }
        }
        return captures;
    }

    function getLegalMoves(row, col) {
        const playerCaptures = getAllCaptures(currentPlayer);
        const mustCapture = playerCaptures.length > 0;
        if (mustCapture) {
            if (forcedChain && (forcedChain.row !== row || forcedChain.col !== col)) {
                return [];
            }
            return getMovesForPiece(row, col, true).filter((move) => move.capture);
        }
        return getMovesForPiece(row, col, false);
    }

    function hasAnyMoves(player) {
        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const piece = pieceAt(row, col);
                if (piece && ownerOf(piece) === player && getMovesForPiece(row, col, false).length) {
                    return true;
                }
            }
        }
        return false;
    }

    function updateStatus() {
        if (gameOver) {
            return;
        }
        if (forcedChain) {
            setStatus(`${playerName[currentPlayer]} 말은 연속 점프를 이어가야 합니다.`);
            return;
        }
        if (getAllCaptures(currentPlayer).length) {
            setStatus(`${playerName[currentPlayer]} 차례입니다. 잡을 수 있으면 반드시 잡아야 합니다.`);
            return;
        }
        setStatus(`${playerName[currentPlayer]} 차례입니다.`);
    }

    function clearSelection() {
        selected = null;
    }

    function finishTurn() {
        forcedChain = null;
        clearSelection();
        currentPlayer = currentPlayer === "red" ? "black" : "red";

        if (!hasAnyMoves(currentPlayer)) {
            gameOver = true;
            const winner = currentPlayer === "red" ? "검정" : "빨강";
            setStatus(`${winner} 승리입니다.`);
            return;
        }

        updateStatus();
    }

    function handleMove(toRow, toCol) {
        if (!selected) {
            return;
        }

        const fromRow = selected.row;
        const fromCol = selected.col;
        const piece = pieceAt(fromRow, fromCol);
        const move = getLegalMoves(fromRow, fromCol).find(
            (candidate) => candidate.toRow === toRow && candidate.toCol === toCol
        );

        if (!move) {
            return;
        }

        board[toRow][toCol] = piece;
        board[fromRow][fromCol] = "";

        if (move.capture) {
            board[move.capture.row][move.capture.col] = "";
        }

        if (piece === "r" && toRow === 0) {
            board[toRow][toCol] = "R";
        }
        if (piece === "b" && toRow === size - 1) {
            board[toRow][toCol] = "B";
        }

        if (move.capture) {
            const nextCaptures = getMovesForPiece(toRow, toCol, true).filter((candidate) => candidate.capture);
            if (nextCaptures.length) {
                forcedChain = { row: toRow, col: toCol };
                selected = { row: toRow, col: toCol };
                render();
                updateStatus();
                return;
            }
        }

        finishTurn();
        render();
    }

    function handleSquareClick(row, col) {
        if (gameOver || (row + col) % 2 === 0) {
            return;
        }

        const piece = pieceAt(row, col);
        if (selected) {
            if (!piece || ownerOf(piece) !== currentPlayer) {
                handleMove(row, col);
                return;
            }
        }

        if (!piece || ownerOf(piece) !== currentPlayer) {
            return;
        }

        if (forcedChain && (forcedChain.row !== row || forcedChain.col !== col)) {
            return;
        }

        if (!getLegalMoves(row, col).length) {
            return;
        }

        selected = { row, col };
        render();
        updateStatus();
    }

    function render() {
        boardEl.innerHTML = "";
        const hints = new Set();

        if (selected) {
            getLegalMoves(selected.row, selected.col).forEach((move) => {
                hints.add(`${move.toRow},${move.toCol}`);
            });
        }

        for (let row = 0; row < size; row += 1) {
            for (let col = 0; col < size; col += 1) {
                const square = document.createElement("button");
                square.type = "button";
                square.className = "checkers-square";
                square.classList.add((row + col) % 2 === 1 ? "dark" : "light");
                square.setAttribute("aria-label", `${row + 1}행 ${col + 1}열`);

                if (selected && selected.row === row && selected.col === col) {
                    square.classList.add("selected");
                }

                if (hints.has(`${row},${col}`)) {
                    square.classList.add("hint");
                }

                const piece = pieceAt(row, col);
                if (piece) {
                    const pieceEl = document.createElement("div");
                    pieceEl.className = "checkers-piece";
                    pieceEl.classList.add(ownerOf(piece));
                    pieceEl.textContent = isKing(piece) ? "왕" : "";
                    square.appendChild(pieceEl);
                }

                square.addEventListener("click", () => handleSquareClick(row, col));
                boardEl.appendChild(square);
            }
        }
    }

    function resetGame() {
        initBoard();
        currentPlayer = "black";
        selected = null;
        forcedChain = null;
        gameOver = false;
        render();
        setStatus("검정 차례입니다.");
    }

    resetBtn.addEventListener("click", resetGame);
    resetGame();
})();
