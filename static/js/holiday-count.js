/* Optional public facts only. Date inputs stay in the calling document. */
(function (root, factory) {
    const api = factory();
    if (typeof module === 'object' && module.exports) module.exports = api;
    else root.AgeCalcHolidayCount = api;
}(typeof window === 'object' ? window : globalThis, function () {
    'use strict';
    const MAX_LEASE = 600000;
    const DAY = 86400000;
    const date = value => typeof value === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(`${value}T00:00:00Z`)) && new Date(`${value}T00:00:00Z`).toISOString().slice(0,10) === value;
    function validate(data) {
        const aware = value => {
            if (typeof value !== 'string') return false;
            const parts = value.match(/^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,6})?(Z|[+-]\d{2}:\d{2})$/);
            return Boolean(parts && date(parts[1]) && Number(parts[2])<24 && Number(parts[3])<60 && Number(parts[4])<60 &&
                (parts[5]==='Z' || (Number(parts[5].slice(1,3))<24 && Number(parts[5].slice(4))<60)) && Number.isFinite(Date.parse(value)));
        };
        if (!data || data.available !== true || data.state !== 'current' || data.year !== 2027 ||
            !Array.isArray(data.holidays) || data.holidays.length !== 24 ||
            !Number.isFinite(data.lease_ms) || data.lease_ms <= 0 || data.lease_ms > MAX_LEASE ||
            !aware(data.server_now) || !aware(data.expires_at)) throw new Error('unavailable');
        const meta = data.metadata;
        if (!meta || !['version','source_url','verified_on','next_review'].every(key => typeof meta[key] === 'string' && meta[key].length > 0)) throw new Error('unavailable');
        const source = new URL(meta.source_url);
        if (source.protocol !== 'https:' || !['www.kasa.go.kr','kasa.go.kr','gwanbo.go.kr','www.gwanbo.go.kr'].includes(source.hostname) || source.username || source.password) throw new Error('unavailable');
        if (!date(meta.verified_on) || !date(meta.next_review) || meta.verified_on > meta.next_review || Date.parse(`${meta.next_review}T00:00:00Z`)-Date.parse(`${meta.verified_on}T00:00:00Z`) !== 7*DAY) throw new Error('unavailable');
        const seen = new Set();
        for (const item of data.holidays) {
            if (!item || !date(item.date) || !item.date.startsWith('2027-') || seen.has(item.date) ||
                typeof item.label !== 'string' || !item.label.trim() || item.label.length > 200 ||
                !['national','substitute'].includes(item.type)) throw new Error('unavailable');
            seen.add(item.date);
        }
        const server = Date.parse(data.server_now), expires = Date.parse(data.expires_at);
        const kstDay = new Date(server + 9*3600000).toISOString().slice(0,10);
        const midnight = Math.floor((server+9*3600000)/DAY)*DAY+DAY-9*3600000;
        const reviewDeadline = Date.parse(`${meta.next_review}T00:00:00+09:00`)+DAY;
        const limit = Math.min(MAX_LEASE,midnight-server,reviewDeadline-server);
        if (meta.verified_on > kstDay || meta.next_review < kstDay || expires <= server || expires > Math.min(midnight,reviewDeadline) || data.lease_ms > limit || expires-server < data.lease_ms) throw new Error('unavailable');
        return data;
    }
    function create(env) {
        let generation = 0, abort, timeout, expiry, clockCheck;
        function clear(state = 'idle') {
            generation += 1;
            if (abort) abort.abort();
            env.clearTimeout(timeout); env.clearTimeout(expiry); env.clearInterval(clockCheck);
            abort = timeout = expiry = clockCheck = undefined;
            env.render({state});
        }
        function submit(selected,start,end,inclusive) {
            clear();
            if (!selected) return;
            if (!date(start) || !date(end) || end < start) {env.render({state:'unavailable'}); return;}
            if (!/^2027-\d{2}-\d{2}$/.test(start) || !/^2027-\d{2}-\d{2}$/.test(end)) {env.render({state:'unsupported'}); return;}
            if (!env.online()) {env.render({state:'unavailable'}); return;}
            const mine = generation, began = env.now(), wallBegan = env.wall();
            abort = new AbortController();
            env.render({state:'loading'});
            timeout = env.setTimeout(() => {if(mine === generation) clear('unavailable');},10000);
            env.fetch('/api/calendar/korea/2027',{method:'GET',credentials:'omit',referrerPolicy:'no-referrer',cache:'no-store',signal:abort.signal})
                .then(response => {if(!response.ok) throw new Error('unavailable'); return response.json();})
                .then(raw => {
                    if (mine !== generation) return;
                    const data = validate(raw), elapsed = env.now()-began, wallElapsed = env.wall()-wallBegan;
                    const remaining = data.lease_ms-elapsed;
                    if (!Number.isFinite(elapsed) || elapsed < 0 || remaining <= 0 || wallElapsed < 0 || Math.abs(wallElapsed-elapsed)>2000) throw new Error('unavailable');
                    const answer = env.calculate(start,end,inclusive,data.holidays);
                    env.clearTimeout(timeout);
                    env.render({state:'ready',answer,metadata:data.metadata});
                    expiry = env.setTimeout(() => {if(mine === generation) clear('expired');},remaining);
                    clockCheck = env.setInterval(() => {
                        if(mine !== generation) return;
                        const monotonic = env.now()-began, wall = env.wall()-wallBegan;
                        if(monotonic < 0 || wall < 0 || Math.abs(wall-monotonic)>2000 || monotonic >= data.lease_ms) clear('expired');
                    },1000);
                }).catch(() => {if(mine === generation) clear('unavailable');});
        }
        return {submit,invalidate:clear};
    }
    return {create,validate};
}));
