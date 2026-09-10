const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.I18N_TEST_BASE || 'http://127.0.0.1:8000';
(async () => {
    const browser = await chromium.launch({headless: true});
    try {
        for (const prefix of ['', '/en', '/ja', '/es', '/pt-br', '/zh-cn']) {
            const context = await browser.newContext({viewport: {width: 375, height: 900}, timezoneId: 'America/New_York'});
            await context.addCookies([{name: 'cookieConsent', value: 'rejected', url: base}]);
            const requests = [];
            await context.route('**/*', route => {
                requests.push(route.request().url());
                return route.request().url().startsWith(base) ? route.continue() : route.abort();
            });
            const page = await context.newPage();
            const response = await page.goto(base + prefix + '/days-between-dates');
            assert.equal(response.status(), 200);
            await page.locator('#calculator-unavailable').waitFor({state: 'hidden'});
            const fill = async (name, year, month, day) => {
                await page.locator(`#${name}-year`).fill(year);
                await page.locator(`#${name}-month`).selectOption(month);
                await page.locator(`#${name}-day`).fill(day);
            };
            const calculate = async () => page.locator('#global-calculator button[type="submit"]').click();
            const total = async () => (await page.locator('#result-values dd').first().innerText()).match(/\d+/g).join('');
            await fill('start', '2026', '9', '1');
            await fill('end', '2026', '9', '10');
            requests.length = 0;
            await calculate();
            assert.equal(await total(), '9');
            await page.locator('#include-end').check();
            assert.equal(await page.locator('#global-result').isVisible(), false);
            await calculate();
            assert.equal(await total(), '10');
            assert.equal(await page.locator('#global-result').isVisible(), true);
            await page.locator('#swap-dates').click();
            await calculate();
            assert.ok(await page.locator('#calculator-error').innerText());
            assert.equal(await page.locator('#global-result').isVisible(), false);
            await page.locator('#swap-dates').click();
            await fill('end', '2026', '9', '1');
            await calculate();
            assert.equal(await total(), '1');
            await page.locator('#include-end').uncheck();
            await calculate();
            assert.equal(await total(), '0');
            await fill('start', '2026', '2', '30');
            await calculate();
            assert.ok(await page.locator('#calculator-error').innerText());
            await fill('start', '2024', '2', '28');
            await fill('end', '2024', '3', '1');
            await calculate();
            assert.equal(await total(), '2');
            for (const width of [320, 1280]) {
                await page.setViewportSize({width, height: 900});
                assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), prefix + ' overflow');
            }
            if (!prefix) await page.screenshot({path: '/tmp/agecalc-days-between-ko.png'});
            if (prefix === '/en') {await page.setViewportSize({width: 375, height: 900}); await page.screenshot({path: '/tmp/agecalc-days-between-en.png'});}
            assert.equal(page.url(), base + prefix + '/days-between-dates');
            assert.ok(!requests.some(url => /2024|2026|birth_date|start_date|end_date/.test(url)), 'private dates sent');
            assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0]);
            await page.locator('button[type="reset"]').click();
            assert.equal(await page.locator('#start-year').inputValue(), '');
            assert.equal(await page.locator('#include-end').isChecked(), false);
            assert.equal(await page.locator('#global-result').isVisible(), false);
            await context.close();
        }
        const context = await browser.newContext({javaScriptEnabled: false});
        await context.route('**/*', route => route.request().url().startsWith(base) ? route.continue() : route.abort());
        const page = await context.newPage();
        await page.goto(base + '/days-between-dates');
        assert.equal(await page.locator('#start-year').isDisabled(), true);
        await page.locator('.language-switcher summary').click();
        await page.locator('.language-switcher a[lang="en"]').click();
        assert.equal(new URL(page.url()).pathname, '/en/days-between-dates');
        await context.close();
        console.log('PASS six date-range calculators: inclusive/exclusive, swap, validation, leap day, reset, privacy, responsive layout and JS-off navigation');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
