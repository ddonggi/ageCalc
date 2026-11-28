const assert = require('node:assert/strict');
const { mkdir } = require('node:fs/promises');
const { join } = require('node:path');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');

const base = process.env.AGECALC_TEST_BASE || 'http://127.0.0.1:8137';
assert.ok(['127.0.0.1', 'localhost', '[::1]'].includes(new URL(base).hostname));
const nav = '[data-related-tools]';
const before = process.env.SCREENSHOT_VARIANT === 'before';
const screenshotDir = process.env.SCREENSHOT_DIR;

async function contextFor(browser, consent = 'rejected') {
    const context = await browser.newContext({ locale: 'ko-KR', timezoneId: 'Asia/Seoul', reducedMotion: 'reduce' });
    await context.addCookies([{ name: 'cookieConsent', value: consent, url: base }]);
    await context.route('**/*', route => {
        const url = new URL(route.request().url());
        if (url.origin === base) return route.continue();
        if (url.hostname === 'www.googletagmanager.com' && url.pathname === '/gtag/js') {
            return route.fulfill({ contentType: 'application/javascript', body: '/* local GA loader fixture */' });
        }
        return route.abort();
    });
    return context;
}

async function fillDate(page, field, [year, month, day]) {
    await page.locator('#' + field + '-year').fill(year);
    await page.locator('#' + field + '-month').selectOption(month);
    await page.locator('#' + field + '-day').fill(day);
}

async function capture(page, target, filename) {
    await target.waitFor({ state: 'visible' });
    await page.evaluate(() => document.fonts.ready);
    await target.evaluate(node => node.scrollIntoView({ block: 'center', behavior: 'instant' }));
    if (screenshotDir) {
        await page.screenshot({ path: join(screenshotDir, filename + '.png'), animations: 'disabled' });
    }
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), filename + ' overflow');
}

async function viewports(browser) {
    if (screenshotDir) await mkdir(screenshotDir, { recursive: true });
    const context = await contextFor(browser);
    const page = await context.newPage();
    await page.clock.setFixedTime(new Date('2026-11-22T03:00:00Z'));
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    for (const width of [1440, 768, 390, 320]) {
        await page.setViewportSize({ width, height: 900 });
        await page.goto(base);
        await page.locator('#home-birth-input').fill('19921002');
        await page.locator('#home-age-form button[type=submit]').click();
        const result = page.locator('#home-age-result');
        assert.match(await result.innerText(), /세/);
        assert.equal(await page.locator('#home-grade-link').getAttribute('href'), '/school-grade-calculator?year=1992');
        if (!before) {
            const links = page.locator(nav + ' a[data-tool]');
            assert.equal(await links.count(), 2);
            assert.equal(await links.first().getAttribute('data-tool'), 'birthday_dday_calculator');
            for (const link of await links.all()) {
                const box = await link.boundingBox();
                assert.ok(box && box.height >= 44 && box.width >= 44, 'touch area at ' + width);
            }
            await links.first().focus();
            await page.keyboard.press('Tab');
            assert.ok(await links.last().evaluate(node => document.activeElement === node));
            await links.last().blur();
        }
        await capture(page, before ? result : page.locator(nav), 'home-' + width);
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + '/age?birth_date=19921002&calendar_type=solar');
    await capture(page, page.locator(before ? '.age-result-next' : nav), 'age-390');
    await page.goto(base + '/en/age-calculator');
    await fillDate(page, 'birth', ['1992', '10', '2']);
    await page.locator('#global-calculator button[type=submit]').click();
    await capture(page, page.locator(before ? '#global-result' : nav), 'en-age-390');
    assert.deepEqual(errors, []);
    await context.close();
}

const eventCount = (page, name) => page.evaluate(eventName =>
    (window.dataLayer || []).filter(args => args[0] === 'event' && args[1] === eventName).length, name);

async function tableResultOrder(browser) {
    const context = await contextFor(browser);
    try {
        const page = await context.newPage();
        await page.setViewportSize({ width: 390, height: 844 });
        for (const path of ['/birth-year-age-table?year=2000', '/school-grade-calculator?year=2012']) {
            await page.goto(base + path);
            const panel = page.locator(nav);
            assert.ok(await panel.isVisible());
            const {adjacent, gap} = await panel.evaluate(el => {
                const result = document.querySelector('.birth-year-summary').closest('section');
                return {
                    adjacent: result.nextElementSibling === el,
                    gap: el.getBoundingClientRect().top - result.getBoundingClientRect().bottom,
                };
            });
            assert.ok(adjacent, 'recommendations must immediately follow the rendered result on ' + path);
            assert.ok(gap >= 0 && gap <= 64, 'unexpected result-to-card gap on ' + path + ': ' + gap);
            assert.ok(await page.locator('table.data-table').count() > 0);
        }
    } finally { await context.close(); }
}

async function readableCards(browser) {
    const context = await contextFor(browser);
    await context.clearCookies();
    const page = await context.newPage();
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + '/pt-br/age-calculator');
    await fillDate(page, 'birth', ['1992', '10', '2']);
    await page.locator('#global-calculator button[type=submit]').click();
    const panel = page.locator(nav);
    const snapshot = await panel.ariaSnapshot();
    assert.ok(snapshot.includes('navigation') && snapshot.includes('heading') && snapshot.includes('link'));
    assert.equal(await panel.evaluate(node => !!node.closest('[aria-live]')), false);
    assert.ok(await page.locator('#cookie-banner.show').isVisible());
    // Exercise the recommendation text at 200% with the fixed consent controls present.
    await page.addStyleTag({content: 'html { font-size: 200% !important; }'});
    assert.ok(await page.evaluate(() => parseFloat(getComputedStyle(document.documentElement).fontSize) >= 32));
    for (const link of await panel.locator('a').all()) {
        await link.focus();
        const geometry = await link.evaluate(el => {
            el.scrollIntoView({block: 'center', behavior: 'instant'});
            const box = el.getBoundingClientRect();
            return {
                readable: el.scrollWidth <= el.clientWidth && box.left >= 0 && box.right <= innerWidth,
                reachable: el.contains(document.elementFromPoint(box.left + box.width / 2, box.top + box.height / 2)),
            };
        });
        assert.deepEqual(geometry, {readable: true, reachable: true});
    }
    await page.locator('#reject-cookies').focus();
    await page.keyboard.press('Enter');
    assert.equal(await page.locator('#cookie-banner').isVisible(), false);
    await page.emulateMedia({media: 'print'});
    assert.equal(await panel.isVisible(), false);
    await context.close();
}

async function expectEvent(page, name, count) {
    await page.waitForFunction(([n, c]) => (window.dataLayer || [])
        .filter(args => args[0] === 'event' && args[1] === n).length === c, [name, count], { timeout: 5000 });
}

async function funnel(browser) {
    const context = await contextFor(browser, 'accepted');
    const page = await context.newPage();
    await page.goto(base + '/en/days-between-dates');
    const form = page.locator('#global-calculator');
    await fillDate(page, 'start', ['2024', '2', '29']);
    await fillDate(page, 'end', ['2024', '3', '1']);
    await form.locator('button[type=submit]').click();
    await expectEvent(page, 'calculator_completed', 1);
    const primary = page.locator(nav + ' a').first();
    await primary.scrollIntoViewIfNeeded();
    await page.waitForFunction(() => window.dataLayer.some(a => a[1] === 'related_tool_impression'));
    assert.equal(await primary.getAttribute('href'), '/en/date-add-subtract-calculator');
    await primary.focus();
    await page.keyboard.press('Enter');
    await page.waitForURL(base + '/en/date-add-subtract-calculator');
    assert.equal(await eventCount(page, 'related_calculator_completed'), 0);
    await fillDate(page, 'start', ['2024', '2', '29']);
    await page.locator('#shift-amount').fill('1');
    await page.locator('#global-calculator button[type=submit]').click();
    await expectEvent(page, 'related_calculator_completed', 1);
    await page.locator('#global-calculator button[type=submit]').click();
    await expectEvent(page, 'calculator_completed', 2);
    assert.equal(await eventCount(page, 'related_calculator_completed'), 1);
    await page.locator('#global-calculator button[type=reset]').click();
    assert.equal(await page.locator(nav).isVisible(), false);

    await page.goto(base + '/age');
    await page.locator('[name=birth_date]').fill('19921002');
    await page.locator('#age-form button[type=submit]').click();
    const annual = page.locator(nav + ' [data-tool=annual_age_calculator]');
    await annual.waitFor();
    await expectEvent(page, 'calculator_completed', 1);
    await annual.click();
    await page.waitForURL(/annual-age-calculator\?birth_year=1992/);
    assert.equal(await eventCount(page, 'related_calculator_completed'), 0);
    await page.locator('input[name=birth_year]').fill('1993');
    assert.equal(await page.locator(nav).isVisible(), false);
    await page.locator('form[data-calculator-form] button[type=submit]').click();
    await expectEvent(page, 'related_calculator_completed', 1);
    await page.reload();
    assert.equal(await eventCount(page, 'calculator_completed'), 0);
    const configs = await page.evaluate(() => (window.dataLayer || []).filter(a => a[0] === 'config').map(a => a[2]));
    for (const config of configs) {
        assert.equal(config.page_location, base + '/annual-age-calculator');
        assert.ok(!/[?#]/.test(config.page_referrer || ''));
    }
    await context.close();
}

(async () => {
    const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH });
    try {
        await viewports(browser);
        if (!before) {
            await tableResultOrder(browser);
            await readableCards(browser);
            await funnel(browser);
        }
        console.log('PASS', before ? 'local original' : 'local recommendations and cross-page funnels');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
