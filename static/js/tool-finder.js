/* Search stays in this document: no URL, storage, requests or analytics hooks. */
(function (root) {
  'use strict';
  const normalize = value => String(value ?? '').normalize('NFKC').toLowerCase().trim().replace(/\s+/gu, ' ');
  const contains = (field, token) => field.includes(token) || field.replace(/\s/gu, '').includes(token.replace(/\s/gu, ''));
  function search(items, raw, group = 'all') {
    const query = normalize(String(raw ?? '').slice(0, 80));
    const tokens = query ? query.split(' ') : [];
    return items.filter(item => group === 'all' || item.group === group).map(item => {
      const title = normalize(item.title);
      const aliases = (item.aliases || []).map(normalize);
      const fields = [title, ...aliases];
      if (!tokens.every(token => fields.some(field => contains(field, token)))) return null;
      const rank = !query ? 0 : title === query ? 0 : aliases.includes(query) ? 1 : tokens.every(token => contains(title, token)) ? 2 : 3;
      return {item, rank};
    }).filter(Boolean).sort((a, b) => a.rank - b.rank || a.item.order - b.item.order || (a.item.endpoint < b.item.endpoint ? -1 : a.item.endpoint > b.item.endpoint ? 1 : 0)).map(result => result.item);
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {normalize, search};
  if (!root.document) return;
  const section = root.document.getElementById('tool-finder');
  if (!section) return;
  const data = root.document.getElementById('tool-finder-data');
  const input = section.querySelector('input');
  const controls = section.querySelector('[data-tool-controls]');
  const buttons = Array.from(section.querySelectorAll('[data-tool-group]'));
  const rows = Array.from(section.querySelectorAll('[data-tool-endpoint]'));
  const status = section.querySelector('[data-tool-count]');
  const empty = section.querySelector('[data-tool-empty]');
  const items = JSON.parse(data.textContent);
  let group = 'all';
  let composing = false;
  let completedCompositionValue = null;
  let timer;
  function update() {
    root.clearTimeout(timer);
    const results = search(items, input.value, group);
    const visible = new Set(results.map(item => item.endpoint));
    for (const row of rows) row.hidden = !visible.has(row.dataset.toolEndpoint);
    const list = section.querySelector('ul');
    for (const item of results) list.appendChild(rows.find(row => row.dataset.toolEndpoint === item.endpoint));
    status.textContent = `도구 ${results.length}개`;
    empty.hidden = results.length !== 0;
    for (const button of buttons) button.setAttribute('aria-pressed', String(button.dataset.toolGroup === group));
  }
  function reset(focus) {
    root.clearTimeout(timer);
    composing = false;
    completedCompositionValue = null;
    input.value = '';
    group = 'all';
    update();
    if (focus) input.focus();
  }
  input.addEventListener('compositionstart', () => { composing = true; completedCompositionValue = null; root.clearTimeout(timer); });
  input.addEventListener('compositionend', () => { composing = false; completedCompositionValue = input.value; update(); });
  input.addEventListener('input', event => {
    if (composing || event.isComposing) return;
    if (completedCompositionValue !== null && input.value === completedCompositionValue) {
      completedCompositionValue = null;
      return;
    }
    completedCompositionValue = null;
    root.clearTimeout(timer);
    timer = root.setTimeout(update, 150);
  });
  input.addEventListener('keydown', event => {
    if (event.key !== 'Enter' || composing || event.isComposing || event.keyCode === 229) return;
    event.preventDefault();
    update();
  });
  for (const button of buttons) button.addEventListener('click', () => {
    group = button.dataset.toolGroup;
    if (!composing) update();
  });
  for (const button of section.querySelectorAll('[data-tool-reset]')) button.addEventListener('click', () => reset(true));
  // Native focus scrolling ignores fixed overlays. Keep this section's focused
  // control clear without changing the shared header or consent banner.
  section.addEventListener('focusin', event => {
    const target = event.target;
    root.requestAnimationFrame(() => {
      if (root.document.activeElement !== target) return;
      const rect = target.getBoundingClientRect();
      let top = 8;
      let bottom = root.innerHeight - 8;
      for (const selector of ['.site-header', '#cookie-banner']) {
        const overlay = root.document.querySelector(selector);
        if (!overlay) continue;
        const bounds = overlay.getBoundingClientRect();
        const style = root.getComputedStyle(overlay);
        if (!['fixed', 'sticky'].includes(style.position) || style.visibility === 'hidden' ||
            bounds.width === 0 || bounds.height === 0 || bounds.right <= rect.left || bounds.left >= rect.right) continue;
        if (selector === '.site-header' && bounds.top <= 0) top = Math.max(top, bounds.bottom + 8);
        if (selector === '#cookie-banner' && bounds.top < root.innerHeight) bottom = Math.min(bottom, bounds.top - 8);
      }
      const delta = rect.top < top ? rect.top - top : rect.bottom > bottom ? Math.min(rect.bottom - bottom, rect.top - top) : 0;
      if (delta) root.scrollBy({top: delta, behavior: 'instant'});
    });
  });
  root.addEventListener('pagehide', () => reset(false));
  root.addEventListener('pageshow', () => reset(false));
  reset(false);
  controls.hidden = false;
})(typeof window === 'undefined' ? globalThis : window);
