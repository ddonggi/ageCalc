(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    }
    if (root && root.document) {
        root.AgeCalcReadingProgress = api;
        api.init(root, root.document);
    }
})(typeof window !== 'undefined' ? window : null, function () {
    const MILESTONES = [25, 50, 75, 100];

    const calculateProgress = (scrollY, articleTop, articleHeight, viewportHeight) => {
        const readableDistance = articleHeight - viewportHeight;
        if (readableDistance <= 0) {
            return scrollY >= articleTop ? 100 : 0;
        }
        const percentage = ((scrollY - articleTop) / readableDistance) * 100;
        return Math.max(0, Math.min(100, Math.round(percentage)));
    };

    const newMilestones = (percentage, sent) =>
        MILESTONES.filter((milestone) => percentage >= milestone && !sent.has(milestone));

    const init = (browserWindow, browserDocument) => {
        const progress = browserDocument.querySelector('[data-reading-progress]');
        const fill = browserDocument.querySelector('[data-reading-progress-fill]');
        const article = browserDocument.querySelector('[data-reading-progress-target]');
        if (!progress || !fill || !article) return;

        const sent = new Set();
        let frameRequested = false;

        const update = () => {
            frameRequested = false;
            const bounds = article.getBoundingClientRect();
            const articleTop = bounds.top + browserWindow.scrollY;
            const percentage = calculateProgress(
                browserWindow.scrollY,
                articleTop,
                article.offsetHeight,
                browserWindow.innerHeight
            );
            fill.style.transform = `scaleX(${percentage / 100})`;
            progress.setAttribute('aria-valuenow', String(percentage));
            progress.classList.add('is-ready');

            newMilestones(percentage, sent).forEach((milestone) => {
                const tracked = browserWindow.AgeCalcTracking?.trackEvent?.('reading_progress', {
                    percent: milestone,
                    content_type: article.dataset.contentType,
                    page_path: browserWindow.location.pathname,
                });
                if (tracked) sent.add(milestone);
            });
        };

        const scheduleUpdate = () => {
            if (frameRequested) return;
            frameRequested = true;
            browserWindow.requestAnimationFrame(update);
        };

        browserWindow.addEventListener('scroll', scheduleUpdate, { passive: true });
        browserWindow.addEventListener('resize', scheduleUpdate);
        browserWindow.addEventListener('agecalc:tracking-ready', scheduleUpdate);
        if (typeof browserWindow.ResizeObserver === 'function') {
            new browserWindow.ResizeObserver(scheduleUpdate).observe(article);
        }
        scheduleUpdate();
    };

    return { calculateProgress, newMilestones, init };
});
