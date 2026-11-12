import unittest

from app.collectors.text_normalization import normalize_text_for_comparison


class TextNormalizationTests(unittest.TestCase):
    def test_canonical_unicode_forms_compare_equal(self):
        self.assertEqual(
            normalize_text_for_comparison('Cafe\u0301 房源'),
            normalize_text_for_comparison('Café 房源'),
        )

    def test_unicode_whitespace_is_collapsed(self):
        self.assertEqual(
            normalize_text_for_comparison('Café\t\u00a0房源'),
            normalize_text_for_comparison('Café 房源'),
        )

    def test_compatibility_characters_are_not_rewritten(self):
        self.assertNotEqual(
            normalize_text_for_comparison('Ａ房源'),
            normalize_text_for_comparison('A房源'),
        )


if __name__ == '__main__':
    unittest.main()
