(() => {
    const canvas = document.getElementById('snake-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const scoreEl = document.getElementById('snake-score');
    const bestEl = document.getElementById('snake-best');
    const badgeEls = Array.from(document.querySelectorAll('.badge[data-badge]'));
    const rankEl = document.getElementById('snake-rank');
    const panelEl = document.querySelector('.game-panel');
    const confettiCanvas = document.getElementById('confetti-canvas');
    const bestToast = document.getElementById('best-toast');
    const startBtn = document.getElementById('snake-start');
    const pauseBtn = document.getElementById('snake-pause');
    const speedSelect = document.getElementById('snake-speed');
    const pad = document.querySelector('.game-pad');

    const cellCount = 20;
    let gridSize = 16;
    let boardSize = gridSize * cellCount;
    const cells = cellCount;
    const colors = {
        bg: '#fff7cc',
        grid: 'rgba(42, 31, 45, 0.1)',
        food: '#ffd166',
        border: '#2a1f2d'
    };

    const stages = [
        { label: '아기뱀', body: '#B8B8B8', eye: '#2a1f2d' },
        { label: '어린뱀', body: '#8BC34A', eye: '#2a1f2d' },
        { label: '청년뱀', body: '#4CAF50', eye: '#2a1f2d' },
        { label: '성체뱀', body: '#2196F3', eye: '#2a1f2d' },
        { label: '노장뱀', body: '#1565C0', eye: '#2a1f2d' },
        { label: '구렁이', body: '#9C27B0', eye: '#2a1f2d' },
        { label: '왕구렁이', body: '#6A1B9A', eye: '#2a1f2d' },
        { label: '영물뱀', body: '#FFC107', eye: '#2a1f2d' },
        { label: '이무기', body: '#FF5722', eye: '#2a1f2d' },
        { label: '승천룡', gradient: ['#00E5FF', '#FF00FF'], eye: '#2a1f2d' }
    ];

    let snake = [];
    let direction = { x: 1, y: 0 };
    let nextDirection = { x: 1, y: 0 };
    let food = { x: 6, y: 6 };
    let score = 0;
    let bestScore = Number(localStorage.getItem('snakeBest') || 0);
    let timer = null;
    let isPaused = false;
    let isGameOver = false;
    let blinkUntil = 0;
    let confettiLoop = null;

    const resizeCanvas = () => {
        const dpr = window.devicePixelRatio || 1;
        const maxSize = 480;
        const displaySize = Math.min(canvas.parentElement?.clientWidth || 400, maxSize);
        gridSize = Math.max(12, Math.floor(displaySize / cellCount));
        boardSize = gridSize * cellCount;
        canvas.style.width = `${boardSize}px`;
        canvas.style.height = `${boardSize}px`;
        canvas.width = boardSize * dpr;
        canvas.height = boardSize * dpr;
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        ctx.imageSmoothingEnabled = false;
    };

    const resizeConfetti = () => {
        if (!confettiCanvas || !panelEl) return;
        const rect = panelEl.getBoundingClientRect();
        const dpr = window.devicePixelRatio || 1;
        confettiCanvas.width = rect.width * dpr;
        confettiCanvas.height = rect.height * dpr;
        confettiCanvas.style.width = `${rect.width}px`;
        confettiCanvas.style.height = `${rect.height}px`;
    };

    const launchConfetti = () => {
        if (!confettiCanvas) return;
        const ctx2 = confettiCanvas.getContext('2d');
        if (!ctx2) return;
        resizeConfetti();
        const dpr = window.devicePixelRatio || 1;
        const width = confettiCanvas.width;
        const height = confettiCanvas.height;
        const pieces = Array.from({ length: 80 }, () => ({
            x: Math.random() * width,
            y: -20 - Math.random() * height * 0.2,
            r: 4 + Math.random() * 6,
            c: ['#ff6fb7', '#ffd166', '#5ad1ff', '#7cf5b5', '#ff9fb1'][Math.floor(Math.random() * 5)],
            vy: 2 + Math.random() * 3,
            vx: -1 + Math.random() * 2,
            rot: Math.random() * Math.PI,
            vr: -0.1 + Math.random() * 0.2
        }));
        let frame = 0;
        const animate = () => {
            frame += 1;
            ctx2.clearRect(0, 0, width, height);
            pieces.forEach(p => {
                p.x += p.vx;
                p.y += p.vy;
                p.rot += p.vr;
                ctx2.save();
                ctx2.translate(p.x, p.y);
                ctx2.rotate(p.rot);
                ctx2.fillStyle = p.c;
                ctx2.fillRect(-p.r / 2, -p.r / 2, p.r, p.r);
                ctx2.restore();
            });
            if (frame < 90) {
                requestAnimationFrame(animate);
            } else {
                ctx2.clearRect(0, 0, width, height);
            }
        };
        animate();
        if (bestToast) {
            bestToast.classList.add('show');
        }
    };

    const startConfettiLoop = () => {
        if (confettiLoop) return;
        launchConfetti();
        confettiLoop = setInterval(() => {
            launchConfetti();
        }, 1800);
    };

    const stopConfettiLoop = () => {
        if (confettiLoop) {
            clearInterval(confettiLoop);
            confettiLoop = null;
        }
    };

    const resetGame = () => {
        resizeCanvas();
        resizeConfetti();
        stopConfettiLoop();
        if (bestToast) bestToast.classList.remove('show');
        snake = [
            { x: 5, y: 8 },
            { x: 4, y: 8 },
            { x: 3, y: 8 }
        ];
        direction = { x: 1, y: 0 };
        nextDirection = { x: 1, y: 0 };
        score = 0;
        isPaused = false;
        isGameOver = false;
        pauseBtn.disabled = false;
        spawnFood();
        updateScore();
        draw();
    };

    const applyBadgeColors = () => {
        badgeEls.forEach((badge, idx) => {
            const stage = stages[idx];
            if (!stage) return;
            const stageColor = stage.body || (stage.gradient ? stage.gradient[0] : '#B8B8B8');
            badge.style.setProperty('--badge-color', stageColor);
        });
    };

    const updateScore = () => {
        scoreEl.textContent = score;
        bestEl.textContent = bestScore;
        badgeEls.forEach((badge, idx) => {
            const threshold = Number(badge.dataset.badge || 0);
            const earned = score >= threshold;
            badge.classList.toggle('is-earned', earned);
            const stageIndex = idx;
            const stage = stages[idx];
            if (!stage) return;
            badge.classList.toggle('badge-epic', stageIndex >= 5);
            const stageColor = stage.body || (stage.gradient ? stage.gradient[0] : '#B8B8B8');
            badge.style.setProperty('--badge-color', stageColor);
            if (earned) {
                if (stage.gradient) {
                    badge.style.backgroundImage = `linear-gradient(135deg, ${stage.gradient[0]}, ${stage.gradient[1]})`;
                    badge.style.backgroundColor = 'transparent';
                } else {
                    badge.style.backgroundImage = '';
                    badge.style.backgroundColor = stageColor;
                }
            } else {
                badge.style.backgroundImage = '';
                badge.style.backgroundColor = 'transparent';
            }
        });
        badgeEls.forEach((badge) => badge.classList.remove('next-badge'));
        const nextBadge = badgeEls.find((badge) => score < Number(badge.dataset.badge || 0));
        if (nextBadge && !isGameOver && timer) {
            nextBadge.classList.add('next-badge');
        }
    };

    const updateLeaderboard = (data) => {
        if (!data) return;
        if (rankEl) {
            rankEl.textContent = data.rank ? `${data.rank}위 / ${data.total || 0}명` : '-';
        }
    };

    const submitScore = async () => {
        try {
            const res = await fetch('/snake-score', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ score })
            });
            if (!res.ok) return;
            const data = await res.json();
            updateLeaderboard(data);
        } catch {
            // ignore
        }
    };

    const spawnFood = () => {
        let pos;
        do {
            pos = {
                x: Math.floor(Math.random() * cells),
                y: Math.floor(Math.random() * cells)
            };
        } while (snake.some(seg => seg.x === pos.x && seg.y === pos.y));
        food = pos;
    };

    const getStage = () => {
        const idx = Math.min(stages.length - 1, Math.floor(score / 10));
        return stages[idx];
    };

    const setDirection = (dir) => {
        const opposites = {
            left: { x: 1, y: 0 },
            right: { x: -1, y: 0 },
            up: { x: 0, y: 1 },
            down: { x: 0, y: -1 }
        };
        if (opposites[dir] && direction.x === opposites[dir].x && direction.y === opposites[dir].y) {
            return;
        }
        if (dir === 'left') nextDirection = { x: -1, y: 0 };
        if (dir === 'right') nextDirection = { x: 1, y: 0 };
        if (dir === 'up') nextDirection = { x: 0, y: -1 };
        if (dir === 'down') nextDirection = { x: 0, y: 1 };
    };

    const getFaceLayout = (dir, stageLabel, isBlinking, isDead, ageYears) => {
        const layouts = {
            front: {
                eyesWhite: [[4, 6, 4, 3], [9, 6, 4, 3]],
                eyesBlack: [[5, 7, 2, 2], [10, 7, 2, 2]]
            }
        };
        const face = layouts.front;
        if (stageLabel === '아기뱀') {
            face.eyesBlack = face.eyesBlack.map(([ex, ey, ew, eh]) => [ex, ey + 1, ew, eh]);
        }
        if (isBlinking) {
            face.eyesBlack = face.eyesBlack.map(([ex, ey, ew, eh]) => [ex, ey + 2, ew, 1]);
        }
        if (isDead) {
            face.eyesWhite = [];
            face.eyesBlack = [
                [4, 8, 4, 1],
                [9, 8, 4, 1]
            ];
        }
        if (ageYears >= 10) {
            face.beard = [[5, 12, 6, 2]];
        } else {
            face.beard = [];
        }
        return face;
    };

    const gameOver = () => {
        clearInterval(timer);
        timer = null;
        isGameOver = true;
        pauseBtn.disabled = true;
        const prevBest = bestScore;
        if (score > bestScore) {
            bestScore = score;
            localStorage.setItem('snakeBest', String(bestScore));
        }
        updateScore();
        draw(true);
        submitScore();
        if (score > prevBest) {
            startConfettiLoop();
        }
    };

    const tick = () => {
        if (isPaused) return;
        if (Math.random() < 0.06) {
            blinkUntil = Date.now() + 120;
        }
        direction = { ...nextDirection };
        const head = { x: snake[0].x + direction.x, y: snake[0].y + direction.y };

        if (head.x < 0 || head.y < 0 || head.x >= cells || head.y >= cells) {
            gameOver();
            return;
        }
        if (snake.some(seg => seg.x === head.x && seg.y === head.y)) {
            gameOver();
            return;
        }

        snake.unshift(head);

        if (head.x === food.x && head.y === food.y) {
            score += 1;
            if (score % 5 === 0 && timer) {
                restartTimer(Math.max(60, Number(speedSelect.value) - 10));
            }
            spawnFood();
            updateScore();
        } else {
            snake.pop();
        }

        draw();
    };

    const draw = (over = false) => {
        ctx.fillStyle = colors.bg;
        ctx.fillRect(0, 0, boardSize, boardSize);

        // Pixel background accents + grass + flowers
        for (let gx = 0; gx < cells; gx += 1) {
            for (let gy = 0; gy < cells; gy += 1) {
                const hash = (gx * 73 + gy * 97) % 100;
                const baseX = gx * gridSize;
                const baseY = gy * gridSize;
                if (hash < 7) {
                    ctx.fillStyle = hash < 3 ? '#7df0a4' : hash < 5 ? '#5ad17a' : '#8be7a0';
                    ctx.fillRect(baseX + 2, baseY + 10, 4, 4);
                    ctx.fillRect(baseX + 6, baseY + 8, 4, 6);
                }
                if (hash === 42) {
                    ctx.fillStyle = '#ffd1e8';
                    ctx.fillRect(baseX + 2, baseY + 2, 3, 3);
                    ctx.fillRect(baseX + 6, baseY + 4, 3, 3);
                    ctx.fillStyle = '#fff7cc';
                    ctx.fillRect(baseX + 5, baseY + 5, 2, 2);
                }
            }
        }

        ctx.strokeStyle = 'rgba(42, 31, 45, 0.28)';
        ctx.lineWidth = 1;
        for (let i = 0; i <= cells; i += 1) {
            const pos = i * gridSize + 0.5;
            ctx.beginPath();
            ctx.moveTo(pos, 0);
            ctx.lineTo(pos, boardSize);
            ctx.stroke();
            ctx.beginPath();
            ctx.moveTo(0, pos);
            ctx.lineTo(boardSize, pos);
            ctx.stroke();
        }

        ctx.fillStyle = colors.food;
        ctx.fillRect(food.x * gridSize + 2, food.y * gridSize + 4, gridSize - 4, gridSize - 6);
        ctx.fillStyle = '#5ad17a';
        ctx.fillRect(food.x * gridSize + 6, food.y * gridSize + 2, 4, 2);

        const stage = getStage();
        snake.forEach((seg, idx) => {
            const x = seg.x * gridSize;
            const y = seg.y * gridSize;
            const isTail = idx === snake.length - 1;
            const isPreTail = idx === snake.length - 2;
            if (idx === 0) {
                const bodyFill = stage.gradient
                    ? (() => {
                        const grad = ctx.createLinearGradient(x, y, x + gridSize, y + gridSize);
                        grad.addColorStop(0, stage.gradient[0]);
                        grad.addColorStop(1, stage.gradient[1]);
                        return grad;
                    })()
                    : stage.body;
                ctx.fillStyle = bodyFill;
                const headInset = 1;
                const headSize = gridSize - headInset * 2;
                const headRadius = Math.max(2, Math.floor(headSize * 0.18));
                ctx.beginPath();
                ctx.moveTo(x + headInset + headRadius, y + headInset);
                ctx.lineTo(x + headInset + headSize - headRadius, y + headInset);
                ctx.quadraticCurveTo(x + headInset + headSize, y + headInset, x + headInset + headSize, y + headInset + headRadius);
                ctx.lineTo(x + headInset + headSize, y + headInset + headSize - headRadius);
                ctx.quadraticCurveTo(x + headInset + headSize, y + headInset + headSize, x + headInset + headSize - headRadius, y + headInset + headSize);
                ctx.lineTo(x + headInset + headRadius, y + headInset + headSize);
                ctx.quadraticCurveTo(x + headInset, y + headInset + headSize, x + headInset, y + headInset + headSize - headRadius);
                ctx.lineTo(x + headInset, y + headInset + headRadius);
                ctx.quadraticCurveTo(x + headInset, y + headInset, x + headInset + headRadius, y + headInset);
                ctx.closePath();
                ctx.fill();
                const face = getFaceLayout('front', stage.label, Date.now() < blinkUntil, over, score);
                const scale = gridSize / 16;
                ctx.fillStyle = '#ffffff';
                face.eyesWhite.forEach(([ex, ey, ew, eh]) => {
                    ctx.fillRect(x + ex * scale, y + ey * scale, ew * scale, eh * scale);
                });
                ctx.fillStyle = stage.eye;
                face.eyesBlack.forEach(([ex, ey, ew, eh]) => {
                    ctx.fillRect(x + ex * scale, y + ey * scale, ew * scale, eh * scale);
                });
                if (face.beard && face.beard.length) {
                    ctx.fillStyle = '#7a6a7f';
                    face.beard.forEach(([bx, by, bw, bh]) => {
                        ctx.fillRect(x + bx * scale, y + by * scale, bw * scale, bh * scale);
                    });
                }
                // Nose and mouth removed
            } else {
                const bodyFill = stage.gradient
                    ? (() => {
                        const grad = ctx.createLinearGradient(x, y, x + gridSize, y + gridSize);
                        grad.addColorStop(0, stage.gradient[0]);
                        grad.addColorStop(1, stage.gradient[1]);
                        return grad;
                    })()
                    : stage.body;
                ctx.fillStyle = bodyFill;
                const inset = isTail ? 6 : isPreTail ? 4 : 2;
                const size = gridSize - inset * 2;
                const radius = Math.max(2, Math.floor(size * 0.28));
                ctx.beginPath();
                ctx.moveTo(x + inset + radius, y + inset);
                ctx.lineTo(x + inset + size - radius, y + inset);
                ctx.quadraticCurveTo(x + inset + size, y + inset, x + inset + size, y + inset + radius);
                ctx.lineTo(x + inset + size, y + inset + size - radius);
                ctx.quadraticCurveTo(x + inset + size, y + inset + size, x + inset + size - radius, y + inset + size);
                ctx.lineTo(x + inset + radius, y + inset + size);
                ctx.quadraticCurveTo(x + inset, y + inset + size, x + inset, y + inset + size - radius);
                ctx.lineTo(x + inset, y + inset + radius);
                ctx.quadraticCurveTo(x + inset, y + inset, x + inset + radius, y + inset);
                ctx.closePath();
                ctx.fill();
            }
        });

        ctx.strokeStyle = colors.border;
        ctx.lineWidth = 3;
        ctx.strokeRect(0, 0, boardSize, boardSize);

        // Border decorations
        for (let i = 0; i < cells; i += 1) {
            if (i % 3 === 0) {
                const topX = i * gridSize + 3;
                const topY = 3;
                ctx.fillStyle = '#5ad17a';
                ctx.fillRect(topX, topY, 4, 6);
                ctx.fillRect(topX + 6, topY + 2, 3, 4);
                const botY = boardSize - 9;
                ctx.fillRect(topX, botY, 4, 6);
                ctx.fillRect(topX + 6, botY + 2, 3, 4);
            }
            if (i % 4 === 0) {
                const sideY = i * gridSize + 4;
                const leftX = 3;
                ctx.fillStyle = '#7df0a4';
                ctx.fillRect(leftX, sideY, 5, 3);
                ctx.fillRect(leftX + 2, sideY + 4, 3, 3);
                const rightX = boardSize - 9;
                ctx.fillRect(rightX, sideY, 5, 3);
                ctx.fillRect(rightX + 2, sideY + 4, 3, 3);
            }
        }

        if (isPaused && !over) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.88)';
            ctx.fillRect(0, boardSize / 2 - 24, boardSize, 48);
            ctx.fillStyle = colors.border;
            ctx.font = '14px "Press Start 2P", monospace';
            ctx.textAlign = 'center';
            ctx.fillText('PAUSED', boardSize / 2, boardSize / 2 + 6);
        }

        if (over) {
            ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
            ctx.fillRect(0, boardSize / 2 - 28, boardSize, 56);
            ctx.fillStyle = colors.border;
            ctx.font = '16px "Press Start 2P", monospace';
            ctx.textAlign = 'center';
            ctx.fillText('GAME OVER', boardSize / 2, boardSize / 2 + 6);
            const stage = getStage();
            ctx.font = '12px "Press Start 2P", monospace';
            ctx.fillText(`나의 등급 : ${stage.label}`, boardSize / 2, boardSize / 2 + 22);
        }
    };

    const restartTimer = (speed) => {
        if (timer) clearInterval(timer);
        timer = setInterval(tick, speed);
    };

    startBtn?.addEventListener('click', () => {
        resetGame();
        restartTimer(Number(speedSelect.value));
        pauseBtn.disabled = false;
    });

    const togglePause = () => {
        if (isGameOver) return;
        isPaused = !isPaused;
        pauseBtn.textContent = isPaused ? '계속하기' : '일시정지';
        draw();
    };

    pauseBtn?.addEventListener('click', () => {
        togglePause();
    });

    speedSelect?.addEventListener('change', (e) => {
        if (timer) restartTimer(Number(e.target.value));
    });

    document.addEventListener('keydown', (e) => {
        if (e.code === 'Space') {
            e.preventDefault();
            togglePause();
            return;
        }
        const key = e.key.toLowerCase();
        if (['arrowup', 'w'].includes(key)) setDirection('up');
        if (['arrowdown', 's'].includes(key)) setDirection('down');
        if (['arrowleft', 'a'].includes(key)) setDirection('left');
        if (['arrowright', 'd'].includes(key)) setDirection('right');
    });

    pad?.addEventListener('click', (e) => {
        const btn = e.target.closest('button');
        if (!btn) return;
        const dir = btn.dataset.dir;
        if (dir) setDirection(dir);
    });

    window.addEventListener('resize', () => {
        resizeCanvas();
        resizeConfetti();
        draw();
    });

    bestEl.textContent = bestScore;
    applyBadgeColors();
    resetGame();
    isGameOver = true;
    pauseBtn.disabled = true;
})();
