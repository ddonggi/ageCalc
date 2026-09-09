/* Calendar values only. No locale, DOM, storage, network or translated strings. */
(function (root, factory) {
    if (typeof module === 'object' && module.exports) {
        module.exports = factory(require('./date-rules.js'));
    } else {
        root.AgeCalcGlobalRules = factory(root.AgeCalcDateRules);
    }
}(typeof globalThis !== 'undefined' ? globalThis : this, function (rules) {
    'use strict';
    const DAY = 86400000;

    function date(value) {
        try {
            const parsed = rules.parseIsoDate(value);
            if (parsed.getUTCFullYear() < 1) throw new Error();
            return parsed;
        } catch (_) {
            throw new Error('invalid_date');
        }
    }

    function iso(value) {
        const year = value.getUTCFullYear();
        if (year < 1 || year > 9999) throw new Error('date_range');
        return `${String(year).padStart(4, '0')}-${String(value.getUTCMonth() + 1).padStart(2, '0')}-${String(value.getUTCDate()).padStart(2, '0')}`;
    }

    function utc(year, month, day) {
        const value = new Date(0);
        value.setUTCHours(0, 0, 0, 0);
        value.setUTCFullYear(year, month, day);
        return value;
    }

    function isoParts(year, month, day) {
        if (!/^\d{4}$/.test(String(year)) || !/^\d{1,2}$/.test(String(month)) || !/^\d{1,2}$/.test(String(day))) {
            throw new Error('invalid_date');
        }
        const value = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
        return iso(date(value));
    }

    function today() {
        const now = new Date();
        return iso(utc(now.getFullYear(), now.getMonth(), now.getDate()));
    }

    function daysBetween(start, end) {
        return (date(end) - date(start)) / DAY;
    }

    function monthlyAnchor(birth, months) {
        const first = utc(birth.getUTCFullYear(), birth.getUTCMonth() + months, 1);
        const lastDay = utc(first.getUTCFullYear(), first.getUTCMonth() + 1, 0).getUTCDate();
        return utc(first.getUTCFullYear(), first.getUTCMonth(), Math.min(birth.getUTCDate(), lastDay));
    }

    function completedMonths(birth, reference) {
        const b = date(birth);
        const r = date(reference);
        if (b > r) throw new Error('reference_before_birth');
        // The legacy helper uses Date.UTC (which maps years 0–99 to 1900–1999).
        // Translate very early dates by a full Gregorian cycle without changing it.
        if (r.getUTCFullYear() <= 100) {
            return rules.calculateCompletedMonths(
                iso(utc(b.getUTCFullYear() + 400, b.getUTCMonth(), b.getUTCDate())),
                iso(utc(r.getUTCFullYear() + 400, r.getUTCMonth(), r.getUTCDate())));
        }
        return rules.calculateCompletedMonths(birth, reference);
    }

    function duration(birth, reference) {
        const b = date(birth);
        const r = date(reference);
        if (b > r) throw new Error('reference_before_birth');
        const years = rules.calculateManAge(birth, reference);
        for (let months = 11; months >= 0; months -= 1) {
            // Whole years retain the existing March 1 leap-birthday convention.
            const anchor = months === 0
                ? utc(b.getUTCFullYear() + years, b.getUTCMonth(), b.getUTCDate())
                : monthlyAnchor(b, years * 12 + months);
            if (anchor <= r) return {years, months, days: (r - anchor) / DAY};
        }
        throw new Error('invalid_date');
    }

    function birthday(month, day, reference) {
        date(isoParts('2000', String(month), String(day)));
        const r = date(reference);
        for (let year = r.getUTCFullYear(); year <= 9999; year += 1) {
            const candidate = utc(year, Number(month) - 1, Number(day));
            if (candidate.getUTCMonth() + 1 === Number(month) && candidate.getUTCDate() === Number(day) && candidate >= r) {
                return {nextDate: iso(candidate), days: (candidate - r) / DAY};
            }
        }
        throw new Error('date_range');
    }

    function age(birth, reference) {
        const b = date(birth);
        const elapsed = duration(birth, reference);
        let next;
        try {
            next = birthday(b.getUTCMonth() + 1, b.getUTCDate(), reference);
        } catch (error) {
            if (error.message !== 'date_range') throw error;
            next = null;
        }
        return {...elapsed, totalMonths: completedMonths(birth, reference), totalDays: daysBetween(birth, reference), next};
    }

    function baby(birth, reference) {
        const months = completedMonths(birth, reference);
        return {months, years: Math.floor(months / 12), remainingMonths: months % 12, days: daysBetween(birth, reference)};
    }

    function hundred(start, reference) {
        const milestone = iso(rules.addUtcDays(date(start), 99));
        return {date: milestone, days: daysBetween(reference, milestone)};
    }

    function yearGap(first, second, reference) {
        const year = date(reference).getUTCFullYear();
        const minimum = Math.max(1900, year - 100);
        const values = [first, second].map(value => {
            if (!/^\d{4}$/.test(String(value)) || Number(value) < minimum || Number(value) > year) throw new Error('invalid_year');
            return Number(value);
        });
        return Math.abs(values[0] - values[1]);
    }

    return {isoParts, today, daysBetween, completedMonths, duration, birthday, age, baby, hundred, yearGap};
}));
