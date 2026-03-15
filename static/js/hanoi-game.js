(() => {
    const diskCount = 4;
    const pegs = [[], [], []];
    const pegEls = Array.from(document.querySelectorAll('.hanoi-peg'));
    const statusEl = document.getElementById('hanoi-status');
    const movesEl = document.getElementById('hanoi-moves');
    const resetBtn = document.getElementById('hanoi-reset');
    if (!pegEls.length || !statusEl || !movesEl || !resetBtn) return;
    let selectedPeg = null; let moves = 0; let solved = false;
    const colors = ['#ffe29a', '#ffd166', '#ffb86b', '#ff9fb1', '#8fb9ff'];
    const setStatus = (t) => { statusEl.textContent = t; };
    const render = () => {
        pegs.forEach((peg, index) => {
            const stackEl = document.getElementById(`hanoi-peg-${index}`); if (!stackEl) return; stackEl.innerHTML = '';
            peg.forEach((size, diskIndex) => { const disk = document.createElement('div'); disk.className = 'hanoi-disk'; if (index === selectedPeg && diskIndex === peg.length - 1) disk.classList.add('selected'); disk.style.width = `${44 + size * 22}px`; disk.style.background = colors[size] || colors[0]; stackEl.appendChild(disk); });
        });
        movesEl.textContent = `이동: ${moves}`;
    };
    const resetGame = () => { pegs[0] = Array.from({ length: diskCount }, (_, i) => diskCount - i); pegs[1] = []; pegs[2] = []; selectedPeg = null; moves = 0; solved = false; setStatus('원판을 선택하고 이동할 기둥을 클릭하세요.'); render(); };
    const topDisk = (pegIndex) => { const peg = pegs[pegIndex]; return peg[peg.length - 1]; };
    const tryMove = (from, to) => {
        const disk = topDisk(from); if (disk === undefined) { setStatus('빈 기둥입니다.'); return; }
        const target = topDisk(to); if (target !== undefined && target < disk) { setStatus('큰 원판은 작은 원판 위에 놓을 수 없습니다.'); return; }
        pegs[from].pop(); pegs[to].push(disk); moves += 1;
        if (pegs[2].length === diskCount) { solved = true; setStatus(`${moves}번 만에 완료했습니다!`); } else { setStatus('다음 이동을 선택하세요.'); }
    };
    const handlePegClick = (index) => {
        if (solved) return;
        if (selectedPeg === null) { if (!pegs[index].length) { setStatus('빈 기둥입니다.'); return; } selectedPeg = index; setStatus('이동할 기둥을 선택하세요.'); render(); return; }
        if (selectedPeg === index) { selectedPeg = null; setStatus('선택 해제'); render(); return; }
        tryMove(selectedPeg, index); selectedPeg = null; render();
    };
    pegEls.forEach((peg) => { peg.addEventListener('click', () => handlePegClick(Number(peg.dataset.peg))); });
    resetBtn.addEventListener('click', resetGame); resetGame();
})();
