// Result links also work in server-rendered pages without JavaScript.
(() => {
    const nav = document.querySelector('[data-related-tools]');
    if (!nav) return;

    // SubmitEvent omits the click modifiers. Carry them through the button's
    // native activation so focus, analytics and result reuse all defer to the browser.
    document.addEventListener('click', click => {
        if (!click.isTrusted || !(click.metaKey || click.ctrlKey || click.shiftKey || click.altKey)) return;
        const button = click.target.closest('button, input');
        const form = button?.form;
        if (!form?.matches('form[data-calculator-form]') || !['submit', 'image'].includes(button.type)) return;

        const mark = submit => {
            if (submit.submitter === button && !click.defaultPrevented) submit.ageCalcModifiedSubmit = true;
        };
        form.addEventListener('submit', mark, {once: true});
        // Invalid or cancelled clicks may finish without dispatching submit.
        window.setTimeout(() => form.removeEventListener('submit', mark), 0);
    }, true);

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

        // A GET of the current query with a result fragment stays in this
        // document. There is no new server response to publish its completion.
        window.addEventListener('submit', event => {
            const form = event.target;
            if (!event.isTrusted || event.defaultPrevented || event.ageCalcModifiedSubmit || !form.matches('form[data-calculator-form]')
                || form.method !== 'get' || (form.target && form.target !== '_self')) return;
            const button = event.submitter;
            if (button?.matches('[formaction], [formmethod], [formtarget]')) return;
            const action = new URL(form.action);
            if (!action.hash || action.origin !== location.origin || action.pathname !== location.pathname) return;
            action.search = new URLSearchParams(new FormData(form, button));
            if (action.search !== location.search) return;

            const result = document.getElementById(action.hash.slice(1));
            if (!result?.getClientRects().length) {
                // The calculator discarded the rendered result on edit. Let the
                // browser request it again instead of jumping to a hidden anchor.
                const originalAction = form.getAttribute('action');
                form.action = action.pathname;
                window.setTimeout(() => form.setAttribute('action', originalAction), 0);
                return;
            }
            event.preventDefault();
            location.hash = action.hash;
            document.dispatchEvent(new Event('agecalc:result-completed'));
        });
    }
})();
