import solarLunar from 'solarlunar';

export function convertLunarToSolar(year: number, month: number, day: number): { year: number; month: number; day: number } {
    // solarlunar.lunar2solar returns an object with cYear, cMonth, cDay (Solar date)
    const result = solarLunar.lunar2solar(year, month, day);

    if (result === -1) {
        throw new Error('Invalid Lunar Date');
    }

    return {
        year: result.cYear,
        month: result.cMonth,
        day: result.cDay
    };
}
