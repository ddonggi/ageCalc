(function () {
    const CONFIG_ID = 'tracking-config';
    const GA_SCRIPT_ID = 'ga-loader';
    const ADSENSE_SCRIPT_ID = 'adsense-loader';
    const CLARITY_SCRIPT_ID = 'clarity-loader';

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
        window.gtag('js', new Date());
        window.gtag('consent', 'update', {
            analytics_storage: 'granted',
            ad_storage: 'granted',
            ad_user_data: 'granted',
            ad_personalization: 'granted',
        });
        window.gtag('config', measurementId, {
            anonymize_ip: true,
        });
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

    const initAdsense = (clientId) => {
        if (!clientId) {
            return;
        }
        loadScriptOnce(
            ADSENSE_SCRIPT_ID,
            `https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=${encodeURIComponent(clientId)}`,
            () => {}
        );
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
        if (config.clarity_project_id) {
            initClarity(config.clarity_project_id);
        }
        if (config.adsense_client) {
            initAdsense(config.adsense_client);
        }
    };

    window.AgeCalcTracking = window.AgeCalcTracking || { init };
    init();
})();
