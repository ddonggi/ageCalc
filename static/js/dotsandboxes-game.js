(() => {
    const canvas = document.getElementById('dab-board');
    const statusEl = document.getElementById('dab-status');
    const resetBtn = document.getElementById('dab-reset');
    if (!canvas || !statusEl || !resetBtn) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dotCount = 5;
    const boxCount = dotCount - 1;
    const margin = 40;
    const size = canvas.width;
    const spacing = (size - margin * 2) / (dotCount - 1);
    const hitRange = 12;
    const players = [
        { name: '플레이어 1', color: '#c84b4b', fill: 'rgba(200, 75, 75, 0.2)' },
        { name: '플레이어 2', color: '#3f6ab3', fill: 'rgba(63, 106, 179, 0.2)' }
    ];

    let hLines = [];
    let vLines = [];
    let boxes = [];
    let currentPlayer = 0;
    let scores = [0, 0];
    let gameOver = false;

    const updateStatus = (message) => {
        statusEl.textContent = `${message} 점수 ${scores[0]}-${scores[1]}.`;
    };

    const allLinesFilled = () => hLines.every((row) => row.every((cell) => cell !== null)) && vLines.every((row) => row.every((cell) => cell !== null));
    const checkBoxComplete = (row, col) => hLines[row][col] !== null && hLines[row + 1][col] !== null && vLines[row][col] !== null && vLines[row][col + 1] !== null;
    const claimBox = (row, col, playerIndex) => { boxes[row][col] = playerIndex; scores[playerIndex] += 1; };

    const finishGame = () => {
        if (scores[0] === scores[1]) updateStatus('게임 종료. 무승부입니다.');
        else if (scores[0] > scores[1]) updateStatus('게임 종료. 플레이어 1 승리입니다.');
        else updateStatus('게임 종료. 플레이어 2 승리입니다.');
        gameOver = true;
    };

    const getLineFromClick = (x, y) => {
        let best = null;
        let bestDistance = hitRange;

        for (let row = 0; row < dotCount; row += 1) {
            const yPos = margin + row * spacing;
            if (Math.abs(y - yPos) > hitRange) continue;
            for (let col = 0; col < boxCount; col += 1) {
                const xStart = margin + col * spacing;
                const xEnd = xStart + spacing;
                if (x < xStart - hitRange || x > xEnd + hitRange) continue;
                const distance = Math.abs(y - yPos);
                if (distance <= bestDistance) {
                    best = { type: 'h', row, col };
                    bestDistance = distance;
                }
            }
        }

        for (let row = 0; row < boxCount; row += 1) {
            const yStart = margin + row * spacing;
            const yEnd = yStart + spacing;
            if (y < yStart - hitRange || y > yEnd + hitRange) continue;
            for (let col = 0; col < dotCount; col += 1) {
                const xPos = margin + col * spacing;
                if (Math.abs(x - xPos) > hitRange) continue;
                const distance = Math.abs(x - xPos);
                if (distance <= bestDistance) {
                    best = { type: 'v', row, col };
                    bestDistance = distance;
                }
            }
        }

        return best;
    };

    const renderDots = () => {
        ctx.fillStyle = '#1d1b16';
        for (let row = 0; row < dotCount; row += 1) {
            for (let col = 0; col < dotCount; col += 1) {
                const x = margin + col * spacing;
                const y = margin + row * spacing;
                ctx.beginPath();
                ctx.arc(x, y, 4.5, 0, Math.PI * 2);
                ctx.fill();
            }
        }
    };

    const renderLines = () => {
        ctx.lineCap = 'round';
        ctx.lineWidth = 6;

        for (let row = 0; row < dotCount; row += 1) {
            for (let col = 0; col < boxCount; col += 1) {
                const xStart = margin + col * spacing;
                const xEnd = xStart + spacing;
                const yPos = margin + row * spacing;
                const owner = hLines[row][col];
                ctx.strokeStyle = owner === null ? '#d8cfc0' : players[owner].color;
                ctx.beginPath();
                ctx.moveTo(xStart, yPos);
                ctx.lineTo(xEnd, yPos);
                ctx.stroke();
            }
        }

        for (let row = 0; row < boxCount; row += 1) {
            for (let col = 0; col < dotCount; col += 1) {
                const yStart = margin + row * spacing;
                const yEnd = yStart + spacing;
                const xPos = margin + col * spacing;
                const owner = vLines[row][col];
                ctx.strokeStyle = owner === null ? '#d8cfc0' : players[owner].color;
                ctx.beginPath();
                ctx.moveTo(xPos, yStart);
                ctx.lineTo(xPos, yEnd);
                ctx.stroke();
            }
        }
    };

    const renderBoxes = () => {
        for (let row = 0; row < boxCount; row += 1) {
            for (let col = 0; col < boxCount; col += 1) {
                const owner = boxes[row][col];
                if (owner === null) continue;
                const x = margin + col * spacing + 6;
                const y = margin + row * spacing + 6;
                ctx.fillStyle = players[owner].fill;
                ctx.fillRect(x, y, spacing - 12, spacing - 12);
            }
        }
    };

    const render = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        renderBoxes();
        renderLines();
        renderDots();
    };

    const handleLineSelection = (line) => {
        if (!line) return;

        if (line.type === 'h') {
            if (hLines[line.row][line.col] !== null) return;
            hLines[line.row][line.col] = currentPlayer;
        } else {
            if (vLines[line.row][line.col] !== null) return;
            vLines[line.row][line.col] = currentPlayer;
        }

        let claimed = false;
        if (line.type === 'h') {
            if (line.row < boxCount && boxes[line.row][line.col] === null && checkBoxComplete(line.row, line.col)) {
                claimBox(line.row, line.col, currentPlayer);
                claimed = true;
            }
            if (line.row > 0 && boxes[line.row - 1][line.col] === null && checkBoxComplete(line.row - 1, line.col)) {
                claimBox(line.row - 1, line.col, currentPlayer);
                claimed = true;
            }
        } else {
            if (line.col < boxCount && boxes[line.row][line.col] === null && checkBoxComplete(line.row, line.col)) {
                claimBox(line.row, line.col, currentPlayer);
                claimed = true;
            }
            if (line.col > 0 && boxes[line.row][line.col - 1] === null && checkBoxComplete(line.row, line.col - 1)) {
                claimBox(line.row, line.col - 1, currentPlayer);
                claimed = true;
            }
        }

        if (!claimed) currentPlayer = currentPlayer === 0 ? 1 : 0;

        if (allLinesFilled()) finishGame();
        else updateStatus(`${players[currentPlayer].name} 차례입니다.`);

        render();
    };

    const resetGame = () => {
        hLines = Array.from({ length: dotCount }, () => Array(boxCount).fill(null));
        vLines = Array.from({ length: boxCount }, () => Array(dotCount).fill(null));
        boxes = Array.from({ length: boxCount }, () => Array(boxCount).fill(null));
        currentPlayer = 0;
        scores = [0, 0];
        gameOver = false;
        updateStatus('플레이어 1이 먼저 시작합니다. 선을 클릭하세요.');
        render();
    };

    canvas.addEventListener('click', (event) => {
        if (gameOver) return;
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const x = (event.clientX - rect.left) * scaleX;
        const y = (event.clientY - rect.top) * scaleY;
        handleLineSelection(getLineFromClick(x, y));
    });

    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
