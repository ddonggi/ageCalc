(function (root, factory) {
    const api = factory();
    if (typeof module !== 'undefined' && module.exports) module.exports = api;
    else root.WorldTimeCalculations = api;
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';
    const ZONES = Object.freeze(['UTC', 'Asia/Seoul', 'Asia/Tokyo', 'Asia/Shanghai', 'Asia/Kolkata', 'Europe/London', 'America/New_York']);
    // Exact links verified in IANA tzdata2026f backward; never infer equivalence from an offset.
    const UTC_ALIASES = Object.freeze(['UTC', 'Etc/UTC', 'Etc/UCT', 'Etc/Universal', 'Etc/Zulu', 'UCT', 'Universal', 'Zulu']);
    const MINUTE = 60000;
    const DAY = 86400000;
    const pad = value => String(value).padStart(2, '0');
    const error = (field, code) => ({ok: false, field, code});

    function civilDate(year, month, day) {
        const value = new Date(0);
        value.setUTCHours(0, 0, 0, 0);
        value.setUTCFullYear(year, month - 1, day);
        if (value.getUTCFullYear() !== year || value.getUTCMonth() !== month - 1 || value.getUTCDate() !== day) return null;
        return value;
    }

    function cityRow(Format, zone, instant, inputDay) {
        try {
            const formatter = new Format('en-US', {
                timeZone: zone, calendar: 'gregory', numberingSystem: 'latn', hourCycle: 'h23',
                year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
            });
            const resolved = formatter.resolvedOptions();
            const resolvedZone = resolved.timeZone;
            const matchingZone = resolvedZone === zone
                || (zone === 'UTC' && UTC_ALIASES.includes(resolvedZone))
                || (zone === 'Asia/Kolkata' && resolvedZone === 'Asia/Calcutta');
            if (!matchingZone) throw new Error('unsupported time zone');
            if (resolved.calendar !== 'gregory' || resolved.numberingSystem !== 'latn' || resolved.hourCycle !== 'h23') throw new Error('unsupported options');
            const values = {};
            const required = ['year', 'month', 'day', 'hour', 'minute'];
            for (const part of formatter.formatToParts(instant)) {
                if (!required.includes(part.type)) continue;
                if (Object.hasOwn(values, part.type) || typeof part.value !== 'string' || !/^\d+$/.test(part.value)) throw new Error('invalid numeric parts');
                values[part.type] = Number(part.value);
            }
            if (required.some(type => !Object.hasOwn(values, type))) throw new Error('missing numeric parts');
            const {year, month, day, hour, minute} = values;
            if (year < 2019 || year > 2031 || month < 1 || month > 12 || day < 1 || day > 31 || hour < 0 || hour > 23 || minute < 0 || minute > 59) throw new Error('invalid civil time');
            const date = civilDate(year, month, day);
            if (!date) throw new Error('invalid calendar date');
            const offsetMinutes = (date.getTime() + (hour * 60 + minute) * MINUTE - instant.getTime()) / MINUTE;
            const dayDelta = (date.getTime() - inputDay) / DAY;
            if (!Number.isInteger(offsetMinutes) || Math.abs(offsetMinutes) > 14 * 60 || ![-1, 0, 1].includes(dayDelta)) throw new Error('invalid time zone result');
            return {zone, status: 'ok', date: `${year}-${pad(month)}-${pad(day)}`, time: `${pad(hour)}:${pad(minute)}`, offsetMinutes, weekday: date.getUTCDay(), dayDelta};
        } catch (_) {
            return {zone, status: 'unsupported'};
        }
    }

    function calculate(input, dependencies) {
        const source = input && typeof input === 'object' ? input : {};
        if (typeof source.date !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(source.date)) return error('date', 'invalid_date');
        const [year, month, day] = source.date.split('-').map(Number);
        const date = civilDate(year, month, day);
        if (!date || year < 2020 || year > 2030) return error('date', 'invalid_date');
        if (typeof source.time !== 'string' || !/^([01]\d|2[0-3]):[0-5]\d$/.test(source.time)) return error('time', 'invalid_time');
        if (source.sourceOffsetMinutes !== 0 && source.sourceOffsetMinutes !== 540) return error('sourceOffsetMinutes', 'invalid_source');
        const Format = dependencies && Object.hasOwn(dependencies, 'DateTimeFormat')
            ? dependencies.DateTimeFormat : (typeof Intl !== 'undefined' ? Intl.DateTimeFormat : null);
        if (typeof Format !== 'function' || !Format.prototype || typeof Format.prototype.formatToParts !== 'function') return error(null, 'unsupported_intl');
        const [hour, minute] = source.time.split(':').map(Number);
        const instant = new Date(date.getTime() + (hour * 60 + minute - source.sourceOffsetMinutes) * MINUTE);
        const rows = ZONES.map(zone => cityRow(Format, zone, instant, date.getTime()));
        const seoul = rows[1];
        return {
            ok: true, instant: instant.toISOString().replace('.000Z', 'Z'), sourceOffsetMinutes: source.sourceOffsetMinutes, rows,
            seoulMismatch: source.sourceOffsetMinutes === 540 && seoul.status === 'ok' && seoul.offsetMinutes !== 540
        };
    }
    return {calculate};
}));
