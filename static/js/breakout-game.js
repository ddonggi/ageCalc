(() => {
    const canvas = document.getElementById('breakout-canvas');
    const statusEl = document.getElementById('breakout-status');
    const startBtn = document.getElementById('breakout-start');
    const resetBtn = document.getElementById('breakout-reset');
    if (!canvas || !statusEl || !startBtn || !resetBtn) return;
    const ctx = canvas.getContext('2d'); if (!ctx) return;
    const rows = 5, cols = 8, brickHeight = 16, brickGap = 6, topOffset = 50;
    let bricks = []; let paddle = { x: 0, y: 0, w: 80, h: 10, speed: 5 }; let ball = { x: 0, y: 0, r: 6, vx: 2.6, vy: -2.6 }; let score = 0; let running = false; let started = false; let moveDir = 0;
    const setStatus = (t) => { statusEl.textContent = t; };
    const buildBricks = () => { const totalGap = brickGap * (cols - 1); const brickWidth = Math.floor((canvas.width - totalGap - 40) / cols); const startX = Math.floor((canvas.width - (brickWidth * cols + totalGap)) / 2); bricks = []; for (let r = 0; r < rows; r += 1) for (let c = 0; c < cols; c += 1) bricks.push({ x: startX + c * (brickWidth + brickGap), y: topOffset + r * (brickHeight + brickGap), w: brickWidth, h: brickHeight, active: true }); };
    const draw = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#2a1f2d'; bricks.forEach((b) => { if (b.active) ctx.fillRect(b.x, b.y, b.w, b.h); });
        ctx.fillStyle = '#ff6fb7'; ctx.fillRect(paddle.x, paddle.y, paddle.w, paddle.h);
        ctx.fillStyle = '#2a1f2d'; ctx.beginPath(); ctx.arc(ball.x, ball.y, ball.r, 0, Math.PI * 2); ctx.fill();
    };
    const resetGame = () => { buildBricks(); score = 0; paddle.x = (canvas.width - paddle.w) / 2; paddle.y = canvas.height - 30; ball.x = canvas.width / 2; ball.y = paddle.y - 12; ball.vx = 2.6; ball.vy = -2.6; running = false; started = false; moveDir = 0; setStatus('시작 버튼을 눌러 게임을 시작하세요.'); draw(); };
    const paddleControl = () => { paddle.x = Math.max(0, Math.min(canvas.width - paddle.w, paddle.x + moveDir * paddle.speed)); };
    const checkBrickHits = () => { for (const brick of bricks) { if (!brick.active) continue; if (ball.x + ball.r > brick.x && ball.x - ball.r < brick.x + brick.w && ball.y + ball.r > brick.y && ball.y - ball.r < brick.y + brick.h) { brick.active = false; ball.vy *= -1; score += 1; if (score === rows * cols) { running = false; setStatus('모든 벽돌 파괴!'); } break; } } };
    const update = () => {
        if (!running) return; paddleControl(); ball.x += ball.vx; ball.y += ball.vy;
        if (ball.x - ball.r <= 0 || ball.x + ball.r >= canvas.width) ball.vx *= -1;
        if (ball.y - ball.r <= 0) ball.vy *= -1;
        if (ball.y + ball.r >= paddle.y && ball.x >= paddle.x && ball.x <= paddle.x + paddle.w) { const hitPoint = (ball.x - (paddle.x + paddle.w / 2)) / (paddle.w / 2); ball.vx = hitPoint * 3; ball.vy = -Math.abs(ball.vy); }
        if (ball.y - ball.r > canvas.height) { running = false; setStatus('실패! 리셋 후 다시 도전하세요.'); }
        checkBrickHits(); draw(); requestAnimationFrame(update);
    };
    const startGame = () => { if (!started || !running) { started = true; running = true; setStatus('벽돌을 깨보세요!'); requestAnimationFrame(update); } };
    window.addEventListener('keydown', (e) => { if (e.key === 'ArrowLeft') moveDir = -1; if (e.key === 'ArrowRight') moveDir = 1; });
    window.addEventListener('keyup', (e) => { if (e.key === 'ArrowLeft' || e.key === 'ArrowRight') moveDir = 0; });
    canvas.addEventListener('mousemove', (e) => { const rect = canvas.getBoundingClientRect(); const x = e.clientX - rect.left; paddle.x = Math.max(0, Math.min(canvas.width - paddle.w, x - paddle.w / 2)); });
    startBtn.addEventListener('click', startGame); resetBtn.addEventListener('click', resetGame); resetGame();
})();
