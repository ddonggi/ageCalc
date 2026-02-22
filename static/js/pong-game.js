(() => {
    const canvas = document.getElementById('pong-canvas');
    const scoreEl = document.getElementById('pong-score');
    const toggleBtn = document.getElementById('pong-toggle');
    const resetBtn = document.getElementById('pong-reset');
    const upBtn = document.getElementById('pong-up');
    const downBtn = document.getElementById('pong-down');

    if (!canvas || !scoreEl || !toggleBtn || !resetBtn) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const court = { width: canvas.width, height: canvas.height };
    const paddle = { width: 12, height: 70, speed: 4 };
    const ballSize = 10;
    const heldKeys = { up: false, down: false };

    let player = { x: 18, y: (court.height - paddle.height) / 2, dy: 0 };
    let ai = { x: court.width - 18 - paddle.width, y: (court.height - paddle.height) / 2 };
    let ball = { x: court.width / 2, y: court.height / 2, vx: 2.6, vy: 2.2 };
    let score = { player: 0, ai: 0 };
    let running = false;
    let rafId = null;

    const clamp = (value, min, max) => Math.max(min, Math.min(max, value));

    const updatePlayerMotion = () => {
        if (heldKeys.up && !heldKeys.down) {
            player.dy = -paddle.speed;
            return;
        }
        if (heldKeys.down && !heldKeys.up) {
            player.dy = paddle.speed;
            return;
        }
        player.dy = 0;
    };

    const updateScore = () => {
        scoreEl.textContent = `플레이어 ${score.player} - ${score.ai} AI`;
    };

    const resetBall = (direction) => {
        ball.x = court.width / 2;
        ball.y = court.height / 2;
        ball.vx = direction * 2.6;
        ball.vy = (Math.random() * 2 + 1.4) * (Math.random() < 0.5 ? -1 : 1);
    };

    const resetGame = () => {
        score = { player: 0, ai: 0 };
        player.y = (court.height - paddle.height) / 2;
        ai.y = (court.height - paddle.height) / 2;
        player.dy = 0;
        heldKeys.up = false;
        heldKeys.down = false;
        resetBall(Math.random() < 0.5 ? 1 : -1);
        updateScore();
    };

    const draw = () => {
        ctx.clearRect(0, 0, court.width, court.height);
        ctx.fillStyle = '#ffeec8';
        ctx.fillRect(0, 0, court.width, court.height);

        ctx.fillStyle = '#2a1f2d';
        for (let y = 10; y < court.height; y += 20) {
            ctx.fillRect(court.width / 2 - 1, y, 2, 10);
        }

        ctx.fillStyle = '#ff6fb7';
        ctx.fillRect(player.x, player.y, paddle.width, paddle.height);
        ctx.fillStyle = '#5ad1ff';
        ctx.fillRect(ai.x, ai.y, paddle.width, paddle.height);

        ctx.fillStyle = '#2a1f2d';
        ctx.beginPath();
        ctx.arc(ball.x, ball.y, ballSize / 2, 0, Math.PI * 2);
        ctx.fill();
    };

    const step = () => {
        player.y = clamp(player.y + player.dy, 0, court.height - paddle.height);

        const aiCenter = ai.y + paddle.height / 2;
        const diff = ball.y - aiCenter;
        ai.y = clamp(ai.y + clamp(diff, -3, 3), 0, court.height - paddle.height);

        ball.x += ball.vx;
        ball.y += ball.vy;

        if (ball.y <= ballSize / 2 || ball.y >= court.height - ballSize / 2) {
            ball.vy *= -1;
        }

        if (
            ball.x - ballSize / 2 <= player.x + paddle.width &&
            ball.y + ballSize / 2 >= player.y &&
            ball.y - ballSize / 2 <= player.y + paddle.height
        ) {
            ball.vx = Math.abs(ball.vx);
        }

        if (
            ball.x + ballSize / 2 >= ai.x &&
            ball.y + ballSize / 2 >= ai.y &&
            ball.y - ballSize / 2 <= ai.y + paddle.height
        ) {
            ball.vx = -Math.abs(ball.vx);
        }

        if (ball.x < -ballSize) {
            score.ai += 1;
            updateScore();
            resetBall(1);
        }

        if (ball.x > court.width + ballSize) {
            score.player += 1;
            updateScore();
            resetBall(-1);
        }

        draw();
        rafId = window.requestAnimationFrame(step);
    };

    const stopLoop = () => {
        if (rafId) {
            window.cancelAnimationFrame(rafId);
            rafId = null;
        }
    };

    const toggleGame = () => {
        running = !running;
        toggleBtn.textContent = running ? '일시정지' : '시작';
        if (running) {
            if (!rafId) rafId = window.requestAnimationFrame(step);
            return;
        }
        stopLoop();
    };

    const keyDown = (event) => {
        const key = event.key.toLowerCase();
        if (event.key === 'ArrowUp' || key === 'w') {
            heldKeys.up = true;
            updatePlayerMotion();
        }
        if (event.key === 'ArrowDown' || key === 's') {
            heldKeys.down = true;
            updatePlayerMotion();
        }
        if (event.code === 'Space') {
            event.preventDefault();
            toggleGame();
        }
    };

    const keyUp = (event) => {
        const key = event.key.toLowerCase();
        if (event.key === 'ArrowUp' || key === 'w') {
            heldKeys.up = false;
        }
        if (event.key === 'ArrowDown' || key === 's') {
            heldKeys.down = false;
        }
        updatePlayerMotion();
    };

    const bindTouch = (button, direction) => {
        if (!button) return;
        const press = (event) => {
            event.preventDefault();
            heldKeys[direction] = true;
            updatePlayerMotion();
        };
        const release = (event) => {
            event.preventDefault();
            heldKeys[direction] = false;
            updatePlayerMotion();
        };
        button.addEventListener('touchstart', press, { passive: false });
        button.addEventListener('touchend', release, { passive: false });
        button.addEventListener('touchcancel', release, { passive: false });
        button.addEventListener('mousedown', press);
        button.addEventListener('mouseup', release);
        button.addEventListener('mouseleave', release);
    };

    window.addEventListener('keydown', keyDown);
    window.addEventListener('keyup', keyUp);

    toggleBtn.addEventListener('click', toggleGame);
    resetBtn.addEventListener('click', () => {
        resetGame();
        if (!running) draw();
    });

    bindTouch(upBtn, 'up');
    bindTouch(downBtn, 'down');

    resetGame();
    draw();
})();
