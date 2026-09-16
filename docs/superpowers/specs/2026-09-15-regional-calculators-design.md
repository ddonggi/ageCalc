# Regional calculator release

User approved five features and seven public documents. No deployment, push or merge.

## Public documents

- ko `/lunar-birthday-calculator`: lunar month/day, leap flag, reference date; current and next five lunar years, unavailable occurrences explicitly marked. Korea calendar only.
- ja `/ja/business-days-calculator`, pt-BR `/pt-br/business-days-calculator`: inclusive date-range count with optional final-day exclusion; add/subtract N workdays excluding the starting date; Saturday/Sunday plus national holidays plus custom dates. Initially 2025–2027 only, no automatic municipal/state holidays.
- ja `/ja/school-year-calculator`: birth date, optional gap years and university course length (2/4/6 years); expected elementary, junior, high-school and university admission/graduation years. April 1 / April 2 cohort boundary. Not official enrollment certification.
- en `/en/date-of-birth-calculator`, pt-BR `/pt-br/date-of-birth-calculator`: completed integer age at a reference date -> inclusive possible birth-date interval. Leap-day birthday policy must match implementation and be documented. No invented exact birthdate.
- ja `/ja/japanese-era-converter`: Gregorian date -> named Japanese era date and back. Meiji through Reiwa; explicit earliest supported date and exact era boundaries. No historic lunisolar conversion.

## Architecture

Use the existing Flask page registry and locale allowlists. Add pure Python calculation functions and a regional SSR form template extending the existing visual tokens. POST only for personal inputs; no query-string results, persistence or analytics payloads. Form errors and result tables are server rendered and usable without JavaScript. POST results are noindex and no-store, canonical remains the clean GET document. Unknown parameters, invalid dates and unsupported ranges fail visibly.

Only supported locales appear in tool navigation and sitemap. Foreign-only registry entries must not create phantom Korean URLs. Real equivalents alone get reciprocal hreflang; singleton pages omit it. No IP redirects.

Source-backed holiday tables are local, bounded and versioned. Japan uses the Cabinet Office calendar. Brazil includes national statutory dates only; optional closures and local religious dates are user exclusions. Lunar conversion uses the existing library with checked return values and strict supported-range handling. All locale-specific rules have boundary fixtures.

## Verification

Pure unit tests for all five engines and invalid inputs; Flask tests for seven GET/POST pages, locale gates, SSR content, canonical/hreflang, sitemap uniqueness and no-store. Run existing Python and JS regressions. Browser checks if the existing browser harness is available. Korean content uses humanize-korean. Existing UI hierarchy, typography and responsive date-form patterns remain unchanged.
