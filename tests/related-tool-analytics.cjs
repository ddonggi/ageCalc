// Run against matching server/test settings (RELATED_TOOLS_LAYOUT=cards or baseline). All third-party traffic is intercepted.
// Set GA_TEST_LOADER to a local copy of the site's gtag.js to inspect real GA request serialization.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const http = require('node:http');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const base = process.env.AGECALC_TEST_BASE || 'http://127.0.0.1:8123';
assert.ok(['127.0.0.1', 'localhost'].includes(new URL(base).hostname));
const layout = process.env.RELATED_TOOLS_LAYOUT || 'cards';
const homeSubmit = '#home-age-form button[type="submit"]';
const grade = '#home-grade-link';
const submitGrade = 'form[data-calculator-form] button[type="submit"]';
const names = ['calculator_completed', 'related_tool_impression', 'related_tool_click', 'related_calculator_completed'];

async function fixture(browser, options = {}) {
    const context = await browser.newContext({bypassCSP: Boolean(options.receiver), viewport: {width: 1280, height: 900}});
    if (!options.unset) await context.addCookies([{name: 'cookieConsent', value: 'accepted', url: base}]);
    const events = [];
    let release;
    const delay = new Promise(resolve => { release = resolve; });
    await context.addInitScript(({blocked, recording}) => {
        if (blocked) Object.defineProperty(window, 'sessionStorage', {get() { throw new Error('blocked'); }});
        if (recording) {
            window.gtag = function () {
                (window.dataLayer ||= []).push(arguments);
                if (arguments[0] === 'event') console.debug('funnel-test ' + JSON.stringify([arguments[1], arguments[2]]));
            };
        }
    }, {blocked: options.blocked, recording: !options.realLoader});
    if (options.receiver) {
        // Leave serialization, transport and keepalive behavior to gtag and the browser.
        // Playwright's page request events omit some batches sent after document teardown.
        await context.addInitScript(receiver => {
            const localAddress = address => {
                const target = new URL(address, location.href);
                return target.pathname.endsWith('/collect') ? receiver + target.pathname + target.search : address;
            };
            const fetch = window.fetch.bind(window);
            window.fetch = (address, init) => fetch(localAddress(address), init);
            const beacon = navigator.sendBeacon.bind(navigator);
            navigator.sendBeacon = (address, body) => beacon(localAddress(address), body);
        }, options.receiver);
    }
    await context.route('**/*', async route => {
        const req = route.request();
        const url = new URL(req.url());
        if (url.origin === base || url.origin === options.receiver) return route.continue();
        if (url.hostname === 'www.googletagmanager.com' && url.pathname === '/gtag/js') {
            if (options.delay) await delay;
            return route.fulfill({contentType: 'text/javascript', body: options.realLoader || ''});
        }
        return route.abort();
    });
    context.on('console', msg => {
        if (msg.text().startsWith('funnel-test ')) events.push(JSON.parse(msg.text().slice(12)));
    });
    const page = await context.newPage();
    page.setDefaultTimeout(6500);
    return {context, page, events, release};
}

async function home(page, path = '/') {
    await page.goto(base + path, {waitUntil: 'domcontentloaded'});
    await page.locator('#home-birth-input').fill('20120314');
    await page.locator(homeSubmit).click();
}
async function navigate(page, link) {
    await Promise.all([page.waitForNavigation({waitUntil: 'domcontentloaded'}), link.click()]);
}
async function waitCount(events, name, count) {
    for (let i = 0; i < 100 && events.filter(([event]) => event === name).length < count; i++) {
        await new Promise(resolve => setTimeout(resolve, 30));
    }
    assert.equal(events.filter(([event]) => event === name).length, count, name);
}
function checkDimensions(events) {
    const allowed = ['source_tool', 'destination_tool', 'locale', 'placement_version', 'measurable', 'card_rank'];
    for (const [name, params] of events) {
        assert.ok(names.includes(name));
        assert.ok(Object.keys(params).every(key => allowed.includes(key)));
        assert.ok(!JSON.stringify(params).includes('2012'));
    }
}

async function yearHandoff(browser, delayed, blocked = false) {
    const {page, context, events, release} = await fixture(browser, {delay: delayed, blocked});
    try {
        await home(page);
        await navigate(page, page.locator(grade));
        release();
        await page.waitForFunction(() => window.dataLayer.some(command => command[0] === 'config'));
        assert.match(page.url(), /year=2012/);
        const expectedSource = delayed && blocked ? 0 : 1;
        await waitCount(events, 'calculator_completed', expectedSource);
        assert.equal(events.filter(([name]) => name === 'related_calculator_completed').length, 0);
        await page.locator('select[name="year"]').selectOption('2011');
        await navigate(page, page.locator(submitGrade));
        await waitCount(events, 'related_calculator_completed', blocked ? 0 : 1);
        if (blocked) assert.equal(events.find(([n]) => n === 'related_tool_click')[1].measurable, false);
        if (!blocked) {
            const toSchool = events.filter(([,p]) => p.destination_tool === 'school_grade_calculator');
            assert.deepEqual(toSchool.map(([name]) => name), names.slice(1));
            assert.ok(toSchool.every(([,p]) => p.card_rank === 1 && p.placement_version === layout));
            assert.equal(events.filter(([n]) => n === 'calculator_completed').length, 2);
        }
        checkDimensions(events);
        const count = events.filter(([n]) => n === 'calculator_completed').length;
        await page.reload();
        await page.goBack();
        await page.goto(base + '/school-grade-calculator?year=2010');
        assert.equal(events.filter(([n]) => n === 'calculator_completed').length, count);
    } finally { release(); await context.close(); }
}

async function annualAgeResubmission(browser) {
    const {page, context, events} = await fixture(browser);
    try {
        await page.goto(base + '/age');
        await page.locator('[name=birth_date]').fill('19921002');
        await navigate(page, page.locator('#age-form button[type=submit]'));
        await navigate(page, page.locator('[data-related-tools] a[data-tool=annual_age_calculator]'));
        assert.equal(events.filter(([name]) => name === 'related_calculator_completed').length, 0);
        const input = page.locator('input[name=birth_year]');
        const panel = page.locator('[data-related-tools]');
        assert.equal(await input.inputValue(), '1992');
        const documents = [];
        page.on('request', request => { if (request.isNavigationRequest()) documents.push(request.url()); });
        const originalUrl = page.url();
        const originalWindow = await browserWindowId(page);
        for (const modifier of ['ControlOrMeta', 'Shift']) {
            const [opened] = await Promise.all([
                context.waitForEvent('page', {timeout: 6500}),
                page.locator(submitGrade).click({modifiers: [modifier]}),
            ]);
            await opened.waitForURL(originalUrl + '#annual-age-result');
            assert.ok(await opened.locator('#annual-age-result').isVisible());
            assert.equal(await browserWindowId(opened) === originalWindow, modifier === 'ControlOrMeta',
                modifier + ' must use the native tab or window');
            assert.equal(page.url(), originalUrl);
            assert.equal(documents.length, 0);
            assert.equal(events.filter(([name]) => name === 'related_calculator_completed').length, 0);
            await opened.close();
            await page.bringToFront();
        }
        await page.locator(submitGrade).click();
        await waitCount(events, 'related_calculator_completed', 1);
        await waitCount(events, 'calculator_completed', 2);
        assert.equal(context.pages().length, 1);
        await input.fill('1993');
        await input.fill('1992');
        assert.equal(await panel.isVisible(), false);
        await page.locator(submitGrade).click();
        await waitCount(events, 'calculator_completed', 3);
        assert.ok(await panel.isVisible());
        assert.equal(documents.length, 0);
        await input.fill('1993');
        await navigate(page, page.locator(submitGrade));
        await waitCount(events, 'calculator_completed', 4);
        assert.equal(documents.length, 1);
        await page.reload();
        assert.equal(events.filter(([name]) => name === 'calculator_completed').length, 4);
        assert.equal(events.filter(([name]) => name === 'related_calculator_completed').length, 1);
    } finally { await context.close(); }
}

async function browserWindowId(page) {
    const session = await page.context().newCDPSession(page);
    try {
        const {windowId} = await session.send('Browser.getWindowForTarget');
        return windowId;
    } finally { await session.detach(); }
}

async function familyDestinationRank(browser) {
    const {page, context, events} = await fixture(browser);
    try {
        await page.setViewportSize({width: 390, height: 844});
        await page.goto(base + '/parent-child?parent_role=mother&parent_birth=19800213&child_role=son&child_birth=20150831&child_role=daughter&child_birth=20191216');
        await page.locator('#child-lines input').first().fill('20140831');
        await navigate(page, page.locator(submitGrade));
        const links = page.locator('[data-baseline-tools] a[data-tool=school_grade_calculator]');
        assert.equal(await links.count(), 2);
        await links.first().evaluate(el => el.scrollIntoView({block: 'center', behavior: 'instant'}));
        await waitCount(events, 'related_tool_impression', 1);
        await navigate(page, links.nth(1));
        await waitCount(events, 'related_tool_click', 1);
        const school = events.filter(([, p]) => p.destination_tool === 'school_grade_calculator');
        assert.deepEqual(school.map(([name, p]) => [name, p.card_rank]),
            [['related_tool_impression', 1], ['related_tool_click', 1]]);
        assert.match(page.url(), /year=2019/);
    } finally { await context.close(); }
}

async function consentAndExposure(browser) {
    const {page, context, events} = await fixture(browser, {unset: true});
    try {
        await home(page);
        await page.locator('#accept-cookies').click();
        await page.waitForFunction(() => window.dataLayer.some(command => command[0] === 'config'));
        await page.locator(grade).scrollIntoViewIfNeeded();
        await page.waitForTimeout(1100);
        assert.equal(events.length, 0);
        await page.setViewportSize({width: 1100, height: 360});
        await page.locator(homeSubmit).click();
        const showFraction = fraction => page.locator(grade).evaluate((link, amount) => {
            const rect = link.getBoundingClientRect();
            window.scrollBy({top: rect.top - innerHeight + rect.height * amount, behavior: 'instant'});
        }, fraction);
        await showFraction(0.4);
        await page.waitForTimeout(1100);
        assert.equal(events.filter(([n]) => n === 'related_tool_impression').length, 0);
        await showFraction(0.7);
        await page.waitForTimeout(600);
        await showFraction(0.3);
        await page.waitForTimeout(100);
        await showFraction(0.7);
        await page.waitForTimeout(600);
        assert.equal(events.filter(([n]) => n === 'related_tool_impression').length, 0);
        await waitCount(events, 'related_tool_impression', 2);
        await page.locator(grade).scrollIntoViewIfNeeded();
        await page.waitForTimeout(1100);
        assert.equal(events.filter(([n]) => n === 'related_tool_impression').length, 2);
        await page.evaluate(() => { document.cookie = 'cookieConsent=rejected;path=/'; });
        await navigate(page, page.locator(grade));
        await navigate(page, page.locator(submitGrade));
        assert.equal(events.filter(([n]) => n === 'related_tool_click').length, 0);
        assert.equal(events.filter(([n]) => n === 'related_calculator_completed').length, 0);
    } finally { await context.close(); }
}

async function unlinked(browser, reason) {
    const {page, context, events} = await fixture(browser);
    try {
        await home(page);
        let destination = page;
        if (reason === 'new-tab') {
            await page.locator(grade).evaluate(link => { link.target = '_blank'; link.rel = 'opener'; });
            [destination] = await Promise.all([context.waitForEvent('page'), page.locator(grade).click()]);
            await destination.waitForLoadState('domcontentloaded');
        } else {
            await navigate(page, page.locator(grade));
            if (reason === 'expired') {
                const future = Date.now() + 31 * 60 * 1000;
                const advance = timestamp => { Date.now = () => timestamp; };
                await page.context().addInitScript(advance, future);
                await page.evaluate(advance, future);
            } else {
                await page.goto(base + '/about');
                await page.goto(base + '/school-grade-calculator?year=2012');
            }
        }
        await navigate(destination, destination.locator(submitGrade));
        await waitCount(events, 'calculator_completed', 2);
        assert.equal(events.filter(([n]) => n === 'related_calculator_completed').length, 0, reason);
        assert.equal(events.find(([n]) => n === 'related_tool_click')[1].measurable, reason !== 'new-tab');
    } finally { await context.close(); }
}

async function dateHandoff(browser, locale) {
    const {page, context, events} = await fixture(browser);
    async function date(prefix, day) {
        await page.locator('#' + prefix + '-year').fill('2026');
        await page.locator('#' + prefix + '-month').selectOption('8');
        await page.locator('#' + prefix + '-day').fill(day);
    }
    const submit = '#global-calculator button[type="submit"]';
    try {
        await page.goto(base + '/' + locale + '/days-between-dates');
        await date('start', '1');
        await date('end', '4');
        await page.locator(submit).click();
        await navigate(page, page.locator('[data-related-tools] a[data-tool="date_add_subtract"]'));
        await page.locator(submit).click(); // Missing amount is invalid.
        await date('start', '4');
        await page.locator('#shift-amount').fill('2');
        await page.locator(submit).click();
        await page.locator(submit).click();
        await waitCount(events, 'calculator_completed', 3);
        await waitCount(events, 'related_calculator_completed', 1);
        assert.ok(events.every(([,p]) => p.locale.toLowerCase() === locale));
        checkDimensions(events);
    } finally { await context.close(); }
}

async function regionalPost(browser) {
    const {page, context, events} = await fixture(browser);
    try {
        await page.goto(base + '/ja/business-days-calculator');
        await page.locator('[name="start"]').fill('2026-09-15');
        await page.locator('[name="end"]').fill('2026-09-01');
        await navigate(page, page.locator(submitGrade));
        assert.equal(await page.locator('[data-related-tools]').getAttribute('data-ssr-success'), 'false');
        assert.equal(events.length, 0);
        await page.locator('[name="end"]').fill('2026-09-16');
        await navigate(page, page.locator(submitGrade));
        await waitCount(events, 'calculator_completed', 1);
        await page.reload();
        assert.equal(events.filter(([n]) => n === 'calculator_completed').length, 1);
    } finally { await context.close(); }
}

async function realRequests(browser) {
    const hits = [];
    const server = http.createServer((request, response) => {
        const chunks = [];
        request.on('data', chunk => chunks.push(chunk));
        request.on('end', () => {
            hits.push([receiver + request.url, Buffer.concat(chunks).toString(), request.headers.referer || ''].join('\n'));
            response.writeHead(204, {'Access-Control-Allow-Origin': '*'}).end();
        });
    });
    await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
    const receiver = 'http://127.0.0.1:' + server.address().port;
    const {page, context} = await fixture(browser, {receiver, realLoader: fs.readFileSync(process.env.GA_TEST_LOADER, 'utf8')});
    try {
        const secret = 'private-test-name';
        await page.goto(base + '/age?birth_date=19921002&label=' + secret + '#private-hash', {referer: base + '/parent-child?s=' + secret});
        await page.waitForFunction(() => window.dataLayer.some(command => command[0] === 'config'));
        const deadline = Date.now() + 10000;
        while (!hits.some(hit => hit.includes('en=page_view')) && Date.now() < deadline) await page.waitForTimeout(100);
        assert.ok(hits.some(hit => hit.includes('en=page_view')), 'no real GA page_view was intercepted');
        assert.ok(hits.every(hit => !/private-test-name|19921002|private-hash|birth_date/.test(decodeURIComponent(hit))));
        const hit = new URL(hits.find(item => item.includes('en=page_view')).split('\n')[0]);
        assert.equal(hit.searchParams.get('dl'), base + '/age');
        assert.equal(hit.searchParams.get('dr'), base + '/parent-child');

        await home(page, '/?label=' + secret + '#private-hash');
        await navigate(page, page.locator(grade));
        await navigate(page, page.locator(submitGrade));
        const limit = Date.now() + 15000;
        const sent = name => hits.some(hit => hit.includes('en=' + name));
        while (!names.every(sent) && Date.now() < limit) await page.waitForTimeout(200);
        assert.ok(names.every(sent), 'missing wire events: ' + names.filter(name => !sent(name)));
        assert.ok(hits.every(hit => !/private-test-name|19921002|private-hash|20120314|[?&]year=2012/.test(decodeURIComponent(hit))));
    } finally { await context.close(); server.close(); }
}

(async () => {
    const browser = await chromium.launch({
        // Native modifier-click dispositions need full Chromium, including in headless mode.
        channel: 'chromium',
        executablePath: process.env.CHROMIUM_EXECUTABLE,
        args: ['--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE 127.0.0.1, EXCLUDE localhost', '--no-proxy-server'],
    });
    try {
        if (layout === 'baseline') {
            await familyDestinationRank(browser);
            console.log('PASS baseline shared destination rank for two children');
            await yearHandoff(browser, false);
            console.log('PASS baseline links and downstream user submission');
            return;
        }
        for (const [label, check] of [
            ['native tab/window and same-tab annual age submissions', () => annualAgeResubmission(browser)],
            ['GET handoff', () => yearHandoff(browser, false)],
            ['delayed loader', () => yearHandoff(browser, true)],
            ['blocked storage', () => yearHandoff(browser, false, true)],
            ['invalid/valid regional POST', () => regionalPost(browser)],
            ['consent and impressions', () => consentAndExposure(browser)],
            ...['new-tab', 'expired', 'detour'].map(label => [label, () => unlinked(browser, label)]),
            ...['en', 'pt-br', 'zh-cn'].map(label => [label, () => dateHandoff(browser, label)]),
        ]) {
            await check();
            console.log('PASS', label);
        }
        if (process.env.GA_TEST_LOADER) { await realRequests(browser); console.log('PASS intercepted gtag collection'); }
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
