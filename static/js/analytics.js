(function () {
    const CONFIG_ID = 'tracking-config';
    const GA_SCRIPT_ID = 'ga-loader';
    const CLARITY_SCRIPT_ID = 'clarity-loader';
    let googleAnalyticsReady = false;
    const sensitiveQueryKeys = new Set(['birth_date', 's', 'token', 'review_token']);
    const url = new URL(window.location.href);
    let removedSensitiveValue = false;
    Array.from(url.searchParams.keys()).forEach((key) => {
        if (sensitiveQueryKeys.has(key) || /^[pc]\d+(?:b|y|m|d)$/.test(key)) {
            url.searchParams.delete(key);
            removedSensitiveValue = true;
        }
    });
    const calculator = document.querySelector?.('[data-related-tools]');
    if (removedSensitiveValue) {
        window.history.replaceState({}, document.title, `${url.pathname}${url.search}${url.hash}`);
    }
    const pathOnly = calculator || document.body?.dataset.analyticsPathOnly === 'true';
    const cleanPageLocation = url.origin + url.pathname + (pathOnly ? '' : url.search);
    function cleanReferrer() {
        try {
            const previous = new URL(document.referrer);
            if (!['https:', 'http:'].includes(previous.protocol)) return '';
            return previous.origin === url.origin ? previous.origin + previous.pathname : previous.origin;
        } catch {
            return '';
        }
    }

    const getCookie = (key) =>
        document.cookie.split('; ').find((row) => row.startsWith(key + '='))?.split('=')[1];

    const readConfig = () => {
        const node = document.getElementById(CONFIG_ID);
        if (!node) return null;
        try {
            return JSON.parse(node.textContent || '{}');
        } catch (error) {
            console.warn('tracking config parse failed', error);
            return null;
        }
    };

    const loadScriptOnce = (id, src, onLoad) => {
        const existing = document.getElementById(id);
        if (existing) {
            if (onLoad) {
                if (existing.dataset.loaded === 'true') {
                    onLoad();
                } else {
                    existing.addEventListener('load', onLoad, { once: true });
                }
            }
            return;
        }

        const script = document.createElement('script');
        script.id = id;
        script.async = true;
        script.src = src;
        if (onLoad) {
            script.addEventListener('load', () => {
                script.dataset.loaded = 'true';
                onLoad();
            }, { once: true });
        }
        document.head.appendChild(script);
    };

    const initGoogleAnalytics = (measurementId) => {
        window.dataLayer = window.dataLayer || [];
        window.gtag = window.gtag || function gtag() {
            window.dataLayer.push(arguments);
        };
        // Consent may have changed in another tab while the loader was pending.
        const accepted = getCookie('cookieConsent') === 'accepted';
        const storage = accepted ? 'granted' : 'denied';
        window.gtag('consent', 'update', {
            analytics_storage: storage,
            ad_storage: storage,
            ad_user_data: storage,
            ad_personalization: storage,
        });
        if (!accepted) {
            window.__agecalcTrackingInitialized = false;
            return;
        }
        window.gtag('js', new Date());
        window.gtag('config', measurementId, {
            anonymize_ip: true,
            page_location: cleanPageLocation,
            page_referrer: cleanReferrer(),
            ...(calculator && window.location.search && {page_title: calculator.dataset.source}),
            page_path: window.location.pathname,
        });
        googleAnalyticsReady = true;
        if (typeof window.dispatchEvent === 'function' && typeof window.Event === 'function') {
            window.dispatchEvent(new window.Event('agecalc:tracking-ready'));
        }
    };

    const initClarity = (projectId) => {
        if (window.clarity || !projectId) {
            return;
        }
        (function (c, l, a, r, i, t, y) {
            c[a] = c[a] || function () { (c[a].q = c[a].q || []).push(arguments); };
            t = l.createElement(r);
            t.async = 1;
            t.src = "https://www.clarity.ms/tag/" + i;
            t.id = CLARITY_SCRIPT_ID;
            y = l.getElementsByTagName(r)[0];
            y.parentNode.insertBefore(t, y);
        })(window, document, "clarity", "script", projectId);
    };

    const init = () => {
        if (window.__agecalcTrackingInitialized) {
            return;
        }
        if (getCookie('cookieConsent') !== 'accepted') {
            return;
        }
        const config = readConfig();
        if (!config) {
            return;
        }

        window.__agecalcTrackingInitialized = true;
        if (config.ga_measurement_id) {
            loadScriptOnce(
                GA_SCRIPT_ID,
                `https://www.googletagmanager.com/gtag/js?id=${encodeURIComponent(config.ga_measurement_id)}`,
                () => initGoogleAnalytics(config.ga_measurement_id)
            );
        }
        if (config.clarity_project_id && document.body?.dataset.disableClarity !== 'true') {
            initClarity(config.clarity_project_id);
        }
    };

    const trackEvent = (name, params = {}) => {
        if (getCookie('cookieConsent') !== 'accepted') {
            return false;
        }
        init();
        if (!googleAnalyticsReady || typeof window.gtag !== 'function') {
            return false;
        }
        window.gtag('event', name, params);
        return true;
    };

    // A handoff exists in storage only between leaving a document and starting
    // the next one. Opening or duplicating a tab cannot copy a live attribution.
    const handoffKey = 'agecalc.related.handoff.v1';
    const ttl = 30 * 60 * 1000;
    function takeHandoff() {
        try {
            const raw = window.sessionStorage.getItem(handoffKey);
            window.sessionStorage.removeItem(handoffKey);
            return JSON.parse(raw);
        } catch {
            return null;
        }
    }
    function fresh(timestamp) {
        const elapsed = Date.now() - timestamp;
        return Number.isFinite(timestamp) && elapsed >= 0 && elapsed < ttl;
    }

    // A rejection in another open tab invalidates in-memory, consented work even
    // if the user accepts again before this tab is focused.
    let consentChannel;
    try {
        if (window.BroadcastChannel) consentChannel = new window.BroadcastChannel('agecalc.analytics.consent');
    } catch { /* Restricted contexts can still check the consent cookie on every action. */ }
    document.addEventListener?.('click', event => {
        if (event.target.closest('#reject-cookies')) consentChannel?.postMessage('rejected');
    });

    function measureCalculator(nav) {
        const source = nav.dataset.source;
        const locale = nav.dataset.locale;
        const layout = nav.dataset.layout === 'baseline' ? 'baseline' : 'cards';
        const base = {source_tool: source, locale, placement_version: layout};
        const accepted = () => getCookie('cookieConsent') === 'accepted';
        const activeTab = () => document.visibilityState === 'visible' && document.hasFocus();
        let deferred = [];
        let outgoing = null;
        let incoming = null;
        let run = null;
        let observer = null;
        const timers = new Map();

        function cards() {
            const links = layout === 'baseline'
                ? document.querySelectorAll('[data-baseline-tools] a[data-tool]')
                : nav.querySelectorAll('a[data-tool]');
            return Array.from(links).filter(link => link.getClientRects().length);
        }

        // Only these fixed dimensions cross documents or enter custom events.
        // Reconstruct pending payloads, including after a storage read.
        function dimensions(params) {
            if (!params || typeof params.source_tool !== 'string' || !/^[a-z_]{1,64}$/.test(params.source_tool)
                || !['ko', 'en', 'ja', 'es', 'pt-br', 'zh-cn'].includes(params.locale?.toLowerCase?.())
                || !['baseline', 'cards'].includes(params.placement_version)
                || typeof params.measurable !== 'boolean') return null;
            const result = {
                source_tool: params.source_tool, locale: params.locale,
                placement_version: params.placement_version, measurable: params.measurable,
            };
            if (params.destination_tool !== undefined) {
                if (!/^[a-z_]{1,64}$/.test(params.destination_tool)
                    || !Number.isInteger(params.card_rank) || params.card_rank < 1) return null;
                result.destination_tool = params.destination_tool;
                result.card_rank = params.card_rank;
            }
            return result;
        }
        function send(name, params) {
            if (!accepted()) return;
            if (!trackEvent(name, params)) deferred.push({name, params});
        }
        function flush() {
            const events = deferred;
            deferred = [];
            for (const {name, params} of events) send(name, params);
        }
        function stopObserving() {
            observer?.disconnect();
            observer = null;
            for (const timer of timers.values()) window.clearTimeout(timer);
            timers.clear();
        }
        function clearRun() {
            stopObserving();
            run = null;
            outgoing = null;
        }
        function forget() {
            clearRun();
            incoming = null;
            deferred = [];
            takeHandoff();
        }
        function recordImpression(link) {
            const params = run?.links.get(link);
            if (!params || !activeTab() || !accepted() || run.seen.has(params.destination_tool)) return;
            run.seen.add(params.destination_tool);
            send('related_tool_impression', params);
        }
        function observe() {
            stopObserving();
            if (!run || !activeTab() || !window.IntersectionObserver) return;
            const current = new window.IntersectionObserver(entries => {
                if (observer !== current) return;
                for (const entry of entries) {
                    const link = entry.target;
                    window.clearTimeout(timers.get(link));
                    timers.delete(link);
                    if (entry.isIntersecting && entry.intersectionRatio >= 0.5) {
                        timers.set(link, window.setTimeout(() => {
                            timers.delete(link);
                            recordImpression(link);
                        }, 1000));
                    }
                }
            }, {threshold: 0.5});
            observer = current;
            for (const link of run.links.keys()) current.observe(link);
        }
        function completed() {
            clearRun();
            if (!accepted()) { forget(); return; }
            // Baseline results can link to the same tool once per child. Both
            // exposure and activation use that destination's first visible position.
            const firstRank = new Map();
            const links = new Map();
            cards().forEach((link, index) => {
                const tool = link.dataset.tool;
                if (!firstRank.has(tool)) firstRank.set(tool, index + 1);
                links.set(link, {
                    ...base, destination_tool: tool, card_rank: firstRank.get(tool),
                    measurable: link.dataset.measurable === 'true',
                });
            });
            run = {links, seen: new Set(), clicked: new Set()};
            send('calculator_completed', {
                ...base, measurable: [...links.values()].some(item => item.measurable),
            });
            if (incoming && fresh(incoming.time)) send('related_calculator_completed', incoming.params);
            incoming = null;
            observe();
        }

        const marker = takeHandoff();
        const navigation = window.performance.getEntriesByType('navigation')[0];
        if (accepted() && navigation?.type === 'navigate' && marker?.tool === source
            && marker.locale === locale && fresh(marker.time)) {
            const previous = dimensions(marker.click?.params);
            if (previous?.destination_tool === source && previous.locale === locale
                && previous.measurable && fresh(marker.click.time)) {
                incoming = {params: previous, time: marker.click.time};
            }
            const names = ['calculator_completed', 'related_tool_impression', 'related_tool_click', 'related_calculator_completed'];
            for (const event of Array.isArray(marker.deferred) ? marker.deferred : []) {
                const params = dimensions(event?.params);
                if (params && names.includes(event.name)) send(event.name, params);
            }
            if (marker.submitted && nav.dataset.ssrSuccess === 'true') completed();
        }

        function canLink(event, link, params) {
            if (!params.measurable || event.button !== 0 || event.ctrlKey || event.metaKey
                || event.altKey || event.shiftKey || (link.target && link.target !== '_self')
                || link.hasAttribute('download') || new URL(link.href).origin !== url.origin) return false;
            try {
                // Check writes here so a privacy mode or full store is excluded from
                // the linked-click denominator. The actual marker is written on exit.
                window.sessionStorage.setItem(handoffKey, '');
                window.sessionStorage.removeItem(handoffKey);
                return true;
            } catch {
                return false;
            }
        }
        function activate(event) {
            outgoing = null;
            if (!accepted()) { forget(); return; }
            if (!event.isTrusted || event.defaultPrevented || !run || !activeTab()) return;
            const link = event.target.closest('a[data-tool]');
            const params = run.links.get(link);
            if (!params || !link.getClientRects().length || run.clicked.has(params.destination_tool)) return;
            if (event.type === 'click' ? event.button !== 0 : event.button !== 1) return;
            recordImpression(link);
            const linked = canLink(event, link, params);
            send('related_tool_click', {...params, measurable: linked});
            run.clicked.add(params.destination_tool);
            if (linked) {
                outgoing = {tool: params.destination_tool, click: {params, time: Date.now()}, event};
            }
        }
        document.addEventListener('click', event => {
            if (event.target.closest('#reject-cookies')) { forget(); return; }
            activate(event);
        });
        document.addEventListener('auxclick', activate);
        window.addEventListener('submit', event => {
            outgoing = null;
            const form = event.target;
            if (!accepted() || !event.isTrusted || event.defaultPrevented
                || !form.matches('form[data-calculator-form]')) return;
            const target = event.submitter?.getAttribute('formtarget') ?? form.target;
            if (target && target !== '_self') return;
            outgoing = {tool: source, submitted: true, click: incoming, event};
        });
        window.addEventListener('pagehide', () => {
            if (accepted() && outgoing && !outgoing.event.defaultPrevented) {
                const {tool, submitted, click} = outgoing;
                try {
                    window.sessionStorage.setItem(handoffKey, JSON.stringify({
                        tool, locale, submitted, click, time: Date.now(), deferred,
                    }));
                } catch { /* Storage restrictions make this navigation unverifiable. */ }
            }
            clearRun();
            incoming = null;
            deferred = [];
        });
        function visibilityChanged() {
            if (accepted()) observe();
            else forget();
        }
        document.addEventListener('visibilitychange', visibilityChanged);
        window.addEventListener('blur', stopObserving);
        window.addEventListener('focus', visibilityChanged);
        consentChannel?.addEventListener('message', event => {
            if (event.data === 'rejected') forget();
        });
        window.cookieStore?.addEventListener('change', event => {
            if ([...event.changed, ...event.deleted].some(cookie => cookie.name === 'cookieConsent')) {
                visibilityChanged();
            }
        });
        window.addEventListener('agecalc:tracking-ready', flush);
        document.addEventListener('agecalc:result-completed', completed);
        document.addEventListener('agecalc:result-cleared', clearRun);
    }

    if (calculator) {
        // All deferred renderers and baseline annotations are installed first.
        if (document.readyState === 'complete') measureCalculator(calculator);
        else document.addEventListener('DOMContentLoaded', () => measureCalculator(calculator), {once: true});
    } else if (document.querySelector) {
        takeHandoff();
    }

    window.AgeCalcTracking = window.AgeCalcTracking || { init, trackEvent };
    init();
})();
