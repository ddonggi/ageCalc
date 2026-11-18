// Run against a local AgeCalc test server with PLAYWRIGHT_MODULE set when needed.
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.AGECALC_TEST_BASE || 'http://127.0.0.1:8123';
assert.ok(['127.0.0.1', 'localhost'].includes(new URL(base).hostname));

const family = new URL('/parent-child', base);
for (const [parent, child, parentBirth, childBirth] of [
    ['mother', 'daughter', '19800101', '20100101'],
    ['father', 'son', '19820202', '20120202'],
]) {
    family.searchParams.append('parent_role', parent);
    family.searchParams.append('parent_birth', parentBirth);
    family.searchParams.append('child_role', child);
    family.searchParams.append('child_birth', childBirth);
}
family.hash = 'parent-child-result-container';

async function checkConsent(browser, consent) {
    const context = await browser.newContext();
    try {
        if (consent === 'accepted' || consent === 'rejected') {
            await context.addCookies([{name: 'cookieConsent', value: consent, url: base}]);
        }
        let gaRequests = 0;
        let clarityRequests = 0;
        let releaseLoader;
        const delayed = new Promise(resolve => { releaseLoader = resolve; });
        await context.route('**/*', async route => {
            const target = new URL(route.request().url());
            if (target.origin === base) return route.continue();
            if (target.hostname === 'www.googletagmanager.com' && target.pathname === '/gtag/js') {
                gaRequests++;
                if (consent === 'late' || consent === 'withdrawn') await delayed;
                return route.fulfill({contentType: 'text/javascript', body: ''});
            }
            if (target.hostname === 'www.clarity.ms') clarityRequests++;
            return route.abort();
        });
        const page = await context.newPage();
        const response = await page.goto(family.href);
        assert.equal(response.status(), 200);
        assert.equal(await page.locator('#parent-child-result-content .result.success').count(), 4);
        assert.equal(await page.locator('script[src*="/adsbygoogle.js"]').count(), 1);
        if (consent === 'late' || consent === 'withdrawn') {
            assert.equal(gaRequests, 0);
            const otherTab = consent === 'withdrawn' ? await context.newPage() : null;
            if (otherTab) await otherTab.goto(base + '/parent-child');
            await page.locator('#accept-cookies').click();
            await page.evaluate(() => window.AgeCalcTracking.init());
            if (otherTab) {
                await otherTab.locator('#reject-cookies').click();
                assert.ok(await page.evaluate(() => document.cookie.includes('cookieConsent=rejected')));
            }
            releaseLoader();
            if (otherTab) {
                await page.waitForFunction(() => document.querySelector('#ga-loader')?.dataset.loaded === 'true');
                const state = await page.evaluate(() => ({
                    configs: window.dataLayer.filter(args => args[0] === 'config').length,
                    consent: window.dataLayer.filter(args => args[0] === 'consent').at(-1)[2],
                }));
                assert.equal(state.configs, 0);
                assert.ok(Object.values(state.consent).every(value => value === 'denied'));
                await context.addCookies([{name: 'cookieConsent', value: 'accepted', url: base}]);
                await page.evaluate(() => window.AgeCalcTracking.init());
                await otherTab.close();
            }
        }
        if (['accepted', 'late', 'withdrawn'].includes(consent)) {
            await page.waitForFunction(() => window.dataLayer?.some(args => args[0] === 'config'));
            const configs = await page.evaluate(() => window.dataLayer.filter(args => args[0] === 'config').map(args => args[2]));
            assert.equal(configs.length, 1);
            assert.equal(configs[0].page_location, base + '/parent-child');
            assert.equal(gaRequests, 1);
        } else {
            assert.equal(gaRequests, 0);
            assert.equal(await page.locator('#ga-loader').count(), 0);
        }
        assert.equal(clarityRequests, 0);
        if (consent === 'accepted') {
            await page.locator('#parent-child-result-content a[href*="school-grade"]').first().click();
            assert.equal(await page.evaluate(() => document.referrer), '');
            await page.goBack();
            await page.reload();
            assert.equal(await page.locator('#parent-child-result-content .result.success').count(), 4);
            const publicUrl = base + '/college-entry-year-calculator?year=2026';
            await page.goto(publicUrl);
            await page.waitForFunction(() => window.dataLayer?.some(args => args[0] === 'config'));
            const location = await page.evaluate(() => window.dataLayer.find(args => args[0] === 'config')[2].page_location);
            assert.equal(location, publicUrl);
        }
    } finally {
        await context.close();
    }
}

(async () => {
    const browser = await chromium.launch();
    try {
        for (const consent of ['accepted', 'late', 'withdrawn', 'rejected', 'unset']) {
            await checkConsent(browser, consent);
            console.log('PASS family analytics:', consent);
        }
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
