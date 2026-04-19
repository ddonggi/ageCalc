document.addEventListener("DOMContentLoaded", () => {
  const body = document.body;
  const toggleButton = document.querySelector("[data-nav-toggle]");
  const closeButton = document.querySelector("[data-nav-close]");
  const panel = document.querySelector("[data-mobile-nav-panel]");
  const overlay = document.querySelector("[data-mobile-nav-overlay]");
  const groupButtons = document.querySelectorAll("[data-mobile-group-toggle]");

  if (!toggleButton || !panel || !overlay) {
    return;
  }

  const hidePanel = () => {
    panel.hidden = true;
    overlay.hidden = true;
  };

  const showPanel = () => {
    panel.hidden = false;
    overlay.hidden = false;
  };

  const closePanel = ({ returnFocus = true } = {}) => {
    panel.classList.remove("is-open");
    overlay.classList.remove("is-open");
    body.classList.remove("no-scroll");
    toggleButton.setAttribute("aria-expanded", "false");

    window.setTimeout(() => {
      hidePanel();
      if (returnFocus) {
        toggleButton.focus();
      }
    }, 180);
  };

  const openPanel = () => {
    showPanel();
    window.requestAnimationFrame(() => {
      panel.classList.add("is-open");
      overlay.classList.add("is-open");
      body.classList.add("no-scroll");
      toggleButton.setAttribute("aria-expanded", "true");
      if (closeButton) {
        closeButton.focus();
      }
    });
  };

  toggleButton.addEventListener("click", () => {
    if (panel.hidden) {
      openPanel();
      return;
    }
    closePanel();
  });

  if (closeButton) {
    closeButton.addEventListener("click", () => closePanel());
  }

  overlay.addEventListener("click", () => closePanel({ returnFocus: false }));

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) {
      closePanel();
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 980 && !panel.hidden) {
      closePanel({ returnFocus: false });
    }
  });

  groupButtons.forEach((button) => {
    const targetId = button.getAttribute("aria-controls");
    const target = targetId ? document.getElementById(targetId) : null;
    if (!target) {
      return;
    }

    button.addEventListener("click", () => {
      const expanded = button.getAttribute("aria-expanded") === "true";
      button.setAttribute("aria-expanded", expanded ? "false" : "true");
      target.hidden = expanded;
    });
  });
});
