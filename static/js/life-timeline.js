(function (root) {
    'use strict';

    const ZODIAC = ['원숭이', '닭', '개', '돼지', '쥐', '소', '호랑이', '토끼', '용', '뱀', '말', '양'];
    const RELATED_TOOL_DESTINATIONS = {
        '/age': 'age',
        '/birthday-dday-calculator': 'birthday_dday',
        '/birth-year-zodiac-table': 'birth_year_zodiac'
    };

    function trackEvent(name, params) {
        if (root.AgeCalcTracking && typeof root.AgeCalcTracking.trackEvent === 'function') {
            root.AgeCalcTracking.trackEvent(name, params);
        }
    }

    function parseIso(value) {
        const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || ''));
        if (!match) throw new Error('invalid date');
        const year = Number(match[1]);
        const month = Number(match[2]);
        const day = Number(match[3]);
        const parsed = new Date(Date.UTC(year, month - 1, day));
        if (parsed.getUTCFullYear() !== year || parsed.getUTCMonth() !== month - 1 || parsed.getUTCDate() !== day) {
            throw new Error('invalid date');
        }
        return parsed;
    }

    function iso(date) {
        return date.toISOString().slice(0, 10);
    }

    function dateForAge(year, month, day) {
        const candidate = new Date(Date.UTC(year, month - 1, day));
        if (candidate.getUTCMonth() !== month - 1) return new Date(Date.UTC(year, 2, 1));
        return candidate;
    }

    function nextExactBirthday(birth, asOf) {
        let year = asOf.getUTCFullYear();
        while (true) {
            const candidate = new Date(Date.UTC(year, birth.getUTCMonth(), birth.getUTCDate()));
            const isExact = candidate.getUTCMonth() === birth.getUTCMonth() && candidate.getUTCDate() === birth.getUTCDate();
            if (isExact && candidate >= asOf) return candidate;
            year += 1;
        }
    }

    function constellation(month, day) {
        const value = month * 100 + day;
        if (value >= 1222 || value <= 119) return '염소자리';
        const boundaries = [
            [120, '물병자리'], [219, '물고기자리'], [321, '양자리'],
            [420, '황소자리'], [521, '쌍둥이자리'], [622, '게자리'],
            [723, '사자자리'], [823, '처녀자리'], [923, '천칭자리'],
            [1023, '전갈자리'], [1123, '사수자리']
        ];
        let label = '염소자리';
        boundaries.forEach(([boundary, name]) => {
            if (value >= boundary) label = name;
        });
        return label;
    }

    function buildLifeTimeline(birthIso, asOfIso) {
        const birth = parseIso(birthIso);
        const asOf = parseIso(asOfIso);
        if (birth > asOf) throw new Error('future date');

        const year = asOf.getUTCFullYear();
        const birthYear = birth.getUTCFullYear();
        const birthdayThisYear = dateForAge(year, birth.getUTCMonth() + 1, birth.getUTCDate());
        const nextBirthday = nextExactBirthday(birth, asOf);
        const dayMs = 24 * 60 * 60 * 1000;

        return {
            fullAge: year - birthYear - (asOf < birthdayThisYear ? 1 : 0),
            yearAge: year - birthYear,
            daysLived: Math.round((asOf - birth) / dayMs),
            nextBirthday: iso(nextBirthday),
            daysUntilBirthday: Math.round((nextBirthday - asOf) / dayMs),
            zodiac: ZODIAC[birthYear % 12],
            constellation: constellation(birth.getUTCMonth() + 1, birth.getUTCDate())
        };
    }

    function formatKoreanDate(value) {
        const parsed = parseIso(value);
        return `${parsed.getUTCFullYear()}년 ${parsed.getUTCMonth() + 1}월 ${parsed.getUTCDate()}일`;
    }

    function renderResult(result) {
        const dday = result.daysUntilBirthday === 0 ? '오늘' : `D-${result.daysUntilBirthday}`;
        return `
            <div class="life-timeline-track">
                <article class="life-moment is-now">
                    <span class="life-moment-dot" aria-hidden="true"></span>
                    <p class="eyebrow">지금</p>
                    <h3>만 ${result.fullAge}세</h3>
                    <p>출생연도 기준 연 나이는 ${result.yearAge}세입니다.</p>
                    <a href="/age">만 나이 계산 기준 보기</a>
                </article>
                <article class="life-moment">
                    <span class="life-moment-dot" aria-hidden="true"></span>
                    <p class="eyebrow">지나온 시간</p>
                    <h3>${result.daysLived.toLocaleString('ko-KR')}일</h3>
                    <p>출생일부터 오늘까지의 순수한 날짜 차이입니다.</p>
                </article>
                <article class="life-moment is-next">
                    <span class="life-moment-dot" aria-hidden="true"></span>
                    <p class="eyebrow">다음 생일 · ${dday}</p>
                    <h3>${formatKoreanDate(result.nextBirthday)}</h3>
                    <p>${result.daysUntilBirthday === 0 ? '오늘이 생일입니다.' : `다음 생일까지 ${result.daysUntilBirthday}일 남았습니다.`}</p>
                    <a href="/birthday-dday-calculator">생일 D-day 자세히 보기</a>
                </article>
                <article class="life-moment is-profile">
                    <span class="life-moment-dot" aria-hidden="true"></span>
                    <p class="eyebrow">출생 프로필</p>
                    <h3>${result.zodiac}띠 · ${result.constellation}</h3>
                    <p>띠는 출생연도 기준이며 음력 설·입춘 기준과 다를 수 있습니다.</p>
                    <a href="/birth-year-zodiac-table">출생연도별 띠표 보기</a>
                </article>
            </div>`;
    }

    function bindPage() {
        const form = document.getElementById('life-timeline-form');
        if (!form || !root.AgeCalcDateRules) return;
        const input = document.getElementById('life-birth-date');
        const error = document.getElementById('life-timeline-error');
        const result = document.getElementById('life-timeline-result');
        const asOf = form.dataset.today;

        result.addEventListener('click', (event) => {
            const link = event.target.closest('a[href]');
            const destination = link && RELATED_TOOL_DESTINATIONS[link.getAttribute('href')];
            if (destination) {
                trackEvent('life_timeline_related_tool_click', {
                    calculator: 'life_timeline',
                    destination
                });
            }
        });

        input.addEventListener('input', () => {
            input.value = root.AgeCalcDateRules.formatDateDigits(input.value);
            const digits = input.value.replace(/\D/g, '');
            if (digits.length < 8) {
                error.textContent = '';
                result.hidden = true;
                result.innerHTML = '';
                return;
            }
            try {
                const birthDate = root.AgeCalcDateRules.parseDateDigits(input.value);
                const timeline = buildLifeTimeline(iso(birthDate), asOf);
                error.textContent = '';
                input.classList.remove('error');
                result.innerHTML = renderResult(timeline);
                result.hidden = false;
                trackEvent('life_timeline_complete', { calculator: 'life_timeline' });
            } catch (exception) {
                error.textContent = String(exception.message).includes('future')
                    ? '미래 날짜는 입력할 수 없습니다.'
                    : '존재하는 생년월일 8자리를 입력해 주세요.';
                input.classList.add('error');
                result.hidden = true;
                result.innerHTML = '';
            }
        });
    }

    if (typeof document !== 'undefined') document.addEventListener('DOMContentLoaded', bindPage);
    if (typeof module !== 'undefined' && module.exports) module.exports = { buildLifeTimeline };
}(typeof window !== 'undefined' ? window : globalThis));
