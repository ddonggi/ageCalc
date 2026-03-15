(() => {
    const suits = ['♠', '♥', '♦', '♣'];
    const ranks = [
        { label: 'A', value: 11 }, { label: '2', value: 2 }, { label: '3', value: 3 }, { label: '4', value: 4 },
        { label: '5', value: 5 }, { label: '6', value: 6 }, { label: '7', value: 7 }, { label: '8', value: 8 },
        { label: '9', value: 9 }, { label: '10', value: 10 }, { label: 'J', value: 10 }, { label: 'Q', value: 10 }, { label: 'K', value: 10 }
    ];
    const dealerCardsEl = document.getElementById('bj-dealer-cards');
    const playerCardsEl = document.getElementById('bj-player-cards');
    const dealerScoreEl = document.getElementById('bj-dealer-score');
    const playerScoreEl = document.getElementById('bj-player-score');
    const statusEl = document.getElementById('bj-status');
    const dealBtn = document.getElementById('bj-deal');
    const hitBtn = document.getElementById('bj-hit');
    const standBtn = document.getElementById('bj-stand');
    const newBtn = document.getElementById('bj-new');
    if (!dealerCardsEl || !playerCardsEl || !dealerScoreEl || !playerScoreEl || !statusEl || !dealBtn || !hitBtn || !standBtn || !newBtn) return;
    let deck = [], dealerHand = [], playerHand = [], inRound = false, revealDealer = false;
    const setStatus = (t) => { statusEl.textContent = t; };
    const shuffleDeck = () => { deck = []; suits.forEach((s) => ranks.forEach((r) => deck.push({ suit: s, label: r.label, value: r.value }))); for (let i = deck.length - 1; i > 0; i -= 1) { const j = Math.floor(Math.random() * (i + 1)); [deck[i], deck[j]] = [deck[j], deck[i]]; } };
    const drawCard = () => { if (!deck.length) shuffleDeck(); return deck.pop(); };
    const handValue = (hand) => { let total = 0, aces = 0; hand.forEach((c) => { total += c.value; if (c.label === 'A') aces += 1; }); while (total > 21 && aces > 0) { total -= 10; aces -= 1; } return total; };
    const renderHand = (el, hand, hideSecond) => { el.innerHTML = ''; hand.forEach((card, idx) => { const c = document.createElement('div'); c.textContent = hideSecond && idx === 1 ? '[hidden]' : `${card.label}${card.suit}`; el.appendChild(c); }); };
    const updateScores = () => { playerScoreEl.textContent = `점수: ${handValue(playerHand)}`; dealerScoreEl.textContent = revealDealer ? `점수: ${handValue(dealerHand)}` : '점수: ?'; };
    const setControls = () => { dealBtn.disabled = inRound; hitBtn.disabled = !inRound; standBtn.disabled = !inRound; };
    const render = () => { renderHand(dealerCardsEl, dealerHand, !revealDealer); renderHand(playerCardsEl, playerHand, false); updateScores(); setControls(); };
    const dealerPlay = () => { revealDealer = true; while (handValue(dealerHand) < 17) dealerHand.push(drawCard()); };
    const endRound = () => {
        revealDealer = true; inRound = false; dealerPlay();
        const dv = handValue(dealerHand); const pv = handValue(playerHand);
        if (pv > 21) setStatus('버스트! 딜러 승리');
        else if (dv > 21) setStatus('딜러 버스트! 승리');
        else if (pv > dv) setStatus('승리!');
        else if (pv < dv) setStatus('딜러 승리');
        else setStatus('무승부');
        render();
    };
    const startRound = () => { shuffleDeck(); dealerHand = [drawCard(), drawCard()]; playerHand = [drawCard(), drawCard()]; inRound = true; revealDealer = false; setStatus('내 차례입니다.'); render(); if (handValue(playerHand) === 21) endRound(); };
    dealBtn.addEventListener('click', () => { if (!inRound) startRound(); });
    hitBtn.addEventListener('click', () => { if (!inRound) return; playerHand.push(drawCard()); if (handValue(playerHand) > 21) endRound(); else render(); });
    standBtn.addEventListener('click', () => { if (inRound) endRound(); });
    newBtn.addEventListener('click', () => { dealerHand = []; playerHand = []; inRound = false; revealDealer = false; setStatus('Deal 버튼으로 시작하세요.'); render(); });
    render();
})();
