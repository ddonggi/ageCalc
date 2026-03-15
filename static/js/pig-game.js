(() => {
    const targetScore = 50;
    const playerTotalEl = document.getElementById('pig-player-total');
    const cpuTotalEl = document.getElementById('pig-cpu-total');
    const turnEl = document.getElementById('pig-turn');
    const dieEl = document.getElementById('pig-die');
    const turnTotalEl = document.getElementById('pig-turn-total');
    const statusEl = document.getElementById('pig-status');
    const rollBtn = document.getElementById('pig-roll');
    const holdBtn = document.getElementById('pig-hold');
    const newBtn = document.getElementById('pig-new');
    if (!playerTotalEl || !cpuTotalEl || !turnEl || !dieEl || !turnTotalEl || !statusEl || !rollBtn || !holdBtn || !newBtn) return;
    let playerTotal = 0, cpuTotal = 0, turnTotal = 0, playerTurn = true, inGame = true;
    const setStatus = (t) => { statusEl.textContent = t; };
    const rollDie = () => Math.floor(Math.random() * 6) + 1;
    const updateUI = () => {
        playerTotalEl.textContent = String(playerTotal);
        cpuTotalEl.textContent = String(cpuTotal);
        turnTotalEl.textContent = String(turnTotal);
        turnEl.textContent = `턴: ${playerTurn ? '나' : '컴퓨터'}`;
        rollBtn.disabled = !playerTurn || !inGame;
        holdBtn.disabled = !playerTurn || !inGame;
    };
    const endGame = (message) => { inGame = false; setStatus(message); updateUI(); };
    const switchTurn = () => { playerTurn = !playerTurn; turnTotal = 0; updateUI(); if (!playerTurn) window.setTimeout(cpuTurn, 700); };
    const handleRoll = () => {
        if (!inGame || !playerTurn) return;
        const roll = rollDie(); dieEl.textContent = String(roll);
        if (roll === 1) { turnTotal = 0; setStatus('1이 나와 턴 종료'); switchTurn(); return; }
        turnTotal += roll; setStatus(`${roll}이 나왔습니다.`);
        if (playerTotal + turnTotal >= targetScore) { playerTotal += turnTotal; endGame('승리!'); return; }
        updateUI();
    };
    const handleHold = () => {
        if (!inGame || !playerTurn) return;
        playerTotal += turnTotal;
        if (playerTotal >= targetScore) { endGame('승리!'); return; }
        setStatus('점수 저장. 컴퓨터 차례'); switchTurn();
    };
    const cpuTurn = () => {
        if (!inGame || playerTurn) return;
        const roll = rollDie(); dieEl.textContent = String(roll);
        if (roll === 1) { turnTotal = 0; setStatus('컴퓨터가 1을 굴렸습니다.'); playerTurn = true; updateUI(); return; }
        turnTotal += roll;
        if (cpuTotal + turnTotal >= targetScore) { cpuTotal += turnTotal; endGame('컴퓨터 승리'); return; }
        if (turnTotal >= 12) { cpuTotal += turnTotal; turnTotal = 0; playerTurn = true; setStatus('컴퓨터가 Hold 했습니다.'); updateUI(); return; }
        updateUI(); window.setTimeout(cpuTurn, 700);
    };
    const newGame = () => { playerTotal = 0; cpuTotal = 0; turnTotal = 0; playerTurn = true; inGame = true; dieEl.textContent = '-'; setStatus('주사위를 굴려 시작하세요.'); updateUI(); };
    rollBtn.addEventListener('click', handleRoll); holdBtn.addEventListener('click', handleHold); newBtn.addEventListener('click', newGame); newGame();
})();
