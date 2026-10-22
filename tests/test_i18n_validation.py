"""Editorial sections may differ by locale; UI contracts remain strict."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from content.i18n import catalog, validate_translations


class TranslationValidationTests(unittest.TestCase):
    def validate_page(self, mutate):
        changed = deepcopy(catalog('es'))
        mutate(changed['pages']['date_add_subtract'])
        real_catalog = catalog
        with patch('content.i18n.catalog', side_effect=lambda code: changed if code == 'es' else real_catalog(code)):
            validate_translations()

    def test_current_editorial_content_validates_without_overrides(self):
        validate_translations()

    def test_sections_and_paragraphs_may_have_different_counts(self):
        def expand(page):
            page['sections'].append({'heading': 'Más información', 'paragraphs': ['Uno.', 'Dos.', 'Tres.']})
            page['sections'][0]['paragraphs'].append('Otra explicación.')
        self.validate_page(expand)
        self.validate_page(lambda page: page.update(sections=[{'heading': 'Resumen', 'paragraphs': ['Una explicación.']}]))

    def test_rejects_missing_and_unknown_section_fields(self):
        for section in ({'heading': 'Hola'}, {'paragraphs': ['Hola']}, {'heading': 'Hola', 'paragraphs': ['Hola'], 'typo': 'Hola'}):
            with self.subTest(section=section), self.assertRaisesRegex(ValueError, r'Invalid translation: es.sections'):
                self.validate_page(lambda page: page.update(sections=[section]))

    def test_rejects_empty_or_wrongly_typed_editorial_containers(self):
        for sections in ([], {}, 'text', [None], [{'heading': 'Title', 'paragraphs': []}], [{'heading': 'Title', 'paragraphs': 'Text'}]):
            with self.subTest(sections=sections), self.assertRaisesRegex(ValueError, r'Invalid translation: es.sections'):
                self.validate_page(lambda page: page.update(sections=sections))

    def test_rejects_blank_nonstring_and_placeholder_editorial_text(self):
        for text in ('', ' \n ', None, 42, '{unexpected}', 'Texto {year}'):
            for field in ('heading', 'paragraphs'):
                section = {'heading': 'Title', 'paragraphs': ['Body']}
                section[field] = [text] if field == 'paragraphs' else text
                with self.subTest(text=text, field=field), self.assertRaisesRegex(ValueError, r'Invalid translation: es.sections'):
                    self.validate_page(lambda page: page.update(sections=[section]))

    def test_missing_sections_key_is_not_silently_accepted(self):
        with self.assertRaisesRegex(ValueError, 'Translation keys differ: es'):
            self.validate_page(lambda page: page.pop('sections'))

    def test_ui_fields_and_faq_still_require_matching_keys(self):
        for mutate in (lambda page: page.pop('h1'), lambda page: page['faq'].pop()):
            with self.subTest(mutate=mutate), self.assertRaisesRegex(ValueError, 'Translation keys differ: es'):
                self.validate_page(mutate)

    def test_ui_text_still_rejects_blanks_and_unexpected_placeholders(self):
        for text in (' ', 'Resultado {unexpected}'):
            with self.subTest(text=text), self.assertRaisesRegex(ValueError, 'Invalid translation: es'):
                self.validate_page(lambda page: page.update(h1=text))


if __name__ == '__main__':
    unittest.main()
