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

  document.addEventListener("DOMContentLoaded", focusFirstCalculatorInput);
  document.addEventListener("keydown", submitOnEnter);
}());
