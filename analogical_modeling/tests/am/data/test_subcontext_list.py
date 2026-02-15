"""Test SubcontextList"""

import unittest

from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.am.label.missing_data_compare import MissingDataCompare
from analogical_modeling.tests.am import test_utils


class SubContextListTest(unittest.TestCase):


    @staticmethod
    def get_sub_list(subcontext_list: SubcontextList) -> list[Subcontext]:
        return list(subcontext_list)

    def test_chapter_3_data(self):
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        test = train[0]
        # train.remove(0)
        train.data.drop(index=0, inplace=True)

        labeler = Labeler(test, False, MissingDataCompare.MATCH)
        subs = SubcontextList(labeler, train, False)
        self.assertEqual(3, subs.get_cardinality())

        sub_list = self.get_sub_list(subs)
        self.assertEqual(4, len(sub_list))

        expected = Subcontext(Label({0}, 3), "foo")
        expected.add(train[0])  # 310e
        expected.add(train[4])  # 311r
        self.assertTrue(expected in sub_list)

        expected = Subcontext(Label({2}, 3), "foo")
        expected.add(train[3])  # 212r
        self.assertTrue(expected in sub_list)

        expected = Subcontext(Label({0, 2}, 3), "foo")
        expected.add(train[1])  # 210r
        self.assertTrue(expected in sub_list)

        expected = Subcontext(Label({1, 2}, 3), "foo")
        expected.add(train[2])  # 032r
        self.assertTrue(expected in sub_list)

    def test_ignore_full_matches(self):
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        test = train[0]
        labeler = Labeler(test, False, MissingDataCompare.MATCH)
        all_matching_sub = Subcontext(Label(set(), 3), "foo")
        all_matching_sub.add(train[0])  # 310e

        subs = SubcontextList(labeler, train, False)
        self.assertTrue(all_matching_sub in self.get_sub_list(subs),
                        "Should contain 000 sub when not ignoring full matches")

        subs = SubcontextList(labeler, train, True)
        self.assertFalse(all_matching_sub in self.get_sub_list(subs),
                         "Should not contain 000 sub when ignoring full "
                         "matches")

    def test_accessors(self):
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        test = train[0]
        train.data.drop(index=0, inplace=True)

        labeler = Labeler(test, False, MissingDataCompare.MATCH)

        subs = SubcontextList(labeler, train, False)
        self.assertEqual(labeler, subs.labeler,
                         "getLabeler returns the labeler used in the "
                         "constructor")
        self.assertEqual(3, subs.get_cardinality(),
                         "getCardinality returns the cardinality of the test item")
