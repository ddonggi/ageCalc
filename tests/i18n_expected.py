"""Independent URL baseline recorded from c81bd94 before localization."""
KOREAN_REVIEW_PATHS = frozenset('''
/
/about
/contact
/references
/privacy
/terms
/age
/birth-year-age-table
/age-gap-calculator
/baby-months-table
/annual-age-calculator
/age-comparison-table
/korean-age-guide
/birth-year-zodiac-table
/baby-months
/parent-child
/school-grade-calculator
/grade-birth-year-table
/college-entry-year-calculator
/100-day-calculator
/birthday-dday-calculator
/d-day
/pet-age-table
/pet-months-table
/dog
/cat
/guide
/faq
/guides/age-calculation-2026
/guides/reference-date-age-guide
/guides/lunar-birthday-age-guide
/guides/birth-year-age-table-guide
/guides/korean-age-vs-annual-age
/guides/sixtieth-seventieth-eightieth-age-guide
/guides/generation-by-birth-year-guide
/guides/school-entry-year-guide
/guides/elementary-school-entry-target-2026
/guides/school-grade-birth-year-guide
/guides/early-birth-school-grade-guide
/guides/baby-months-calculation-guide
/guides/100-day-calculation-guide
/guides/birthday-dday-calculation-guide
/guides/baby-anniversary-calculation-guide
/guides/parent-child-age-gap-guide
'''.split())
GLOBAL_SLUGS = ('age-calculator', 'birthday-dday-calculator', 'd-day', 'baby-months', '100-day-calculator', 'age-gap-calculator')
GLOBAL_PREFIXES = ('en', 'ja', 'es', 'pt-br', 'zh-cn')
REVIEW_URLS = {'https://agecalc.cloud' + path for path in KOREAN_REVIEW_PATHS} | {
    f'https://agecalc.cloud/{prefix}/{slug}' for prefix in GLOBAL_PREFIXES for slug in GLOBAL_SLUGS
}
