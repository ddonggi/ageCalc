// 기준 생일
    const birthDate = new Date("1992-10-02");

    // 오늘 날짜
    const today = new Date();
    const todayStr = today.toISOString().split("T")[0];
    const currentYear = today.getFullYear();

    document.getElementById("today-date").textContent = todayStr;
    document.querySelectorAll(".current-year").forEach(element => {
        element.textContent = currentYear;
    });

    // 만나이 계산
    let manAge = today.getFullYear() - birthDate.getFullYear();
    let exAge = manAge - 1;
    const hasHadBirthday =
        today.getMonth() > birthDate.getMonth() ||
        (today.getMonth() === birthDate.getMonth() && today.getDate() >= birthDate.getDate());
    if (!hasHadBirthday) {
        manAge--;
    }

    // 연 나이
    const yearAge = today.getFullYear() - birthDate.getFullYear();

    // 한국식 나이
    const koreanAge = yearAge + 1;

    // DOM에 반영
    document.querySelector(".ex-age").textContent = exAge;
    document.querySelector(".current-age").textContent = manAge;
    document.getElementById("age-man").textContent = manAge + "세";
    document.getElementById("age-year").textContent = yearAge + "세";
    document.getElementById("age-korean").textContent = koreanAge + "세";
