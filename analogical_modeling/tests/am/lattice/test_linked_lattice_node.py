"""Test LinkedLatticeNode."""

import unittest

from analogical_modeling.am.data.basic_supra import BasicSupra
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.lattice.linked_lattice_node import LinkedLatticeNode
from analogical_modeling.tests.am import test_utils

supras = [BasicSupra, ClassifiedSupra]


class LinkedLatticeNodeTest(unittest.TestCase):
    """Test all implementations of LinkedLatticeNode for correctness."""

    def test_default_index_is_minus1(self):
        for supra in supras:
            test_node = LinkedLatticeNode(supra())
            self.assertEqual(test_node.get_index(), -1)

    def test_next(self):
        for supra in supras:
            test_node = LinkedLatticeNode(supra())
            self.assertIsNone(test_node.next)
            test_node.next = test_node
            self.assertEqual(test_node.next, test_node)

    def test_count(self):
        for supra in supras:
            test_node = LinkedLatticeNode(supra())
            self.assertEqual(1, test_node.count)
            test_node.increment_count()
            self.assertEqual(2, test_node.count)
            test_node.decrement_count()
            self.assertEqual(1, test_node.count)

    def test_decrement_count_throws_error_when_count_is_zero(self):
        for supra in supras:
            test_node = LinkedLatticeNode(supra())
            test_node.count = 0
            with self.assertRaises(ValueError):
                test_node.decrement_count()

    def test_insert_after(self):
        dataset = test_utils.get_dataset(test_utils.FINNVERB_MIN)
        for supra in supras:
            test_node1 = LinkedLatticeNode(supra())
            sub1 = Subcontext(Label({0}, 1), "foo")
            sub1.add(dataset[0])
            sub2 = Subcontext(Label({1}, 1), "foo")
            sub2.add(dataset[1])
            sub2.add(dataset[2])
            sub3 = Subcontext(Label({0}, 1), "foo")

            test_node2 = test_node1.insert_after(sub1, 11)
            expected = BasicSupra({sub1}, 1)
            self.assertEqual(test_node2, expected)
            self.assertEqual(11, test_node2.get_index())
            self.assertIs(test_node2, test_node1.next)
            self.assertIsNone(test_node2.next)

            test_node3 = test_node2.insert_after(sub2, 29)
            expected = BasicSupra({sub1, sub2}, 0)
            self.assertEqual(test_node3, expected)
            self.assertEqual(29, test_node3.get_index())
            self.assertIs(test_node3, test_node2.next)
            self.assertIsNone(test_node3.next)

            test_node4 = test_node2.insert_after(sub3, 37)
            expected = BasicSupra({sub1, sub3}, 0)
            self.assertEqual(test_node4, expected)
            self.assertIs(test_node4, test_node2.next)
            self.assertIs(test_node3, test_node4.next)

        # TODO: test copy, equals and hashCode for correctness regarding next
        #  variable
