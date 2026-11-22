// Result links also work in server-rendered pages without JavaScript.
(() => {
    const nav = document.querySelector('[data-related-tools]');
    if (!nav) return;

    if (nav.dataset.layout === 'baseline') {
        const config = nav.querySelector('[data-baseline-destinations]');
        const destinations = config ? JSON.parse(config.textContent) : {};
        document.querySelectorAll('[data-baseline-tools] a[href]').forEach(link => {
            const url = new URL(link.href);
            const destination = destinations[url.pathname];
            if (url.origin === location.origin && url.pathname !== location.pathname && destination) {
                link.dataset.tool = destination.tool;
                link.dataset.measurable = String(destination.measurable);
            }
        });
    }

    document.addEventListener('agecalc:result-completed', () => {
        if (nav.dataset.layout !== 'baseline') {
            nav.hidden = !nav.querySelector('a[data-tool]');
        }
    });
    document.addEventListener('agecalc:result-cleared', () => { nav.hidden = true; });

    // A GET/POST result belongs to the submitted inputs. It becomes stale
    // when a field is edited, even on pages that keep the old result on screen.
    if (nav.dataset.ssrSuccess === 'true') {
        const clear = event => {
            if (event.target.closest('form[data-calculator-form]')) {
                document.dispatchEvent(new Event('agecalc:result-cleared'));
            }
        };
        document.addEventListener('input', clear);
        document.addEventListener('change', clear);
        document.addEventListener('reset', clear);
    }
})();
