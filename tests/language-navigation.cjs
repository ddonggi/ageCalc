const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.I18N_TEST_BASE || 'http://127.0.0.1:8000';

(async () => {
    const browser = await chromium.launch({headless: true});
    try {
        for (const width of [320, 375, 1280]) {
            const context = await browser.newContext({viewport: {width, height: 900}});
            await context.route('**/*', route => new URL(route.request().url()).origin === base
                ? route.continue() : route.abort());
            const page = await context.newPage();
            for (const path of ['/', '/age', '/annual-age-calculator', '/about', '/blog', '/en/age-calculator', '/ja/birthday-dday-calculator']) {
                const response = await page.goto(base + path);
                assert.equal(response.status(), 200, path);
                const menu = page.locator('.language-switcher');
                const trigger = menu.locator('summary');
                assert.ok(await trigger.isVisible(), path);
                await trigger.click();
                assert.equal(await menu.locator('nav a').count(), 6);
                const box = await menu.locator('nav').boundingBox();
                assert.ok(box.x >= 0 && box.x + box.width <= width, `${width} ${path}: menu overflows ${JSON.stringify(box)}`);
                assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `${width} ${path}: page overflows`);
                await page.keyboard.press('Escape');
                assert.equal(await menu.getAttribute('open'), null);
                assert.ok(await trigger.evaluate(el => el === document.activeElement));
                await trigger.click();
                await page.mouse.click(2, 500);
                assert.equal(await menu.getAttribute('open'), null);
                if (path === '/' && width === 375) {
                    await trigger.click();
                    await page.screenshot({path: '/tmp/agecalc-language-home.png'});
                    await menu.locator('a[hreflang="en"]').click();
                    assert.equal(new URL(page.url()).pathname, '/en/age-calculator');
                }
            }
            await context.close();
        }
        const context = await browser.newContext({javaScriptEnabled: false, viewport: {width: 375, height: 900}});
        const page = await context.newPage();
        await page.goto(base + '/annual-age-calculator');
        await page.locator('.language-switcher summary').click();
        await page.locator('.language-switcher a[hreflang="ja"]').click();
        assert.equal(new URL(page.url()).pathname, '/ja/age-calculator');
        await context.close();
        console.log('PASS language menu: 21 page/viewport checks, fallback navigation, Escape, outside click and JS-off links');
    } finally {
        await browser.close();
    }
})().catch(error => {console.error(error); process.exitCode = 1;});
