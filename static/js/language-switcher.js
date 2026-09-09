/* Native details and links remain usable without JavaScript. */
document.querySelectorAll('.language-switcher').forEach((menu) => {
    const trigger = menu.querySelector('summary');
    document.addEventListener('click', (event) => {
        if (menu.open && !menu.contains(event.target)) menu.open = false;
    });
    menu.addEventListener('keydown', (event) => {
        if (event.key === 'Escape' && menu.open) {
            event.preventDefault();
            menu.open = false;
            trigger.focus();
        }
    });
    menu.addEventListener('focusout', () => {
        window.setTimeout(() => {
            if (!menu.contains(document.activeElement)) menu.open = false;
        }, 0);
    });
});
