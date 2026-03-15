(() => {
    const size = 4;
    const boardEl = document.getElementById('g2048-board');
    const statusEl = document.getElementById('g2048-status');
    const resetBtn = document.getElementById('g2048-reset');
    if (!boardEl || !statusEl || !resetBtn) return;
    let grid = [];
    let moved = false;
    const setStatus = (t) => { statusEl.textContent = t; };
    const emptyGrid = () => { grid = Array.from({ length: size }, () => Array(size).fill(0)); };
    const randomEmptyCell = () => {
        const empty = [];
        for (let r = 0; r < size; r += 1) for (let c = 0; c < size; c += 1) if (grid[r][c] === 0) empty.push([r, c]);
        return empty.length ? empty[Math.floor(Math.random() * empty.length)] : null;
    };
    const addRandomTile = () => { const spot = randomEmptyCell(); if (!spot) return; const [r, c] = spot; grid[r][c] = Math.random() < 0.9 ? 2 : 4; };
    const draw = () => {
        boardEl.innerHTML = '';
        grid.flat().forEach((value) => { const tile = document.createElement('div'); tile.className = 'tile-2048'; tile.textContent = value || ''; boardEl.appendChild(tile); });
    };
    const slideRowLeft = (row) => {
        const values = row.filter((v) => v !== 0);
        for (let i = 0; i < values.length - 1; i += 1) if (values[i] === values[i + 1]) { values[i] *= 2; values[i + 1] = 0; i += 1; }
        const merged = values.filter((v) => v !== 0);
        while (merged.length < size) merged.push(0);
        return merged;
    };
    const rotateGrid = () => {
        const rotated = Array.from({ length: size }, () => Array(size).fill(0));
        for (let r = 0; r < size; r += 1) for (let c = 0; c < size; c += 1) rotated[c][size - 1 - r] = grid[r][c];
        grid = rotated;
    };
    const moveLeft = () => {
        moved = false;
        for (let r = 0; r < size; r += 1) {
            const original = grid[r].slice();
            const slid = slideRowLeft(grid[r]);
            grid[r] = slid;
            if (original.join(',') !== slid.join(',')) moved = true;
        }
    };
    const hasMoves = () => {
        for (let r = 0; r < size; r += 1) for (let c = 0; c < size; c += 1) {
            if (grid[r][c] === 0) return true;
            if (c < size - 1 && grid[r][c] === grid[r][c + 1]) return true;
            if (r < size - 1 && grid[r][c] === grid[r + 1][c]) return true;
        }
        return false;
    };
    const checkEnd = () => {
        if (grid.flat().some((value) => value === 2048)) { setStatus('2048 달성! 계속하거나 새 게임을 시작하세요.'); return; }
        setStatus(hasMoves() ? '방향키로 타일을 이동하세요.' : '더 이상 이동할 수 없습니다. 새 게임을 시작하세요.');
    };
    const move = (direction) => {
        const rotations = { left: 0, up: 1, right: 2, down: 3 };
        for (let i = 0; i < rotations[direction]; i += 1) rotateGrid();
        moveLeft();
        for (let i = 0; i < (4 - rotations[direction]) % 4; i += 1) rotateGrid();
        if (moved) addRandomTile();
        draw();
        checkEnd();
    };
    const reset = () => { emptyGrid(); addRandomTile(); addRandomTile(); draw(); setStatus('방향키로 타일을 이동하세요.'); };
    window.addEventListener('keydown', (event) => {
        if (event.key === 'ArrowLeft') move('left');
        if (event.key === 'ArrowRight') move('right');
        if (event.key === 'ArrowUp') move('up');
        if (event.key === 'ArrowDown') move('down');
    });
    resetBtn.addEventListener('click', reset);
    reset();
})();
