"""Test Subcontext"""

import unittest

from analogical_modeling import utils
from analogical_modeling.am import am_utils
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.label.label import Label


class SubcontextTest(unittest.TestCase):
    def setUp(self):
        # self.dataset = utils.Dataset([[1, 1], [1, 0]])
        self.dataset = utils.Dataset([[1, "r"], [1, "e"]])

    def test(self):
        label = Label(set(), 1)
        s = Subcontext(label, "foo")
        s.add(self.dataset[0])
        self.assertEqual({self.dataset[0]}, s.get_exemplars())
        self.assertEqual(Label(set(), 1), s.get_label())
        self.assertEqual("r", s.outcome)
        self.assertEqual("(0|r|1,r,{1})", str(s))

        s.add(self.dataset[1])
        self.assertEqual({self.dataset[0], self.dataset[1]}, s.get_exemplars())
        self.assertEqual(am_utils.NONDETERMINISTIC, s.outcome)

    #         // TODO: can't test toString() like this because data is an
    #          unordered
    #         // set
    #         // assertEquals("(0|&nondeterministic&|1,r,{2}/1,e,{2})", s.toString());
    #     }

    def test_to_string_with_empty_data(self):
        test_sub = Subcontext(Label({1}, 2), "foo")
        actual = str(test_sub)
        self.assertIsNotNone(actual)
