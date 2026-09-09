document.addEventListener("DOMContentLoaded", () => {
  const desktopPanel = document.querySelector('[data-desktop-nav-panel]');
  const desktopOverlay = document.querySelector('[data-desktop-nav-overlay]');
  const desktopToggle = document.querySelector('[data-desktop-nav-toggle]');
  const desktopClose = document.querySelector('[data-desktop-nav-close]');
  const desktopMedia = window.matchMedia('(min-width: 901px)');
  if (desktopPanel && desktopOverlay && desktopToggle && desktopClose) {
    // Keep fixed positioning relative to the viewport, outside page layout wrappers.
    document.body.append(desktopOverlay, desktopPanel);
    let timer;
    let opened = false;
    const closeDesktop = (returnFocus = true) => {
      opened = false;
      window.clearTimeout(timer);
      desktopPanel.classList.remove('is-open');
      desktopOverlay.classList.remove('is-open');
      desktopToggle.setAttribute('aria-expanded', 'false');
      document.body.classList.remove('desktop-nav-open');
      if (returnFocus) desktopToggle.focus();
      timer = window.setTimeout(() => {
        desktopPanel.hidden = true;
        desktopOverlay.hidden = true;
      }, 220);
    };
    const updateTop = () => {
      const header = document.querySelector('.site-header');
      const top = header ? header.getBoundingClientRect().bottom : 0;
      desktopPanel.style.top = `${top}px`;
      desktopOverlay.style.top = `${top}px`;
    };
    desktopToggle.addEventListener('click', () => {
      if (opened) return closeDesktop();
      if (!desktopMedia.matches) return;
      window.clearTimeout(timer);
      opened = true;
      updateTop();
      desktopPanel.hidden = false;
      desktopOverlay.hidden = false;
      desktopPanel.getBoundingClientRect();
      desktopPanel.classList.add('is-open');
      desktopOverlay.classList.add('is-open');
      desktopToggle.setAttribute('aria-expanded', 'true');
      document.body.classList.add('desktop-nav-open');
      desktopClose.focus();
    });
    desktopClose.addEventListener('click', () => closeDesktop());
    desktopOverlay.addEventListener('click', () => closeDesktop());
    document.addEventListener('keydown', (event) => {
      if (!opened) return;
      if (event.key === 'Escape') closeDesktop();
      if (event.key === 'Tab') {
        const links = desktopPanel.querySelectorAll('a[href], button');
        const first = links[0];
        const last = links[links.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault(); last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault(); first.focus();
        }
      }
    });
    window.addEventListener('resize', () => {
      if (!opened) return;
      if (!desktopMedia.matches) closeDesktop(false);
      else updateTop();
    });
  }
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
    if (desktopMedia.matches) return;
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
  desktopMedia.addEventListener('change', () => {
    if (desktopMedia.matches && !panel.hidden) closePanel({ returnFocus: false });
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !panel.hidden) {
      closePanel();
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
