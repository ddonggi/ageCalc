(function (root, factory) {
    'use strict';
    if (typeof module === 'object' && module.exports) {
        module.exports = factory();
    } else {
        root.AnniversaryCalendar = factory();
    }
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    'use strict';

    const summaries = Object.freeze({
        hundredth: '100일째',
        'first-anniversary': '첫돌(1주년)',
        thousandth: '1000일째',
        birthday: '다음 생일'
    });

    function leapYear(year) {
        return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
    }

    function monthDays(year, month) {
        return [31, leapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1];
    }

    function parseDate(value) {
        if (typeof value !== 'string' || !/^[0-9]{8}$/.test(value)) {
            throw new TypeError('Expected YYYYMMDD date');
        }
        const year = Number(value.slice(0, 4));
        const month = Number(value.slice(4, 6));
        const day = Number(value.slice(6, 8));
        if (year < 1 || year > 9999 || month < 1 || month > 12 || day < 1 || day > monthDays(year, month)) {
            throw new RangeError('Invalid calendar date');
        }
        return {year, month, day};
    }

    function nextDate(value) {
        let {year, month, day} = parseDate(value);
        if (value === '99991231') {
            throw new RangeError('Exclusive end date is outside supported range');
        }
        day += 1;
        if (day > monthDays(year, month)) {
            day = 1;
            month += 1;
            if (month > 12) {
                month = 1;
                year += 1;
            }
        }
        return String(year).padStart(4, '0') + String(month).padStart(2, '0') + String(day).padStart(2, '0');
    }

    function escapeText(value) {
        return value.replace(/\\/g, '\\\\').replace(/\r\n|\r|\n/g, '\\n').replace(/;/g, '\\;').replace(/,/g, '\\,');
    }

    // Count UTF-8 octets without depending on TextEncoder or splitting code points.
    function foldLine(value) {
        const lines = [];
        let line = '';
        let bytes = 0;
        for (const character of value) {
            const code = character.codePointAt(0);
            const width = code <= 0x7f ? 1 : code <= 0x7ff ? 2 : code <= 0xffff ? 3 : 4;
            if (bytes + width > 75) {
                lines.push(line);
                line = ' ';
                bytes = 1;
            }
            line += character;
            bytes += width;
        }
        lines.push(line);
        return lines.join('\r\n');
    }

    function buildEvent(options) {
        if (!options || !Object.prototype.hasOwnProperty.call(summaries, options.kind)) {
            throw new TypeError('Unsupported anniversary kind');
        }
        const end = nextDate(options.date);
        if (typeof options.uid !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(options.uid)) {
            throw new TypeError('Expected cryptographically generated UUID v4');
        }
        if (typeof options.dtstamp !== 'string' || !/^[0-9]{8}T[0-9]{6}Z$/.test(options.dtstamp)) {
            throw new TypeError('Expected UTC timestamp');
        }
        parseDate(options.dtstamp.slice(0, 8));
        if (Number(options.dtstamp.slice(9, 11)) > 23 || Number(options.dtstamp.slice(11, 13)) > 59 || Number(options.dtstamp.slice(13, 15)) > 59) {
            throw new RangeError('Invalid UTC time');
        }
        return [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//AgeCalc//Anniversary Calendar//KO',
            'BEGIN:VEVENT',
            'UID:' + options.uid,
            'DTSTAMP:' + options.dtstamp,
            'DTSTART;VALUE=DATE:' + options.date,
            'DTEND;VALUE=DATE:' + end,
            'SUMMARY:' + escapeText(summaries[options.kind]),
            'END:VEVENT',
            'END:VCALENDAR'
        ].map(foldLine).join('\r\n') + '\r\n';
    }

    return Object.freeze({buildEvent, escapeText, foldLine});
}));
