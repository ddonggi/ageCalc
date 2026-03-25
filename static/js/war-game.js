(() => {
    const playerCardEl = document.getElementById('war-player-card');
    const cpuCardEl = document.getElementById('war-cpu-card');
    const statusEl = document.getElementById('war-status');
    const playerCountEl = document.getElementById('war-player-count');
    const cpuCountEl = document.getElementById('war-cpu-count');
    const pileCountEl = document.getElementById('war-pile-count');
    const turnBtn = document.getElementById('war-turn');
    const resetBtn = document.getElementById('war-reset');
    if (!playerCardEl || !cpuCardEl || !statusEl || !playerCountEl || !cpuCountEl || !pileCountEl || !turnBtn || !resetBtn) return;

    const suits = ['♠', '♥', '♦', '♣'];
    const rankLabels = { 11: 'J', 12: 'Q', 13: 'K', 14: 'A' };

    let playerDeck = [];
    let cpuDeck = [];
    let lastPileCount = 0;
    let gameOver = false;

    const createDeck = () => {
        const deck = [];
        for (let rank = 2; rank <= 14; rank += 1) {
            for (const suit of suits) deck.push({ rank, suit });
        }
        return deck;
    };

    const shuffle = (deck) => {
        for (let i = deck.length - 1; i > 0; i -= 1) {
            const j = Math.floor(Math.random() * (i + 1));
            [deck[i], deck[j]] = [deck[j], deck[i]];
        }
    };

    const deal = () => {
        const deck = createDeck();
        shuffle(deck);
        playerDeck = deck.slice(0, 26);
        cpuDeck = deck.slice(26);
    };

    const formatCard = (card) => {
        if (!card) return '?';
        const label = rankLabels[card.rank] ?? String(card.rank);
        return `${label}${card.suit}`;
    };

    const updateCounts = () => {
        playerCountEl.textContent = `플레이어 카드: ${playerDeck.length}장`;
        cpuCountEl.textContent = `컴퓨터 카드: ${cpuDeck.length}장`;
        pileCountEl.textContent = `이번 승부 카드: ${lastPileCount}장`;
    };

    const setStatus = (message) => {
        statusEl.textContent = message;
    };

    const drawCard = (deck) => deck.shift();

    const finishGame = () => {
        gameOver = true;
        if (playerDeck.length > cpuDeck.length) setStatus('플레이어 승리! 카드를 모두 모았습니다.');
        else if (cpuDeck.length > playerDeck.length) setStatus('컴퓨터 승리! 카드를 모두 모았습니다.');
        else setStatus('무승부입니다.');
    };

    const playTurn = () => {
        if (gameOver) return;
        const roundPile = [];
        let message = '';

        while (true) {
            if (playerDeck.length === 0 || cpuDeck.length === 0) {
                if (playerDeck.length > 0) playerDeck.push(...roundPile);
                else if (cpuDeck.length > 0) cpuDeck.push(...roundPile);
                lastPileCount = roundPile.length;
                updateCounts();
                finishGame();
                return;
            }

            const playerCard = drawCard(playerDeck);
            const cpuCard = drawCard(cpuDeck);
            playerCardEl.textContent = formatCard(playerCard);
            cpuCardEl.textContent = formatCard(cpuCard);
            roundPile.push(playerCard, cpuCard);

            if (playerCard.rank > cpuCard.rank) {
                playerDeck.push(...roundPile);
                message = `플레이어 승! ${roundPile.length}장을 가져갑니다.`;
                break;
            }

            if (playerCard.rank < cpuCard.rank) {
                cpuDeck.push(...roundPile);
                message = `컴퓨터 승! ${roundPile.length}장을 가져갑니다.`;
                break;
            }

            message = '동점! 전쟁이 계속됩니다.';
            if (playerDeck.length > 0) roundPile.push(drawCard(playerDeck));
            if (cpuDeck.length > 0) roundPile.push(drawCard(cpuDeck));
        }

        lastPileCount = roundPile.length;
        setStatus(message);
        updateCounts();
        if (playerDeck.length === 0 || cpuDeck.length === 0) finishGame();
    };

    const resetGame = () => {
        gameOver = false;
        deal();
        playerCardEl.textContent = '?';
        cpuCardEl.textContent = '?';
        lastPileCount = 0;
        setStatus('게임을 시작하세요.');
        updateCounts();
    };

    turnBtn.addEventListener('click', playTurn);
    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
