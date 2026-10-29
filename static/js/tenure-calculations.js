/* Calendar reference only. No legal entitlement, DOM, storage or network. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory(require('./global-calculations.js'));
    } else {
        root.AgeCalcTenureRules = factory(root.AgeCalcGlobalRules);
    }
}(typeof globalThis !== 'undefined' ? globalThis : this, function (rules) {
    'use strict';

    function parts(value) {
        if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
            throw new Error('invalid_date');
        }
        const [year, month, day] = value.split('-').map(Number);
        // Reuse the shared strict validator, including the 0001 lower bound.
        rules.isoParts(value.slice(0, 4), String(month), String(day));
        return {year, month, day};
    }

    function anniversary(start, year) {
        // UTC construction deliberately rolls February 29 to March 1 in a
        // common year. setUTCFullYear avoids Date.UTC's 00..99-year offset.
        const date = new Date(0);
        date.setUTCHours(0, 0, 0, 0);
        date.setUTCFullYear(year, start.month - 1, start.day);
        return `${String(year).padStart(4, '0')}-${String(date.getUTCMonth() + 1).padStart(2, '0')}-${String(date.getUTCDate()).padStart(2, '0')}`;
    }

    function calculate(startISO, endISO) {
        const start = parts(startISO);
        const end = parts(endISO);
        if (endISO < startISO) throw new Error('end_before_start');
        const period = rules.duration(startISO, endISO);
        const elapsedDays = rules.daysBetween(startISO, endISO);
        let year = Math.max(start.year + 1, end.year);
        let nextAnniversary = null;
        if (year <= 9999) {
            let candidate = anniversary(start, year);
            if (candidate < endISO) {
                year += 1;
                if (year <= 9999) candidate = anniversary(start, year);
            }
            if (year <= 9999) {
                nextAnniversary = {
                    date: candidate,
                    years: year - start.year,
                    days: rules.daysBetween(endISO, candidate)
                };
            }
        }
        return {years: period.years, months: period.months, days: period.days, elapsedDays, nextAnniversary};
    }

    return {calculate};
}));
