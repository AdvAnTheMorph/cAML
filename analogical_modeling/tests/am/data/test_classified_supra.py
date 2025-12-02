"""Test ClassifiedSupra."""

import unittest
from math import isnan

from analogical_modeling.am import am_utils
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.utils import Dataset


class ClassifiedSupraTest(unittest.TestCase):


    def setUp(self):
        self.dataset = Dataset([[1, "r"], [1, "e"], [0, "e"]])

        self.subs = []
        sub = Subcontext(Label({0}, 1), "foo")
        sub.add(self.dataset[0])
        sub.add(self.dataset[1])
        self.subs.append(sub)

        sub = Subcontext(Label({0}, 1), "foo")
        sub.add(self.dataset[0])
        sub.add(self.dataset[2])
        self.subs.append(sub)

        sub = Subcontext(Label({0}, 1), "foo")
        sub.add(self.dataset[0])
        self.subs.append(sub)

        sub = Subcontext(Label({0}, 1), "foo")
        sub.add(self.dataset[1])
        self.subs.append(sub)

        sub = Subcontext(Label({0}, 1), "foo")
        sub.add(self.dataset[2])
        self.subs.append(sub)

    def assert_causes_heterogeneity(self, supra: ClassifiedSupra,
                                    sub: Subcontext, causes: bool):
        self.assertFalse(supra.is_heterogeneous())
        self.assertEqual(causes, supra.would_be_hetero(sub))
        supra.add(sub)
        self.assertEqual(causes, supra.is_heterogeneous())

    def test_default_contents(self):
        test_supra = ClassifiedSupra()
        self.assertTrue(len(test_supra.get_data()) == 0)
        self.assertTrue(test_supra.is_empty())
        # AMUtils.UNKNOWN is Double.NaN
        self.assertTrue(isnan(test_supra.outcome))
        self.assertFalse(test_supra.is_heterogeneous())
        self.assertEqual(test_supra, test_supra)

    # TODO: remove this test, and instead don't have a constructor that takes
    # data like this (add() is tested in SupracontextTest).
    def test_data(self):
        test_supra = ClassifiedSupra()
        self.assertEqual(frozenset(), test_supra.get_data())

        label = Label({0}, 3)
        sub1 = Subcontext(label, "foo")
        sub2 = Subcontext(label, "foo")
        sub3 = Subcontext(label, "foo")
        test_supra = ClassifiedSupra({sub1, sub2, sub3}, 0)
        self.assertFalse(test_supra.is_empty())
        self.assertEqual({sub1, sub2, sub3}, test_supra.get_data())

    def test_setup(self):
        # make sure that the subs used for testing are set up properly
        self.assertTrue(self.subs[0].is_nondeterministic())
        self.assertTrue(self.subs[1].is_nondeterministic())
        self.assertFalse(self.subs[2].is_nondeterministic())
        self.assertFalse(self.subs[3].is_nondeterministic())
        self.assertFalse(self.subs[4].is_nondeterministic())

    def test_would_be_heterogeneous(self):
        # one sub, even nondeterministic, does not make a supra heterogeneous
        self.assert_causes_heterogeneity(ClassifiedSupra(), self.subs[0], False)
        self.assert_causes_heterogeneity(ClassifiedSupra(), self.subs[2], False)

        # two subs of same outcome do not make it heterogeneous
        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[3])
        self.assert_causes_heterogeneity(test_supra, self.subs[4], False)

        # conditions for heterogeneity:
        # nondeterministic sub with anything else
        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[0])
        self.assert_causes_heterogeneity(test_supra, self.subs[1], True)

        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[0])
        self.assert_causes_heterogeneity(test_supra, self.subs[2], True)

        # subs with differing outcomes
        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[2])
        self.assert_causes_heterogeneity(test_supra, self.subs[3], True)

        # supra is already heterogeneous
        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[2])
        test_supra.add(self.subs[3])
        self.assertTrue(test_supra.is_heterogeneous())
        self.assertTrue(test_supra.would_be_hetero(self.subs[4]))
        test_supra.add(self.subs[4])
        self.assertTrue(test_supra.is_heterogeneous())

    def test_is_heterogeneous(self):
        count = 0
        sub_set = set()

        #  empty supra is never heterogeneous
        self.assertFalse(ClassifiedSupra(sub_set, count).is_heterogeneous())

        # supra with two subs of the same outcome is not heterogeneous
        sub_set = {self.subs[3], self.subs[4]}
        self.assertFalse(ClassifiedSupra(sub_set, count).is_heterogeneous())

        # conditions for heterogeneity:
        # nondeterministic sub with anything else
        sub_set = {self.subs[0], self.subs[1]}
        self.assertTrue(ClassifiedSupra(sub_set, count).is_heterogeneous())

        sub_set = {self.subs[0], self.subs[2]}
        self.assertTrue(ClassifiedSupra(sub_set, count).is_heterogeneous())

        # subs with differing outcomes
        sub_set = {self.subs[2], self.subs[3]}
        self.assertTrue(ClassifiedSupra(sub_set, count).is_heterogeneous())

    def test_outcome(self):
        count = 0
        sub_set = {self.subs[3], self.subs[4]}  # e, e
        self.assertEqual("e", ClassifiedSupra(sub_set, count).outcome)

        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[3])  # e
        test_supra.add(self.subs[4])  # e
        self.assertEqual("e", ClassifiedSupra(sub_set, count).outcome)

        sub_set = {self.subs[2]}  # r
        self.assertEqual("r", ClassifiedSupra(sub_set, count).outcome)
        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[2])  # r
        self.assertEqual("r", ClassifiedSupra(sub_set, count).outcome)

        sub_set = {self.subs[0]}  # non-deterministic
        self.assertEqual(am_utils.NONDETERMINISTIC,
                         ClassifiedSupra(sub_set, count).outcome)
        test_supra = ClassifiedSupra()
        test_supra.add(self.subs[0])  # non-deterministic
        self.assertEqual(am_utils.NONDETERMINISTIC,
                         ClassifiedSupra(sub_set, count).outcome)
