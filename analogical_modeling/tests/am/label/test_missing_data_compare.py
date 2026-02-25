"""Test handling of non-specified data"""

import unittest
import warnings

from analogical_modeling.am.label.missing_data_compare import \
    NonspecifiedDataCompare
from analogical_modeling.utils import Dataset


class TestMissingDataCompare(unittest.TestCase):
    def setUp(self):
        # Ignore warnings due to too small dataset
        warnings.filterwarnings("ignore", module="analogical_modeling")
        self.dataset = Dataset([["="], [0]])

    def test_match(self):
        ndc = NonspecifiedDataCompare.MATCH
        self.assertTrue(ndc.matches(self.dataset[0], self.dataset[0], 0))
        self.assertTrue(ndc.matches(self.dataset[0], self.dataset[1], 0))
        self.assertTrue(ndc.matches(self.dataset[1], self.dataset[0], 0))

    def test_mismatch(self):
        ndc = NonspecifiedDataCompare.MISMATCH
        self.assertFalse(ndc.matches(self.dataset[0], self.dataset[0], 0))
        self.assertFalse(ndc.matches(self.dataset[0], self.dataset[1], 0))
        self.assertFalse(ndc.matches(self.dataset[1], self.dataset[0], 0))

    def test_variable(self):
        ndc = NonspecifiedDataCompare.VARIABLE
        self.assertTrue(ndc.matches(self.dataset[0], self.dataset[0], 0))
        self.assertFalse(ndc.matches(self.dataset[0], self.dataset[1], 0))
        self.assertFalse(ndc.matches(self.dataset[1], self.dataset[0], 0))
