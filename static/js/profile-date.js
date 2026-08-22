(function (root) {
    'use strict';

    const STORAGE_KEY = 'agecalc.profileBirthDate.v1';

    function storageOrDefault(storage) {
        if (storage) return storage;
        try { return root.localStorage; } catch (error) { return null; }
    }

    function isValidIsoDate(value) {
        const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ''));
        if (!match) return false;
        const year = Number(match[1]);
        const month = Number(match[2]);
        const day = Number(match[3]);
        const parsed = new Date(Date.UTC(year, month - 1, day));
        return parsed.getUTCFullYear() === year
            && parsed.getUTCMonth() === month - 1
            && parsed.getUTCDate() === day;
    }

    function saveProfileDate(value, storage) {
        if (!isValidIsoDate(value)) throw new Error('valid ISO date required');
        const target = storageOrDefault(storage);
        if (!target) return false;
        target.setItem(STORAGE_KEY, value);
        return true;
    }

    function loadProfileDate(storage) {
        const target = storageOrDefault(storage);
        if (!target) return null;
        const value = target.getItem(STORAGE_KEY);
        if (!value) return null;
        if (!isValidIsoDate(value)) {
            target.removeItem(STORAGE_KEY);
            return null;
        }
        return value;
    }

    function clearProfileDate(storage) {
        const target = storageOrDefault(storage);
        if (target) target.removeItem(STORAGE_KEY);
    }

    function formattedValue(value, mode) {
        const [year, month, day] = value.split('-');
        return mode === 'month-day' ? `${month}.${day}` : `${year}.${month}.${day}`;
    }

    function bindPage() {
        const inputs = Array.from(document.querySelectorAll('[data-profile-date-input]'));
        const consent = document.getElementById('profile-date-consent');
        const clearButton = document.getElementById('profile-date-clear');

        setTimeout(() => {
            const stored = loadProfileDate();
            if (!stored) return;
            inputs.forEach(input => {
                if (input.value) return;
                input.value = formattedValue(stored, input.dataset.profileDateInput);
                input.dispatchEvent(new Event('input', { bubbles: true }));
            });
            if (consent) consent.checked = true;
        }, 0);

        inputs.forEach(input => {
            input.addEventListener('input', () => {
                if (!consent || !consent.checked || input.dataset.profileDateInput !== 'full') return;
                const digits = input.value.replace(/\D/g, '');
                if (digits.length !== 8) return;
                const value = `${digits.slice(0, 4)}-${digits.slice(4, 6)}-${digits.slice(6, 8)}`;
                if (isValidIsoDate(value)) saveProfileDate(value);
            });
        });

        consent?.addEventListener('change', () => {
            if (!consent.checked) {
                clearProfileDate();
                return;
            }
            const fullInput = inputs.find(input => input.dataset.profileDateInput === 'full');
            fullInput?.dispatchEvent(new Event('input', { bubbles: true }));
        });

        clearButton?.addEventListener('click', () => {
            clearProfileDate();
            if (consent) consent.checked = false;
        });
    }

    if (typeof document !== 'undefined') document.addEventListener('DOMContentLoaded', bindPage);
    if (typeof module !== 'undefined' && module.exports) {
        module.exports = { saveProfileDate, loadProfileDate, clearProfileDate };
    }
}(typeof window !== 'undefined' ? window : globalThis));
