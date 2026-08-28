(function () {
  "use strict";

  var INVALID_DATE_MESSAGE = "올바른 생년월일을 입력하세요.";

  function parseIsoDate(value) {
    var match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value || "");
    if (!match) {
      return null;
    }

    var year = Number(match[1]);
    var monthIndex = Number(match[2]) - 1;
    var day = Number(match[3]);
    var date = new Date(Date.UTC(year, monthIndex, day));

    if (
      date.getUTCFullYear() !== year ||
      date.getUTCMonth() !== monthIndex ||
      date.getUTCDate() !== day
    ) {
      return null;
    }

    return date;
  }

  function isLeapYear(year) {
    return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  }

  function isLeapDayBirthday(birth) {
    return birth.getUTCMonth() === 1 && birth.getUTCDate() === 29;
  }

  function birthdayInYear(birth, year) {
    if (isLeapDayBirthday(birth) && !isLeapYear(year)) {
      return null;
    }

    return new Date(Date.UTC(year, birth.getUTCMonth(), birth.getUTCDate()));
  }

  function calculateDaysToBirthday(birth, today) {
    var millisecondsPerDay = 24 * 60 * 60 * 1000;
    var targetYear = today.getUTCFullYear();
    var nextBirthday = birthdayInYear(birth, targetYear);

    while (!nextBirthday || nextBirthday < today) {
      targetYear += 1;
      nextBirthday = birthdayInYear(birth, targetYear);
    }

    return Math.round((nextBirthday - today) / millisecondsPerDay);
  }

  function calculateSolarAge(birthIso, todayIso) {
    var birth = parseIsoDate(birthIso);
    var today = parseIsoDate(todayIso);

    if (!birth || !today || birth > today) {
      return { ok: false, error: INVALID_DATE_MESSAGE };
    }

    var birthdayPassed =
      today.getUTCMonth() > birth.getUTCMonth() ||
      (
        today.getUTCMonth() === birth.getUTCMonth() &&
        today.getUTCDate() >= birth.getUTCDate()
      );

    return {
      ok: true,
      age: today.getUTCFullYear() - birth.getUTCFullYear() - (birthdayPassed ? 0 : 1),
      daysToBirthday: calculateDaysToBirthday(birth, today)
    };
  }

  function bindHomeAgeCalculator() {
    var form = document.getElementById("home-age-form");
    if (!form) {
      return;
    }

    var input = document.getElementById("home-birth-input");
    var error = document.getElementById("home-birth-error");
    var result = document.getElementById("home-age-result");
    var ageValue = document.getElementById("home-age-value");
    var todayIso = form.getAttribute("data-today");

    if (!input || !error || !result || !ageValue || !todayIso) {
      return;
    }

    form.addEventListener("submit", function (event) {
      event.preventDefault();

      var calculation = calculateSolarAge(input.value, todayIso);
      if (!calculation.ok) {
        input.setAttribute("aria-invalid", "true");
        error.textContent = calculation.error;
        result.hidden = true;
        ageValue.textContent = "";
        return;
      }

      input.removeAttribute("aria-invalid");
      error.textContent = "";
      ageValue.textContent = calculation.age + "세";
      result.hidden = false;
    });
  }

  if (typeof document !== "undefined") {
    document.addEventListener("DOMContentLoaded", bindHomeAgeCalculator);
  }

  if (typeof module !== "undefined") {
    module.exports = { calculateSolarAge: calculateSolarAge };
  }
}());
