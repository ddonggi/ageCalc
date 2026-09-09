/* Run with PLAYWRIGHT_MODULE pointing to an installed Playwright module. */
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.I18N_TEST_BASE || 'http://127.0.0.1:8123';
const slugs = ['age-calculator', 'birthday-dday-calculator', 'd-day', 'baby-months', '100-day-calculator', 'age-gap-calculator'];

(async () => {
    const browser = await chromium.launch({headless: true});
    try {
        for (const locale of ['en', 'ja', 'es', 'pt-br', 'zh-cn']) {
            const context = await browser.newContext({viewport: {width: 375, height: 812}, timezoneId: 'America/New_York'});
            await context.addCookies([{name: 'cookieConsent', value: 'rejected', url: base}]);
            const page = await context.newPage();
            await page.clock.install({time: new Date('2026-09-09T12:00:00Z')});
            const errors = [];
            page.on('pageerror', error => errors.push(String(error)));
            const requests = [];
            await page.route('**/*', route => {
                requests.push({url: route.request().url(), body: route.request().postData()});
                if (route.request().url().startsWith(base)) return route.continue();
                return route.abort();
            });
            const fillDate = async (name, year, month, day) => {
                if (year) await page.locator(`#${name}-year`).fill(year);
                await page.locator(`#${name}-month`).selectOption(month);
                await page.locator(`#${name}-day`).fill(day);
            };
            for (const slug of slugs) {
                const response = await page.goto(`${base}/${locale}/${slug}`);
                assert.equal(response.status(), 200);
                await page.locator('#calculator-unavailable').waitFor({state: 'hidden'});
                assert.equal(await page.locator('h1').count(), 1);
                assert.equal(await page.locator('.language-switcher a').count(), 6);
                assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${locale}/${slug}: horizontal overflow`);
                requests.length = 0;
                if (slug === 'age-calculator') {
                    await fillDate('birth', '1992', '10', '2');
                    await page.locator('[value="specific"]').check();
                    await fillDate('reference', '2026', '10', '2');
                } else if (slug === 'birthday-dday-calculator') {
                    await fillDate('birthday', null, '9', '9');
                } else if (slug === 'd-day') {
                    await fillDate('target', '2026', '9', '10');
                    await page.locator('#event-label').fill('<img src=x onerror=alert(1)>');
                } else if (slug === 'baby-months') {
                    await fillDate('birth', '2025', '1', '31');
                } else if (slug === '100-day-calculator') {
                    await fillDate('start', '2026', '1', '1');
                } else {
                    await page.locator('#year_a').selectOption('1990');
                    await page.locator('#year_b').selectOption('1995');
                }
                await page.locator('button[type="submit"]').click();
                await page.locator('#global-result').waitFor({state: 'visible'});
                assert.equal(await page.locator('#calculator-error').innerText(), '');
                const result = await page.locator('#result-values').innerText();
                const expected = {'age-calculator': '34', 'birthday-dday-calculator': '0', 'd-day': '1', 'baby-months': '19', '100-day-calculator': '2026', 'age-gap-calculator': '5'};
                assert.ok(result.includes(expected[slug]), `${locale}/${slug}: ${result}`);
                if (slug === 'd-day') {
                    const previousTitle = await page.locator('#result-title').innerText();
                    await page.locator('[name="mode"][value="since"]').check();
                    await page.locator('button[type="submit"]').click();
                    assert.notEqual(await page.locator('#result-title').innerText(), previousTitle);
                }
                assert.equal(await page.locator('#global-result img').count(), 0, 'result text must not become executable HTML');
                assert.equal(page.url(), `${base}/${locale}/${slug}`, 'calculations must not change URL');
                assert.ok(!requests.some(r => /1992|1990|1995|2025|birth_date|year_a|onerror/.test(r.url + (r.body || ''))), 'private input sent over network');
                assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0]);
                assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${locale}/${slug}: result overflow`);
                if (slug === 'age-calculator') {
                    await page.locator('#birth-month').selectOption('2');
                    await page.locator('#birth-day').fill('30');
                    await page.locator('button[type="submit"]').click();
                    assert.notEqual(await page.locator('#calculator-error').innerText(), '');
                    assert.equal(await page.locator('#global-result').isVisible(), false);
                    await page.locator('button[type="reset"]').click();
                    assert.equal(await page.locator('#birth-year').inputValue(), '');
                }
                console.log(`PASS ${locale}/${slug}`);
            }
            assert.deepEqual(errors, []);
            await page.locator('.language-switcher summary').click();
            await page.locator('.language-switcher a[lang="ko"]').click();
            assert.equal(page.url(), `${base}/age-gap-calculator`);
            await context.close();
        }
        const nojs = await browser.newContext({javaScriptEnabled: false, viewport: {width: 375, height: 812}});
        const nojsPage = await nojs.newPage();
        await nojsPage.route('**/*', route => route.request().url().startsWith(base) ? route.continue() : route.abort());
        await nojsPage.goto(`${base}/en/age-calculator`);
        assert.equal(await nojsPage.locator('h1').innerText(), 'Age Calculator');
        assert.equal(await nojsPage.locator('#calculator-unavailable').isVisible(), true);
        assert.equal(await nojsPage.locator('#birth-year').isDisabled(), true);
        await nojsPage.locator('.language-switcher summary').click();
        await nojsPage.locator('.language-switcher a[lang="ja"]').click();
        assert.equal(await nojsPage.locator('html').getAttribute('lang'), 'ja');
        await nojs.close();
        const desktop = await browser.newContext({viewport: {width: 1440, height: 1000}});
        await desktop.addCookies([{name: 'cookieConsent', value: 'rejected', url: base}]);
        const page = await desktop.newPage();
        await page.route('**/*', route => route.request().url().startsWith(base) ? route.continue() : route.abort());
        await page.goto(`${base}/en/age-calculator`);
        await page.screenshot({path: '/tmp/agecalc-i18n-desktop.png', fullPage: true});
        await page.setViewportSize({width: 375, height: 812});
        await page.goto(`${base}/ja/age-calculator`);
        await page.screenshot({path: '/tmp/agecalc-i18n-mobile.png', fullPage: true});
        await page.goto(`${base}/age`);
        assert.equal(await page.locator('h1').innerText(), '만나이 계산기');
        assert.equal(await page.locator('#birth-input').count(), 1);
        await page.locator('.language-switcher summary').click();
        await page.screenshot({path: '/tmp/agecalc-i18n-korean.png'});
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), 'Korean language selector overflow');
        await desktop.close();
        console.log('PASS 30 browser flows, JS-off language navigation, privacy and responsive checks');
    } finally {
        await browser.close();
    }
})().catch(error => {console.error(error); process.exitCode = 1;});
