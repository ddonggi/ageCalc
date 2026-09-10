# Days between dates implementation

## Scope

Add `/days-between-dates` and five foreign prefixed equivalents. Preserve existing age, birthday and D-day routes. D-day compares today with a target; this tool compares two chosen calendar dates.

1. Reuse the common locale-neutral date rules and shared SSR calculator layout. Enable the shared renderer for a new Korean page without migrating legacy Korean calculators.
2. Inputs: two dates, optional inclusive end date, swap and reset. Outputs: total calendar days, whole weeks plus remaining days, both chosen dates and counting convention. Same date is zero, or one when inclusive. Reject reversed dates with a translated message and offer an explicit swap action. No business days, holidays or time-of-day calculations.
3. Store page-specific copy and UI in each locale catalog. Add registry-driven language links, self canonical, sitemap entries and related-tool links. Preserve existing Korean header styling.
4. Validate calendar boundaries, SSR/SEO in six languages, invalid/reversed inputs, inclusive totals, swap, reset, mobile layout and private-input handling. Restart only the development server on port 8000 for review.

Inputs remain browser-only and are not sent to analytics, storage or URLs. Analytics instrumentation and production deployment are separate follow-up steps, not part of this implementation.

## Verification (2026-09-10)

- Focused Python suite: 101 tests passed, covering locale routing/SEO, registry, AdSense preflight, privacy, static assets and existing theme contracts.
- Pure JavaScript calendar/date-range contracts passed, including leap years, DST boundaries, inclusive counting and invalid/reversed dates.
- Existing 30 localized calculator browser flows passed, including JS-off navigation, privacy and responsive checks.
- New calculator browser coverage spans all six locales: inclusive/exclusive totals, swap, same day, invalid dates, leap day, reset, private inputs, 320/1280px overflow and JS-off navigation.
- Registry-driven review sitemap now contains 80 URLs. The production count is expected to increase by six after a separate deployment; production has not been changed by this feature work.

Development review: `http://127.0.0.1:8000/days-between-dates`, with `/en/`, `/ja/`, `/es/`, `/pt-br/` and `/zh-cn/` equivalents.
