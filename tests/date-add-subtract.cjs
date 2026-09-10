const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.I18N_TEST_BASE || 'http://127.0.0.1:8000';

(async () => {
    const browser = await chromium.launch({headless: true});
    try {
        for (const prefix of ['', '/en', '/ja', '/es', '/pt-br', '/zh-cn']) {
            const context = await browser.newContext({viewport: {width: 375, height: 900}});
            await context.addCookies([{name: 'cookieConsent', value: 'rejected', url: base}]);
            const requests = [];
            await context.route('**/*', route => {
                requests.push({url: route.request().url(), body: route.request().postData()});
                return route.request().url().startsWith(base) ? route.continue() : route.abort();
            });
            const page = await context.newPage();
            const response = await page.goto(base + prefix + '/date-add-subtract-calculator');
            assert.equal(response.status(), 200, prefix);
            await page.locator('#calculator-unavailable').waitFor({state: 'hidden'});
            const fillStart = async (year, month, day) => {
                await page.locator('#start-year').fill(year);
                await page.locator('#start-month').selectOption(month);
                await page.locator('#start-day').fill(day);
            };
            const calculate = async () => page.locator('#global-calculator button[type="submit"]').click();
            const resultValue = key => page.locator(`[data-result-key="${key}"] dd`).innerText();
            const thursday = {'': '목요일', '/en': 'Thursday', '/ja': '木曜日', '/es': 'jueves', '/pt-br': 'quinta-feira', '/zh-cn': '星期四'}[prefix];

            await fillStart('2024', '1', '31');
            await page.locator('#shift-amount').fill('1');
            await page.locator('#shift-unit').selectOption('month');
            requests.length = 0;
            await calculate();
            assert.match(await resultValue('result_date'), /2024/);
            assert.match(await resultValue('result_date'), /29/);
            assert.ok((await resultValue('result_date')).toLocaleLowerCase().includes(thursday.toLocaleLowerCase()), prefix + ' weekday');
            assert.equal((await resultValue('calendar_days_moved')).match(/\d+/g).join(''), '29');

            await page.locator('[name="operation"][value="subtract"]').check();
            await page.locator('#shift-amount').fill('2');
            await page.locator('#shift-unit').selectOption('week');
            await calculate();
            assert.match(await resultValue('result_date'), /2024/);
            assert.match(await resultValue('result_date'), /17/);
            assert.equal((await resultValue('calendar_days_moved')).match(/\d+/g).join(''), '14');

            await fillStart('2024', '2', '29');
            await page.locator('[name="operation"][value="add"]').check();
            await page.locator('#shift-amount').fill('1');
            await page.locator('#shift-unit').selectOption('year');
            await calculate();
            assert.match(await resultValue('result_date'), /2025/);
            assert.match(await resultValue('result_date'), /28/);

            await fillStart('9999', '12', '31');
            await page.locator('#shift-unit').selectOption('year');
            await calculate();
            assert.ok(await page.locator('#calculator-error').innerText());
            assert.equal(await page.locator('#global-result').isVisible(), false);

            await page.locator('#shift-amount').fill('-1');
            await calculate();
            assert.ok(await page.locator('#calculator-error').innerText());
            assert.equal(await page.locator('#global-result').isVisible(), false);

            await page.locator('#shift-amount').fill('0');
            await calculate();
            assert.equal(await page.locator('#calculator-error').innerText(), '');
            assert.equal(await page.locator('#global-result').isVisible(), true);
            assert.equal(page.url(), base + prefix + '/date-add-subtract-calculator');
            assert.ok(!requests.some(r => /2024|start_date|shift-amount/.test(r.url + (r.body || ''))), 'private date sent');
            assert.deepEqual(await page.evaluate(() => [localStorage.length, sessionStorage.length]), [0, 0]);
            for (const width of [320, 1280]) {
                await page.setViewportSize({width, height: 900});
                assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), prefix + ' overflow');
            }
            await page.locator('button[type="reset"]').click();
            assert.equal(await page.locator('#start-year').inputValue(), '');
            assert.equal(await page.locator('#shift-amount').inputValue(), '');
            assert.equal(await page.locator('#global-result').isVisible(), false);
            await context.close();
        }
        console.log('PASS six date add/subtract calculators: calendar clamping, subtraction, validation, reset, privacy and responsive layout');
    } finally {
        await browser.close();
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
