(() => {
    const bg = document.getElementById('pixel-background');
    if (!bg) return;

    const sprites = [
        {
            normal: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffd166'/><rect x='5' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='2' fill='%232a1f2d'/><rect x='2' y='6' width='1' height='2' fill='%232a1f2d'/><rect x='13' y='6' width='1' height='2' fill='%232a1f2d'/></svg>",
            happy: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffd166'/><rect x='5' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='5' y='10' width='6' height='1' fill='%232a1f2d'/><rect x='2' y='6' width='1' height='2' fill='%232a1f2d'/><rect x='13' y='6' width='1' height='2' fill='%232a1f2d'/></svg>",
            wink: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffd166'/><rect x='5' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='1' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='5' y='10' width='6' height='1' fill='%232a1f2d'/><rect x='2' y='6' width='1' height='2' fill='%232a1f2d'/></svg>",
            surprised: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffd166'/><rect x='5' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='2' fill='%232a1f2d'/></svg>"
        },
        {
            normal: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='3' width='8' height='10' fill='%235ad1ff'/><rect x='5' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='2' fill='%232a1f2d'/><rect x='6' y='2' width='4' height='1' fill='%232a1f2d'/></svg>",
            happy: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='3' width='8' height='10' fill='%235ad1ff'/><rect x='5' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='6' y='10' width='4' height='1' fill='%232a1f2d'/><rect x='6' y='2' width='4' height='1' fill='%232a1f2d'/></svg>",
            wink: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='3' width='8' height='10' fill='%235ad1ff'/><rect x='5' y='6' width='2' height='1' fill='%232a1f2d'/><rect x='9' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='6' y='10' width='4' height='1' fill='%232a1f2d'/></svg>",
            surprised: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='3' width='8' height='10' fill='%235ad1ff'/><rect x='5' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='5' width='2' height='2' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='2' fill='%232a1f2d'/></svg>"
        },
        {
            normal: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='4' width='10' height='9' fill='%23ff6fb7'/><rect x='5' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='2' y='3' width='2' height='2' fill='%232a1f2d'/><rect x='12' y='3' width='2' height='2' fill='%232a1f2d'/></svg>",
            happy: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='4' width='10' height='9' fill='%23ff6fb7'/><rect x='5' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='5' y='10' width='6' height='1' fill='%232a1f2d'/><rect x='2' y='3' width='2' height='2' fill='%232a1f2d'/><rect x='12' y='3' width='2' height='2' fill='%232a1f2d'/></svg>",
            wink: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='4' width='10' height='9' fill='%23ff6fb7'/><rect x='5' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='7' width='2' height='1' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='5' y='10' width='6' height='1' fill='%232a1f2d'/></svg>",
            surprised: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='4' width='10' height='9' fill='%23ff6fb7'/><rect x='5' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='2' fill='%232a1f2d'/></svg>"
        },
        {
            normal: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23b6ff8f'/><rect x='6' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='1' fill='%232a1f2d'/><rect x='7' y='2' width='2' height='2' fill='%232a1f2d'/></svg>",
            happy: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23b6ff8f'/><rect x='6' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='1' fill='%232a1f2d'/><rect x='6' y='10' width='4' height='1' fill='%232a1f2d'/><rect x='7' y='2' width='2' height='2' fill='%232a1f2d'/></svg>",
            wink: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23b6ff8f'/><rect x='6' y='7' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='1' fill='%232a1f2d'/><rect x='6' y='10' width='4' height='1' fill='%232a1f2d'/></svg>",
            surprised: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23b6ff8f'/><rect x='6' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='2' fill='%232a1f2d'/></svg>"
        },
        {
            normal: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffa94d'/><rect x='5' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='2' y='3' width='2' height='2' fill='%232a1f2d'/><rect x='12' y='3' width='2' height='2' fill='%232a1f2d'/></svg>",
            happy: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffa94d'/><rect x='5' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='5' y='10' width='6' height='1' fill='%232a1f2d'/></svg>",
            wink: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffa94d'/><rect x='5' y='7' width='2' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='6' y='9' width='4' height='1' fill='%232a1f2d'/><rect x='5' y='10' width='6' height='1' fill='%232a1f2d'/></svg>",
            surprised: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='3' y='3' width='10' height='10' fill='%23ffa94d'/><rect x='5' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='9' y='6' width='2' height='2' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='2' fill='%232a1f2d'/></svg>"
        },
        {
            normal: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23c084fc'/><rect x='6' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='1' fill='%232a1f2d'/></svg>",
            happy: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23c084fc'/><rect x='6' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='1' fill='%232a1f2d'/><rect x='6' y='10' width='4' height='1' fill='%232a1f2d'/></svg>",
            wink: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23c084fc'/><rect x='6' y='7' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='1' fill='%232a1f2d'/></svg>",
            surprised: "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='56' height='56' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='4' y='4' width='8' height='8' fill='%23c084fc'/><rect x='6' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='9' y='6' width='1' height='1' fill='%232a1f2d'/><rect x='7' y='9' width='2' height='2' fill='%232a1f2d'/></svg>"
        }
    ];

    const effects = [
        "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><path d='M8 13L4 9V6l2-2h2l2 2v3z' fill='%23ff6fb7'/></svg>",
        "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><path d='M8 2l2 4h4l-3 3 1 5-4-2-4 2 1-5-3-3h4z' fill='%23ffd166'/></svg>",
        "data:image/svg+xml;utf8,<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'><rect width='16' height='16' fill='none'/><rect x='7' y='2' width='2' height='12' fill='%235ad1ff'/><rect x='2' y='7' width='12' height='2' fill='%235ad1ff'/></svg>"
    ];

    const stickerCount = 16;
    const stickers = [];
    let width = window.innerWidth;
    let height = window.innerHeight;

    bg.style.position = 'fixed';
    bg.style.inset = '0';
    bg.style.zIndex = '0';
    bg.style.pointerEvents = 'auto';

    const createSticker = () => {
        const el = document.createElement('div');
        el.className = 'pixel-sticker';
        const pick = sprites[Math.floor(Math.random() * sprites.length)];
        el.dataset.normal = pick.normal;
        el.dataset.happy = pick.happy;
        el.dataset.wink = pick.wink;
        el.dataset.surprised = pick.surprised;
        el.dataset.state = 'normal';
        el.style.backgroundImage = `url("${pick.normal}")`;
        el.style.left = Math.random() * (width - 60) + 'px';
        el.style.top = Math.random() * (height - 60) + 'px';
        el.dataset.vx = (Math.random() * 0.9 + 0.5) * (Math.random() > 0.5 ? 1 : -1);
        el.dataset.vy = (Math.random() * 0.9 + 0.5) * (Math.random() > 0.5 ? 1 : -1);
        bg.appendChild(el);
        stickers.push(el);
    };

    for (let i = 0; i < stickerCount; i += 1) {
        createSticker();
    }

    const tick = () => {
        for (const el of stickers) {
            let x = parseFloat(el.style.left);
            let y = parseFloat(el.style.top);
            let vx = parseFloat(el.dataset.vx);
            let vy = parseFloat(el.dataset.vy);

            x += vx;
            y += vy;

            if (x <= 0 || x >= width - 56) {
                vx *= -1;
                x = Math.max(0, Math.min(width - 56, x));
            }
            if (y <= 0 || y >= height - 56) {
                vy *= -1;
                y = Math.max(0, Math.min(height - 56, y));
            }

            el.style.left = x + 'px';
            el.style.top = y + 'px';
            el.dataset.vx = vx;
            el.dataset.vy = vy;
        }
        requestAnimationFrame(tick);
    };

    requestAnimationFrame(tick);

    window.addEventListener('resize', () => {
        width = window.innerWidth;
        height = window.innerHeight;
    });

    const sparkle = (x, y) => {
        for (let i = 0; i < 12; i += 1) {
            const p = document.createElement('div');
            p.className = 'pixel-spark';
            p.style.left = x + 'px';
            p.style.top = y + 'px';
            p.style.setProperty('--dx', (Math.random() * 60 - 30) + 'px');
            p.style.setProperty('--dy', (Math.random() * 60 - 30) + 'px');
            p.style.backgroundImage = `url("${effects[Math.floor(Math.random() * effects.length)]}")`;
            bg.appendChild(p);
            setTimeout(() => p.remove(), 550);
        }
    };

    const flipFace = (el) => {
        const faces = ['happy', 'wink', 'surprised'];
        const pick = faces[Math.floor(Math.random() * faces.length)];
        el.dataset.state = pick;
        el.style.backgroundImage = `url("${el.dataset[pick]}")`;
        setTimeout(() => {
            el.dataset.state = 'normal';
            el.style.backgroundImage = `url("${el.dataset.normal}")`;
        }, 700);
    };

    bg.addEventListener('click', (e) => {
        const target = e.target;
        if (!(target instanceof HTMLElement)) return;
        if (!target.classList.contains('pixel-sticker')) return;
        const rect = target.getBoundingClientRect();
        sparkle(rect.left + rect.width / 2, rect.top + rect.height / 2);
        flipFace(target);
    });
})();
