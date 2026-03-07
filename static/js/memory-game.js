(() => {
    const symbols = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'];
    const grid = document.getElementById('memory-grid');
    const statusEl = document.getElementById('memory-status');
    const movesEl = document.getElementById('memory-moves');
    const resetBtn = document.getElementById('memory-reset');

    if (!grid || !statusEl || !movesEl || !resetBtn) return;

    let deck = [];
    let revealed = [];
    let matched = new Set();
    let moves = 0;
    let lock = false;

    const shuffle = (array) => {
        for (let i = array.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [array[i], array[j]] = [array[j], array[i]];
        }
        return array;
    };

    const updateMoves = () => {
        movesEl.textContent = `이동 횟수: ${moves}`;
    };

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const renderGrid = () => {
        grid.innerHTML = '';
        deck.forEach((_, index) => {
            const button = document.createElement('button');
            button.className = 'memory-card';
            button.type = 'button';
            button.dataset.index = String(index);
            button.textContent = '?';
            grid.appendChild(button);
        });
    };

    const revealCard = (index) => {
        const card = grid.children[index];
        card.classList.add('revealed');
        card.textContent = deck[index];
    };

    const hideCard = (index) => {
        const card = grid.children[index];
        card.classList.remove('revealed');
        card.textContent = '?';
    };

    const markMatched = (indices) => {
        indices.forEach((index) => {
            grid.children[index].classList.add('matched');
        });
    };

    const handlePick = (index) => {
        if (lock || matched.has(index) || revealed.includes(index)) return;

        revealCard(index);
        revealed.push(index);
        if (revealed.length < 2) return;

        moves += 1;
        updateMoves();
        const [first, second] = revealed;

        if (deck[first] === deck[second]) {
            matched.add(first);
            matched.add(second);
            markMatched([first, second]);
            revealed = [];
            if (matched.size === deck.length) {
                setStatus(`${moves}번 만에 모든 짝을 맞췄습니다!`);
            }
            return;
        }

        lock = true;
        window.setTimeout(() => {
            hideCard(first);
            hideCard(second);
            revealed = [];
            lock = false;
        }, 700);
    };

    const resetGame = () => {
        deck = shuffle([...symbols, ...symbols]);
        revealed = [];
        matched = new Set();
        moves = 0;
        lock = false;
        renderGrid();
        updateMoves();
        setStatus('같은 카드를 찾아보세요.');
    };

    grid.addEventListener('click', (event) => {
        const target = event.target;
        if (!(target instanceof HTMLButtonElement)) return;
        handlePick(Number(target.dataset.index));
    });

    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
