"""Test Supracontext variants"""

import unittest

from analogical_modeling.am.data.basic_supra import BasicSupra
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.lattice.linked_lattice_node import LinkedLatticeNode
from analogical_modeling.tests.am import test_utils

supras = [BasicSupra, ClassifiedSupra, lambda: LinkedLatticeNode(BasicSupra())]


class SupracontextTest(unittest.TestCase):


    def test_count(self):
        for supra in supras:
            test_supra = supra()
            self.assertEqual(1, test_supra.get_count())
            test_supra.set_count(42)
            self.assertEqual(42, test_supra.get_count())

    def test_set_count_throws_error_when_arg_is_none(self):
        for supra in supras:
            test_supra = supra()
            with self.assertRaises(ValueError):
                test_supra.set_count(None)

    def test_default_get_context(self):
        for supra in supras:
            test_supra = supra()
            for bits in [{1, 3}, {1, 3}, {1, 4}, {3, 4}]:
                test_supra.add(Subcontext(Label(bits, 5), "foo"))
            self.assertEqual(Label({1, 3, 4}, 5), test_supra.get_context(),
                             "Label should be intersect of subcontext labels")

            test_supra.add(Subcontext(Label({0, 3}, 5), "foo"))
            self.assertEqual(Label({0, 1, 3, 4}, 5), test_supra.get_context(),
                             "New context should be intersected with previous "
                             "one")

    def test_set_count_throws_error_when_arg_is_less_than_zero(self):
        for supra in supras:
            test_supra = supra()
            with self.assertRaises(ValueError):
                test_supra.set_count(-1)

    def test_is_empty(self):
        for supra in supras:
            test_supra = supra()
            self.assertTrue(test_supra.is_empty())
            test_supra.add(Subcontext(Label({0}, 1), "foo"))
            self.assertFalse(test_supra.is_empty())

    def test_data(self):
        sub1 = Subcontext(Label({0}, 1), "foo")
        sub2 = Subcontext(Label({0}, 2), "foo")
        for supra in supras:
            test_supra = supra()
            test_supra.add(sub1)
            test_supra.add(sub2)
            self.assertTrue(sub1 in test_supra.get_data())
            self.assertTrue(sub2 in test_supra.get_data())

    def test_copy(self):
        sub1 = Subcontext(Label({0}, 1), "foo")
        sub2 = Subcontext(Label({0}, 2), "foo")
        for supra in supras:
            test_supra = supra()
            test_supra.add(sub1)
            test_supra.add(sub2)

            test_supra2 = test_supra.copy()
            self.assertEqual(type(test_supra), type(test_supra2))
            self.assertTrue(
                test_utils.supra_deep_equals(test_supra, test_supra2))
            self.assertIsNot(test_supra, test_supra2)

    def test_equals_and_hash_code(self):
        sub1 = Subcontext(Label(set(), 1), "foo")
        sub2 = Subcontext(Label(set(), 2), "foo")
        for supra in supras:
            test_supra1 = supra()
            test_supra2 = supra()

            test_supra1.add(sub1)
            test_supra1.add(sub2)
            self.assertNotEqual(test_supra1, test_supra2)
            self.assertNotEqual(hash(test_supra1), hash(test_supra2))

            test_supra2.add(sub1)
            test_supra2.add(sub2)
            self.assertEqual(test_supra1, test_supra2)
            self.assertEqual(hash(test_supra1), hash(test_supra2))

            test_supra1.set_count(29)
            self.assertEqual(test_supra1, test_supra2,
                             "Count is not compared for equality")
            self.assertEqual(hash(test_supra1), hash(test_supra2),
                             "Count does not affect Hash")
