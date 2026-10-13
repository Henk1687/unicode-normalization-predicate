import unicodedata
import unittest

from unicode_normalization_predicate.core import (
    ALL_FORMS,
    NormalizationForms,
    UnknownFormError,
    is_normalized,
    which_forms,
)


class TestWhichForms(unittest.TestCase):

    def test_empty_string_satisfies_all_forms(self):
        result = which_forms("")
        self.assertEqual(list(result), list(ALL_FORMS))
        self.assertTrue(result.NFC)
        self.assertTrue(result.NFD)
        self.assertTrue(result.NFKC)
        self.assertTrue(result.NFKD)

    def test_pure_ascii_satisfies_all_forms(self):
        result = which_forms("hello world 123 !")
        self.assertEqual(list(result), list(ALL_FORMS))

    def test_precomposed_e_acute_is_nfc_but_not_nfd(self):
        result = which_forms("\u00e9")  # U+00E9 LATIN SMALL LETTER E WITH ACUTE
        self.assertIn("NFC", list(result))
        self.assertIn("NFKC", list(result))
        self.assertNotIn("NFD", list(result))
        self.assertNotIn("NFKD", list(result))

    def test_decomposed_e_acute_is_nfd_but_not_nfc(self):
        result = which_forms("e\u0301")  # U+0065 + U+0301 COMBINING ACUTE ACCENT
        self.assertIn("NFD", list(result))
        self.assertIn("NFKD", list(result))
        self.assertNotIn("NFC", list(result))
        self.assertNotIn("NFKC", list(result))

    def test_compatibility_fullwidth_satisfies_only_kc_kd(self):
        s = "\uff21"  # U+FF21 FULLWIDTH LATIN CAPITAL LETTER A
        result = which_forms(s)
        self.assertIn("NFC", list(result))
        self.assertIn("NFD", list(result))
        self.assertNotIn("NFKC", list(result))
        self.assertNotIn("NFKD", list(result))

    def test_comp_form_when_kc_transforms_is_not_kc(self):
        s = "\u00e9\uff21"  # precomposed e + fullwidth A
        kc_normalized = unicodedata.normalize("NFKC", s)
        self.assertNotEqual(s, kc_normalized)
        result = which_forms(s)
        self.assertNotIn("NFKC", list(result))
        self.assertNotIn("NFKD", list(result))

    def test_string_satisfying_all_four_forms(self):
        # No compatibility characters, no combining sequences.
        result = which_forms("abcXYZ123")
        self.assertEqual(list(result), list(ALL_FORMS))

    def test_string_satisfying_none_when_compat_changes_differ(self):
        s = "\u00e9\uff21"  # NFC-yes (precomposed) but NFKC-no
        result = which_forms(s)
        self.assertIn("NFC", list(result))
        self.assertNotIn("NFD", list(result))
        self.assertNotIn("NFKC", list(result))
        self.assertNotIn("NFKD", list(result))

    def test_filter_to_requested_forms_only(self):
        result = which_forms("e\u0301", forms=["NFC"])
        self.assertFalse(result.NFC)
        self.assertFalse(result.NFD)
        self.assertFalse(result.NFKC)
        self.assertFalse(result.NFKD)

    def test_forms_argument_case_insensitive(self):
        lower = which_forms("\u00e9", forms=["nfc"])
        upper = which_forms("\u00e9", forms=["NFC"])
        self.assertEqual(lower, upper)
        self.assertTrue(lower.NFC)

    def test_results_are_hashable_and_equal(self):
        a = which_forms("abc")
        b = which_forms("xyz")
        self.assertEqual(hash(a), hash(b))
        self.assertEqual(a, b)

    def test_iter_yields_satisfied_form_names(self):
        result = which_forms("\u00e9")
        names = list(result)
        self.assertEqual(names, ["NFC", "NFKC"])


class TestIsNormalized(unittest.TestCase):

    def test_true_for_satisfied_form(self):
        self.assertTrue(is_normalized("\u00e9", "NFC"))

    def test_false_for_unsatisfied_form(self):
        self.assertFalse(is_normalized("\u00e9", "NFD"))

    def test_case_insensitive(self):
        self.assertTrue(is_normalized("\u00e9", "nfc"))


class TestErrors(unittest.TestCase):

    def test_non_string_text_raises_type_error(self):
        with self.assertRaises(TypeError):
            which_forms(b"abc")

    def test_unknown_form_name_raises(self):
        with self.assertRaises(UnknownFormError):
            which_forms("abc", forms=["NFC", "BOGUS"])

    def test_empty_forms_iterable_raises(self):
        with self.assertRaises(UnknownFormError):
            which_forms("abc", forms=[])

    def test_unknown_form_in_is_normalized_raises(self):
        with self.assertRaises(UnknownFormError):
            is_normalized("abc", "XXX")


if __name__ == "__main__":
    unittest.main()
