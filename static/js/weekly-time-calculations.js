(function (root, factory) {
    'use strict';
    if (typeof module === 'object' && module.exports) module.exports = factory(require('./time-calculations.js'));
    else root.WeeklyTimeCalculations = factory(root.TimeCalculations);
}(typeof globalThis !== 'undefined' ? globalThis : this, function (daily) {
    'use strict';
    var fields = ['start', 'end', 'nextDay', 'breakMinutes'];
    function error(row, field, code, relatedRow) {
        var item = { row: row, field: field, code: code };
        if (relatedRow !== undefined) item.relatedRow = relatedRow;
        return item;
    }
    function minuteOfDay(time) { return Number(time.slice(0, 2)) * 60 + Number(time.slice(3)); }
    function calculateWeek(rows) {
        if (!Array.isArray(rows) || rows.length !== 7) return { ok: false, errors: [error(null, 'rows', 'invalid_week')] };
        var errors = [], days = [], intervals = [];
        var gross = 0, rest = 0, net = 0, active = 0, crosses = false;
        for (var index = 0; index < 7; index += 1) {
            var row = rows[index];
            if (!row || typeof row !== 'object' || Array.isArray(row) ||
                Reflect.ownKeys(row).length !== 4 || fields.some(function (field) { return !Object.prototype.hasOwnProperty.call(row, field); })) {
                errors.push(error(index, 'rows', 'invalid_week'));
                continue;
            }
            if (row.start === '' && row.end === '' && row.nextDay === false && row.breakMinutes === '0') {
                days.push({ index: index, status: 'empty' });
                continue;
            }
            var result = daily.calculateDuration(row);
            if (!result.ok) { errors.push(error(index, result.field, result.code)); continue; }
            active += 1;
            days.push({ index: index, status: 'valid', start: row.start, end: row.end, nextDay: row.nextDay,
                grossMinutes: result.grossMinutes, breakMinutes: result.breakMinutes,
                netMinutes: result.netMinutes, decimalHours: result.decimalHours });
            gross += result.grossMinutes;
            rest += result.breakMinutes;
            net += result.netMinutes;
            var start = index * 1440 + minuteOfDay(row.start);
            var end = start + result.grossMinutes;
            if (end > 10080) crosses = true;
            if (result.grossMinutes > 0) intervals.push({ row: index, start: start, end: end });
        }
        for (var first = 0; first < intervals.length; first += 1) {
            for (var second = first + 1; second < intervals.length; second += 1) {
                var a = intervals[first], b = intervals[second];
                if (a.start < b.end && b.start < a.end) {
                    errors.push(error(a.row, 'rows', 'overlap', b.row));
                    errors.push(error(b.row, 'rows', 'overlap', a.row));
                }
            }
        }
        if (errors.length) {
            errors.sort(function (a, b) { return a.row - b.row || fields.indexOf(a.field) - fields.indexOf(b.field) || (a.relatedRow || 0) - (b.relatedRow || 0); });
            return { ok: false, errors: errors };
        }
        if (!active) return { ok: false, errors: [error(null, 'rows', 'empty_week')] };
        return { ok: true, days: days, totals: { grossMinutes: gross, breakMinutes: rest, netMinutes: net, decimalHours: (net / 60).toFixed(2) }, crossesWeekBoundary: crosses };
    }
    var csvLabels = {"columns": ["요일", "상태", "시작", "종료", "종료일", "전체분", "휴게분", "순분", "순소수시간"], "days": ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"], "empty": "미입력(합계 제외)", "valid": "입력 완료", "same_day": "당일", "following_day": "익일", "total": "합계"};
    function quoteCell(value) { return '"' + String(value).replace(/"/g, '""') + '"'; }
    function createCsv(rows) {
        var result = calculateWeek(rows);
        if (!result.ok) return result;
        var records = [csvLabels.columns.slice()];
        result.days.forEach(function (day) {
            if (day.status === 'empty') {
                records.push([csvLabels.days[day.index], csvLabels.empty, '', '', '', '', '', '', '']);
            } else {
                records.push([csvLabels.days[day.index], csvLabels.valid, day.start, day.end,
                    day.nextDay ? csvLabels.following_day : csvLabels.same_day,
                    day.grossMinutes, day.breakMinutes, day.netMinutes, day.decimalHours]);
            }
        });
        records.push([csvLabels.total, '', '', '', '', result.totals.grossMinutes,
            result.totals.breakMinutes, result.totals.netMinutes, result.totals.decimalHours]);
        return { ok: true, csv: '\uFEFF' + records.map(function (record) {
            return record.map(quoteCell).join(',');
        }).join('\r\n') };
    }
    return Object.freeze({ calculateWeek: calculateWeek, createCsv: createCsv });
}));
