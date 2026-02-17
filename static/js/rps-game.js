(() => {
    const statusEl = document.getElementById('rps-status');
    const scoreEl = document.getElementById('rps-score');
    const resetBtn = document.getElementById('rps-reset');
    const pickButtons = Array.from(document.querySelectorAll('button[data-pick]'));
    const picks = ['rock', 'paper', 'scissors'];
    const labels = {
        rock: '바위',
        paper: '보',
        scissors: '가위'
    };

    if (!statusEl || !scoreEl || !resetBtn || pickButtons.length !== 3) return;

    let userScore = 0;
    let cpuScore = 0;

    const cpuPick = () => picks[Math.floor(Math.random() * picks.length)];

    const decideRound = (user, cpu) => {
        if (user === cpu) return 'draw';
        if (
            (user === 'rock' && cpu === 'scissors') ||
            (user === 'paper' && cpu === 'rock') ||
            (user === 'scissors' && cpu === 'paper')
        ) {
            return 'win';
        }
        return 'lose';
    };

    const updateScore = () => {
        scoreEl.textContent = `나 ${userScore} - ${cpuScore} 컴퓨터`;
    };

    const playRound = (user) => {
        const cpu = cpuPick();
        const result = decideRound(user, cpu);
        const userLabel = labels[user];
        const cpuLabel = labels[cpu];

        if (result === 'win') {
            userScore += 1;
            statusEl.textContent = `내 선택 ${userLabel}, 컴퓨터 ${cpuLabel}. 내가 이겼습니다.`;
        } else if (result === 'lose') {
            cpuScore += 1;
            statusEl.textContent = `내 선택 ${userLabel}, 컴퓨터 ${cpuLabel}. 컴퓨터 승리.`;
        } else {
            statusEl.textContent = `둘 다 ${userLabel}. 무승부.`;
        }

        updateScore();
    };

    const resetGame = () => {
        userScore = 0;
        cpuScore = 0;
        statusEl.textContent = '시작하려면 손동작을 선택하세요.';
        updateScore();
    };

    pickButtons.forEach((button) => {
        button.addEventListener('click', () => {
            playRound(button.dataset.pick);
        });
    });

    resetBtn.addEventListener('click', resetGame);
    resetGame();
})();
