(() => {
    const banner = document.getElementById('cookie-banner');
    if (!banner) return;

    const getCookie = (key) =>
        document.cookie.split('; ').find(row => row.startsWith(key + '='))?.split('=')[1];

    const setCookie = (key, value, days = 365) => {
        const t = new Date();
        t.setTime(t.getTime() + days * 864e5);
        document.cookie = `${key}=${value};expires=${t.toUTCString()};path=/;SameSite=Lax`;
    };

    const consent = getCookie('cookieConsent');
    if (!consent) {
        banner.classList.add('show');
    }

    banner.querySelector('#accept-cookies')?.addEventListener('click', () => {
        setCookie('cookieConsent', 'accepted');
        banner.classList.remove('show');
    });

    banner.querySelector('#reject-cookies')?.addEventListener('click', () => {
        setCookie('cookieConsent', 'rejected');
        banner.classList.remove('show');
    });
})();
