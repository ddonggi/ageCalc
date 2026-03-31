(() => {
    const diceEls = Array.from(document.querySelectorAll(".yahtzee-die"));
    const statusEl = document.getElementById("yahtzee-status");
    const roundEl = document.getElementById("yahtzee-round");
    const rollsEl = document.getElementById("yahtzee-rolls");
    const sheetEl = document.getElementById("yahtzee-sheet");
    const totalsEl = document.getElementById("yahtzee-totals");
    const rollBtn = document.getElementById("yahtzee-roll");
    const resetBtn = document.getElementById("yahtzee-reset");

    if (!diceEls.length || !statusEl || !roundEl || !rollsEl || !sheetEl || !totalsEl || !rollBtn || !resetBtn) {
        return;
    }

    const categories = [
        { key: "ones", label: "1의 합", section: "upper" },
        { key: "twos", label: "2의 합", section: "upper" },
        { key: "threes", label: "3의 합", section: "upper" },
        { key: "fours", label: "4의 합", section: "upper" },
        { key: "fives", label: "5의 합", section: "upper" },
        { key: "sixes", label: "6의 합", section: "upper" },
        { key: "threeKind", label: "같은 눈 3개", section: "lower" },
        { key: "fourKind", label: "같은 눈 4개", section: "lower" },
        { key: "fullHouse", label: "풀하우스", section: "lower" },
        { key: "smallStraight", label: "스몰 스트레이트", section: "lower" },
        { key: "largeStraight", label: "라지 스트레이트", section: "lower" },
        { key: "yahtzee", label: "야추", section: "lower" },
        { key: "chance", label: "찬스", section: "lower" },
    ];

    let dice = [];
    let locks = [];
    let rollCount = 0;
    let scores = {};
    let gameOver = false;

    function setStatus(message) {
        statusEl.textContent = message;
    }

    function resetGame() {
        dice = Array(5).fill(null);
        locks = Array(5).fill(false);
        rollCount = 0;
        scores = {};
        gameOver = false;
        setStatus("주사위를 굴린 뒤 점수 칸을 선택하세요.");
        render();
    }

    function rollDice() {
        if (gameOver || rollCount >= 3) {
            return;
        }

        dice = dice.map((value, index) => (locks[index] ? value : 1 + Math.floor(Math.random() * 6)));
        rollCount += 1;
        setStatus(rollCount >= 3 ? "점수 칸 하나를 선택하세요." : "고정할 주사위를 선택하거나 한 번 더 굴리세요.");
        render();
    }

    function toggleLock(index) {
        if (gameOver || rollCount === 0) {
            return;
        }
        locks[index] = !locks[index];
        render();
    }

    function countsFromDice() {
        const counts = Array(7).fill(0);
        let sum = 0;

        dice.forEach((value) => {
            if (!value) {
                return;
            }
            counts[value] += 1;
            sum += value;
        });

        return { counts, sum };
    }

    function hasStraight(values, length) {
        const set = new Set(values);
        const unique = Array.from(set).sort((a, b) => a - b);

        if (length === 5) {
            return unique.length === 5 && (unique[0] === 1 || unique[0] === 2) && unique[4] - unique[0] === 4;
        }

        return [
            [1, 2, 3, 4],
            [2, 3, 4, 5],
            [3, 4, 5, 6],
        ].some((sequence) => sequence.every((num) => set.has(num)));
    }

    function scoreFor(categoryKey) {
        if (rollCount === 0) {
            return 0;
        }

        const values = dice.filter(Boolean);
        const { counts, sum } = countsFromDice();
        const maxCount = Math.max(...counts);

        switch (categoryKey) {
            case "ones":
                return counts[1] * 1;
            case "twos":
                return counts[2] * 2;
            case "threes":
                return counts[3] * 3;
            case "fours":
                return counts[4] * 4;
            case "fives":
                return counts[5] * 5;
            case "sixes":
                return counts[6] * 6;
            case "threeKind":
                return maxCount >= 3 ? sum : 0;
            case "fourKind":
                return maxCount >= 4 ? sum : 0;
            case "fullHouse":
                return counts.includes(3) && counts.includes(2) ? 25 : 0;
            case "smallStraight":
                return hasStraight(values, 4) ? 30 : 0;
            case "largeStraight":
                return hasStraight(values, 5) ? 40 : 0;
            case "yahtzee":
                return maxCount === 5 ? 50 : 0;
            case "chance":
                return sum;
            default:
                return 0;
        }
    }

    function chooseCategory(key) {
        if (gameOver || rollCount === 0 || scores[key] !== undefined) {
            return;
        }

        scores[key] = scoreFor(key);
        rollCount = 0;
        locks = Array(5).fill(false);
        dice = Array(5).fill(null);

        if (Object.keys(scores).length >= categories.length) {
            gameOver = true;
            setStatus("게임 종료입니다. 최종 점수를 확인하세요.");
        } else {
            setStatus("다음 라운드를 위해 주사위를 굴리세요.");
        }

        render();
    }

    function totals() {
        let upper = 0;
        let lower = 0;

        categories.forEach((category) => {
            const score = scores[category.key];
            if (score === undefined) {
                return;
            }
            if (category.section === "upper") {
                upper += score;
            } else {
                lower += score;
            }
        });

        const bonus = upper >= 63 ? 35 : 0;
        return { upper, lower, bonus, total: upper + lower + bonus };
    }

    function render() {
        const scoredCount = Object.keys(scores).length;
        const round = Math.min(scoredCount + 1, categories.length);

        roundEl.textContent = `라운드 ${round} / ${categories.length}`;
        rollsEl.textContent = `굴림: ${rollCount} / 3`;
        rollBtn.disabled = gameOver || rollCount >= 3;

        diceEls.forEach((die, index) => {
            die.textContent = dice[index] ? String(dice[index]) : "-";
            die.classList.toggle("locked", locks[index]);
            die.disabled = gameOver || rollCount === 0;
        });

        sheetEl.innerHTML = "";
        categories.forEach((category) => {
            const row = document.createElement("button");
            row.type = "button";
            row.className = "yahtzee-row";
            row.dataset.key = category.key;
            const scored = scores[category.key] !== undefined;
            const preview = scoreFor(category.key);
            const valueText = scored ? scores[category.key] : rollCount === 0 ? "-" : preview;
            row.disabled = gameOver || scored || rollCount === 0;
            row.innerHTML = `<span>${category.label}</span><span>${valueText}</span>`;
            sheetEl.appendChild(row);
        });

        const { upper, lower, bonus, total } = totals();
        totalsEl.innerHTML = [
            `<div>상단 합계: ${upper}</div>`,
            `<div>상단 보너스(63점 이상): ${bonus}</div>`,
            `<div>하단 합계: ${lower}</div>`,
            `<div>총점: ${total}</div>`,
        ].join("");
    }

    diceEls.forEach((die) => {
        die.addEventListener("click", () => {
            toggleLock(Number(die.dataset.index));
        });
    });

    sheetEl.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-key]");
        if (!button) {
            return;
        }
        chooseCategory(button.dataset.key);
    });

    rollBtn.addEventListener("click", rollDice);
    resetBtn.addEventListener("click", resetGame);
    resetGame();
})();
