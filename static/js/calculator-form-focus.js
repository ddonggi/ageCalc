(function () {
  "use strict";

  var calculatorFormSelector = "body.home-page #home-age-form, body.calculator-flat-page form";
  var supportedInputTypes = new Set(["text", "search", "tel", "url", "email", "number", "date", "password"]);

  function hasResultAnchor() {
    if (!window.location.hash) {
      return false;
    }

    var resultTarget = document.getElementById(window.location.hash.slice(1));
    return Boolean(resultTarget && (resultTarget.classList.contains("show") || !resultTarget.hasAttribute("hidden")));
  }

  function isSupportedInput(element) {
    return (
      element instanceof HTMLInputElement &&
      !element.disabled &&
      !element.readOnly &&
      supportedInputTypes.has(element.type)
    );
  }

  function focusFirstCalculatorInput() {
    if (hasResultAnchor()) {
      return;
    }

    var form = document.querySelector(calculatorFormSelector);
    if (!form) {
      return;
    }

    var input = Array.prototype.find.call(form.elements, isSupportedInput);
    if (!input) {
      return;
    }

    try {
      input.focus({ preventScroll: true });
    } catch (error) {
      input.focus();
    }
  }

  function submitOnEnter(event) {
    if (
      event.key !== "Enter" ||
      event.isComposing ||
      event.shiftKey ||
      event.ctrlKey ||
      event.altKey ||
      event.metaKey ||
      !isSupportedInput(event.target)
    ) {
      return;
    }

    var form = event.target.closest("form");
    if (!form || !form.matches(calculatorFormSelector)) {
      return;
    }

    event.preventDefault();
    form.requestSubmit();
  }

  function scrollToCalculationResult(form) {
    var targetId = "";
    try { targetId = new URL(form.action, window.location.href).hash.slice(1); } catch (error) {}
    var target = targetId ? document.getElementById(targetId) : null;
    if (!target) {
      target = form.closest(".editorial-calculator-shell")?.querySelector(".result-container.show, [id$='-result']:not([hidden]), .result-container");
    }
    if (!target) return;
    window.setTimeout(function () {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      target.setAttribute("tabindex", "-1");
      try { target.focus({ preventScroll: true }); } catch (error) { target.focus(); }
    }, 0);
  }

  function reorderTableSections() {
    if (!document.body || !document.body.classList.contains("calculator-flat-page")) return;
    var calculator = document.querySelector(".editorial-calculator-shell");
    var directAnswer = document.querySelector(".direct-answer");
    if (!calculator || !directAnswer) return;
    var tableSections = Array.from(document.querySelectorAll("table.data-table"))
      .map(function (table) { return table.closest("section"); })
      .filter(function (section, index, sections) { return section && sections.indexOf(section) === index; });
    var anchor = calculator;
    tableSections.forEach(function (section) { anchor.after(section); anchor = section; });
    anchor.after(directAnswer);
  }

  function scrollToLoadedResult() {
    if (!window.location.search || !document.body || !document.body.classList.contains("calculator-flat-page")) return;
    var target = document.querySelector(".result-container.show, [id$='-result']:not([hidden]), table.data-table");
    if (!target) return;
    target = target.closest("section") || target;
    window.setTimeout(function () { target.scrollIntoView({ behavior: "smooth", block: "start" }); }, 0);
  }

  document.addEventListener("DOMContentLoaded", function () {
    focusFirstCalculatorInput();
    reorderTableSections();
    scrollToLoadedResult();
  });
  document.addEventListener("keydown", submitOnEnter);
  document.addEventListener("submit", function (event) {
    var form = event.target;
    if (form && form.matches(calculatorFormSelector)) scrollToCalculationResult(form);
  });
}());
