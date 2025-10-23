"""weka.classifiers.lazy.AM.label"""

import unittest

from analogical_modeling.am.label.missing_data_compare import \
    MissingDataCompare
from analogical_modeling.utils import Dataset


class TestMissingDataCompare(unittest.TestCase):
    def setUp(self):
        self.dataset = Dataset([["="], [0]])

    def test_match(self):
        mdc = MissingDataCompare.MATCH
        self.assertTrue(mdc.matches(self.dataset[0], self.dataset[0], 0))
        self.assertTrue(mdc.matches(self.dataset[0], self.dataset[1], 0))
        self.assertTrue(mdc.matches(self.dataset[1], self.dataset[0], 0))

    def test_mismatch(self):
        mdc = MissingDataCompare.MISMATCH
        self.assertFalse(mdc.matches(self.dataset[0], self.dataset[0], 0))
        self.assertFalse(mdc.matches(self.dataset[0], self.dataset[1], 0))
        self.assertFalse(mdc.matches(self.dataset[1], self.dataset[0], 0))

    def test_variable(self):
        mdc = MissingDataCompare.VARIABLE
        self.assertTrue(mdc.matches(self.dataset[0], self.dataset[0], 0))
        self.assertFalse(mdc.matches(self.dataset[0], self.dataset[1], 0))
        self.assertFalse(mdc.matches(self.dataset[1], self.dataset[0], 0))
