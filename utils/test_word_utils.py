import os, sys
FILE_PATH = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(FILE_PATH, '../'))

import unittest
from utils.word_utils import remove_accents, isword, correct


class RemoveAccentsTest(unittest.TestCase):
    def test_remove_accents(self):
        self.assertEqual(remove_accents("adénoïde"), "adenoide")

    def test_lower(self):
        self.assertEqual(remove_accents("A"), "a")

    def test_remove_spaces_and_dots(self):
        self.assertEqual(remove_accents("est-ce que ca va"), "estcequecava")


class IsWordTest(unittest.TestCase):
    def test_correct_word(self):
        self.assertTrue(isword("carapace"))

    def test_numerics(self):
        self.assertFalse(isword("carapace12"))

    def test_spaces(self):
        self.assertFalse(isword("super carapace"))

    def test_length(self):
        self.assertFalse(isword("le"))
        self.assertFalse(isword("anticonstitutionellement"))

class CorrectTest(unittest.TestCase):
    def test_correction(self):
        self.assertEqual(correct("pamme"), "pomme")
        self.assertEqual(correct("bannane"), "banane")
        self.assertEqual(correct("menger"), "manger")


if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RemoveAccentsTest))
    suite.addTest(unittest.makeSuite(IsWordTest))
    suite.addTest(unittest.makeSuite(CorrectTest))
    runner = unittest.TextTestRunner()
    runner.run(suite)