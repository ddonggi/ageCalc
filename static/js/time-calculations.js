(function (root, factory) {
    'use strict';
    if (typeof module === 'object' && module.exports) module.exports = factory();
    else root.TimeCalculations = factory();
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';
    function failure(field, code) { return { ok: false, field: field, code: code }; }
    function timeMinutes(value) {
        if (typeof value !== 'string' || !/^(?:[01]\d|2[0-3]):[0-5]\d$/.test(value)) return null;
        return Number(value.slice(0, 2)) * 60 + Number(value.slice(3));
    }
    function calculateDuration(input) {
        input = input || {};
        var start = timeMinutes(input.start);
        var end = timeMinutes(input.end);
        if (start === null) return failure('start', 'invalid_time');
        if (end === null) return failure('end', 'invalid_time');
        if (typeof input.nextDay !== 'boolean') return failure('nextDay', 'invalid_day');
        if (typeof input.breakMinutes !== 'string' || !/^\d+$/.test(input.breakMinutes)) return failure('breakMinutes', 'invalid_break');
        var rest = Number(input.breakMinutes);
        if (!Number.isSafeInteger(rest) || rest > 1440) return failure('breakMinutes', 'invalid_break');
        var gross = end - start + (input.nextDay ? 1440 : 0);
        if (gross < 0) return failure('end', 'end_before_start');
        if (gross > 1440) return failure('end', 'duration_too_long');
        if (rest > gross) return failure('breakMinutes', 'break_exceeds_duration');
        var net = gross - rest;
        return { ok: true, grossMinutes: gross, breakMinutes: rest, netMinutes: net, decimalHours: (net / 60).toFixed(2) };
    }
    return Object.freeze({ calculateDuration: calculateDuration });
}));
