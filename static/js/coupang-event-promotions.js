(function () {
    const mobileQuery = window.matchMedia('(max-width: 768px)');

    function distributeMobilePromotions() {
        const slots = Array.from(document.querySelectorAll('[data-event-promo-mobile-slot]'));
        if (!slots.length || !mobileQuery.matches) return;

        const container = document.querySelector('.container') || document.body;
        const anchors = Array.from(container.querySelectorAll(':scope > .section-shell'));
        if (!anchors.length) {
            slots.forEach((slot) => slot.classList.add('is-placed'));
            return;
        }

        slots.forEach((slot, index) => {
            const anchor = anchors[Math.min(index, anchors.length - 1)];
            anchor.insertAdjacentElement('afterend', slot);
            slot.classList.add('is-placed');
        });
    }

    document.addEventListener('DOMContentLoaded', distributeMobilePromotions);
    if (typeof mobileQuery.addEventListener === 'function') {
        mobileQuery.addEventListener('change', distributeMobilePromotions);
    }
})();
