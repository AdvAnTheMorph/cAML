"""Test Label"""

import unittest

from analogical_modeling.am.label.label import Label
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.am.label.missing_data_compare import NonspecifiedDataCompare
from analogical_modeling.tests.am.test_utils import mock_instance


class TestLabel(unittest.TestCase):


    def test_equivalence(self):
        """test that __eq__() and __hash__() work correctly and agree"""

        def assert_label_equals(first_label: Label, second_label: Label):
            self.assertEqual(first_label, second_label)
            self.assertEqual(second_label, first_label)
            self.assertEqual(hash(first_label), hash(second_label))

        def assert_label_not_equivalent(first_label: Label,
                                        second_label: Label):
            self.assertNotEqual(first_label, second_label)
            self.assertNotEqual(second_label, first_label)
            # technically not always true, but it's a good test on our small set
            self.assertTrue(hash(first_label) != hash(second_label))

        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)

        first_label = labeler.from_bits(0b001)
        second_label = labeler.from_bits(0b001)
        third_label = labeler.from_bits(0b101)

        assert_label_equals(first_label, second_label)
        assert_label_equals(first_label, first_label)
        assert_label_equals(second_label, second_label)

        assert_label_not_equivalent(first_label, third_label)
        assert_label_not_equivalent(second_label, third_label)

    def test_get_cardinality(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)
        test_label = labeler.from_bits(0b001)
        self.assertEqual(test_label.card, 3)

    def test_matches(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)
        test_label = labeler.from_bits(0b001)
        matches = [False, True, True]
        for i, match_ in enumerate(matches):
            self.assertEqual(test_label.matches(i), match_)

        matches = [False, True, False]
        test_label = labeler.from_bits(0b101)
        for i, match_ in enumerate(matches):
            self.assertEqual(test_label.matches(i), match_)

    def test_intersect(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)

        label1 = labeler.from_bits(0b001)
        label2 = labeler.from_bits(0b100)
        matches = [False, True, False]
        intersected = label1.intersect(label2)
        for i, match_ in enumerate(matches):
            self.assertEqual(intersected.matches(i), match_)

    def test_union(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)

        label1 = labeler.from_bits(0b001)
        label2 = labeler.from_bits(0b100)
        unioned = label1.union(label2)
        for i in range(unioned.card):
            self.assertTrue(unioned.matches(i))

    def test_all_matching(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)
        self.assertTrue(labeler.from_bits(0b000).all_matching())
        for bits in [0b100, 0b010, 0b111]:
            self.assertFalse(labeler.from_bits(bits).all_matching())

    def test_matches_throws_exception_for_index_too_low(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)
        test_label = labeler.from_bits(0b001)
        with self.assertRaises(ValueError):
            test_label.matches(-10)

    def test_matches_throws_exception_for_index_too_high(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)
        test_label = labeler.from_bits(0b001)
        with self.assertRaises(ValueError):
            test_label.matches(3)

    def test_descendant_iterator(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)
        label = labeler.from_bits(0b100)

        expected_labels = {labeler.from_bits(0b101), labeler.from_bits(0b111),
                           labeler.from_bits(0b110)}
        actual_labels = set(label.descendant_iterator())
        self.assertEqual(expected_labels, actual_labels)

        # comparing:
        # V , O , V , I , 0 , ? , O , T , T , A , A
        # V , U , V , O , 0 , ? , 0 , ? , L , E , A
        labeler = Labeler(mock_instance(10), False, NonspecifiedDataCompare.VARIABLE)
        label = labeler.from_bits(0b0101001111)

        expected_labels = {labeler.from_bits(0b0101011111),
                           labeler.from_bits(0b0101111111),
                           labeler.from_bits(0b0101101111),
                           labeler.from_bits(0b0111101111),
                           labeler.from_bits(0b0111111111),
                           labeler.from_bits(0b0111011111),
                           labeler.from_bits(0b0111001111),
                           labeler.from_bits(0b1111001111),
                           labeler.from_bits(0b1111011111),
                           labeler.from_bits(0b1111111111),
                           labeler.from_bits(0b1111101111),
                           labeler.from_bits(0b1101101111),
                           labeler.from_bits(0b1101111111),
                           labeler.from_bits(0b1101011111),
                           labeler.from_bits(0b1101001111)}
        actual_labels = set(label.descendant_iterator())
        self.assertEqual(expected_labels, actual_labels)

    def test_is_descendant_of(self):
        labeler = Labeler(mock_instance(3), False, NonspecifiedDataCompare.MATCH)
        parent_label = labeler.from_bits(0b100)
        descendant_label = labeler.from_bits(0b101)
        self.assertTrue(descendant_label.is_descendant_of(parent_label))

        non_descendant_label = labeler.from_bits(0b001)
        self.assertFalse(non_descendant_label.is_descendant_of(parent_label))

    def test_to_string(self):
        label_bits = 0b1010101000111
        labeler = Labeler(mock_instance(13), False, NonspecifiedDataCompare.MATCH)
        label = labeler.from_bits(label_bits)
        self.assertEqual(bin(label_bits)[2:], str(label))

    def test_to_string_all_zeroes(self):
        labeler = Labeler(mock_instance(13), False, NonspecifiedDataCompare.MATCH)
        label = labeler.from_bits(0)
        self.assertEqual("0000000000000", str(label))

    def test_to_string_no_attributes(self):
        labeler = Labeler(mock_instance(0), False, NonspecifiedDataCompare.MATCH)
        label = labeler.from_bits(0)
        self.assertEqual("", str(label))

    def test_constructor(self):
        label = Label({0, 2}, 3)
        self.assertEqual(3, label.card)
        self.assertFalse(label.matches(0))
        self.assertTrue(label.matches(1))
        self.assertFalse(label.matches(2))

        label = Label({0, 2, 32}, 33)
        self.assertEqual(33, label.card)
        self.assertFalse(label.matches(0))
        self.assertTrue(label.matches(1))
        self.assertFalse(label.matches(2))
        for i in range(3, 32):
            self.assertTrue(label.matches(i))
        self.assertFalse(label.matches(32))

    def test_label_bits(self):
        label = Label({0, 1}, 4)
        self.assertEqual({0, 1}, label.label_bits)

        label = Label({0, 1, 32}, 33)
        self.assertEqual({0, 1, 32}, label.label_bits)

    def test_copy_constructor(self):
        first_label = Label({2}, 3)
        second_label = Label(first_label)
        self.assertEqual(second_label, first_label)
