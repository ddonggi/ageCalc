(function (root, factory) {
    const api = factory();
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = api;
    } else {
        root.AgeCalcDateRules = api;
    }
}(typeof globalThis !== 'undefined' ? globalThis : this, function () {
    function parseIsoDate(value) {
        if (!/^\d{4}-\d{2}-\d{2}$/.test(String(value || ''))) {
            throw new Error('date must use a valid YYYY-MM-DD value');
        }
        const [year, month, day] = value.split('-').map(Number);
        const result = new Date(0);
        result.setUTCHours(0, 0, 0, 0);
        result.setUTCFullYear(year, month - 1, day);
        if (
            result.getUTCFullYear() !== year
            || result.getUTCMonth() !== month - 1
            || result.getUTCDate() !== day
        ) {
            throw new Error('date must use a valid YYYY-MM-DD value');
        }
        return result;
    }

    function formatIsoDate(value) {
        return `${value.getUTCFullYear()}-${String(value.getUTCMonth() + 1).padStart(2, '0')}-${String(value.getUTCDate()).padStart(2, '0')}`;
    }

    function parseBirthDateDigits(value, referenceDateValue) {
        const digits = String(value || '').replace(/\D/g, '');
        if (!/^\d{8}$/.test(digits)) {
            throw new Error('birth date must use 8 digits in YYYYMMDD format');
        }
        const birthDate = parseIsoDate(`${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`);
        const referenceDate = referenceDateValue
            ? parseIsoDate(referenceDateValue)
            : new Date(Date.UTC(new Date().getFullYear(), new Date().getMonth(), new Date().getDate()));
        if (birthDate > referenceDate) {
            throw new Error('birth date cannot be in the future');
        }
        return birthDate;
    }

    function calculateManAge(birthDateValue, referenceDateValue) {
        const birthDate = parseIsoDate(birthDateValue);
        const referenceDate = parseIsoDate(referenceDateValue);
        if (birthDate > referenceDate) {
            throw new Error('birth date cannot be in the future');
        }
        const birthdayPassed = referenceDate.getUTCMonth() > birthDate.getUTCMonth()
            || (
                referenceDate.getUTCMonth() === birthDate.getUTCMonth()
                && referenceDate.getUTCDate() >= birthDate.getUTCDate()
            );
        return referenceDate.getUTCFullYear() - birthDate.getUTCFullYear() - (birthdayPassed ? 0 : 1);
    }

    function addUtcDays(value, days) {
        const result = new Date(value.getTime());
        result.setUTCDate(result.getUTCDate() + days);
        return result;
    }

    function calculateCompletedMonths(birthDateValue, referenceDateValue) {
        const birthDate = parseIsoDate(birthDateValue);
        const referenceDate = parseIsoDate(referenceDateValue);
        if (birthDate > referenceDate) {
            throw new Error('birth date cannot be in the future');
        }
        let months = (referenceDate.getUTCFullYear() - birthDate.getUTCFullYear()) * 12;
        months += referenceDate.getUTCMonth() - birthDate.getUTCMonth();
        const anchorYear = birthDate.getUTCFullYear() + Math.floor((birthDate.getUTCMonth() + months) / 12);
        const anchorMonth = (birthDate.getUTCMonth() + months) % 12;
        const lastDay = new Date(Date.UTC(anchorYear, anchorMonth + 1, 0)).getUTCDate();
        const anchorDay = Math.min(birthDate.getUTCDate(), lastDay);
        const anchor = new Date(Date.UTC(anchorYear, anchorMonth, anchorDay));
        if (referenceDate < anchor) months -= 1;
        return Math.max(0, months);
    }

    return {
        parseIsoDate,
        parseBirthDateDigits,
        formatIsoDate,
        calculateManAge,
        calculateCompletedMonths,
        addUtcDays
    };
}));
