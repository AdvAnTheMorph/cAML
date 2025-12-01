"""Test Labeler"""

import unittest

import analogical_modeling.tests.am.test_utils as test_utils
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.label.labeler import Labeler, Partition
from analogical_modeling.am.label.missing_data_compare import MissingDataCompare


class LabelerTest(unittest.TestCase):
    """Test Labeler implementations"""

    def test_accessors(self):
        instance = test_utils.get_instance_from_file(test_utils.CHAPTER_3_DATA,
                                                     0)
        labeler = Labeler(instance, False, MissingDataCompare.MATCH)

        self.assertEqual(labeler.get_cardinality(), 3)
        self.assertFalse(labeler.get_ignore_unknowns())
        self.assertEqual(labeler.get_missing_data_compare(),
                         MissingDataCompare.MATCH)
        self.assertEqual(labeler.get_test_instance().all(), instance.all())

    def test_is_ignored(self):
        """Test the default behavior for Labeler.is_ignored(int).

        :return:
        """
        instance = test_utils.get_instance_from_file(test_utils.FINNVERB, 0)
        labeler = Labeler(instance, False, MissingDataCompare.MATCH)
        for i in range(instance.num_attributes()):
            self.assertFalse(labeler.is_ignored(i))

        labeler = Labeler(instance, True, MissingDataCompare.MATCH)
        for i in range(instance.num_attributes()):
            if instance.is_missing(i):
                self.assertTrue(labeler.is_ignored(i))
            else:
                self.assertFalse(labeler.is_ignored(i))

    def test_get_lattice_top(self):
        cardinality = 100
        labeler = Labeler(test_utils.mock_instance(cardinality), False,
                          MissingDataCompare.MATCH)
        top = labeler.get_lattice_top()
        self.assertEqual(cardinality, top.get_cardinality())
        for i in range(cardinality):
            self.assertTrue(top.matches(i))
        self.assertEqual(cardinality, top.num_matches())

    def test_get_lattice_bottom(self):
        cardinality = 32
        labeler = Labeler(test_utils.mock_instance(cardinality), False,
                          MissingDataCompare.MATCH)
        bottom = labeler.get_lattice_bottom()
        self.assertEqual(cardinality, bottom.get_cardinality())
        for i in range(cardinality):
            self.assertFalse(bottom.matches(i),
                             f"Attribute {i} should not match")
        self.assertEqual(0, bottom.num_matches(), "No attribute should match")

    def test_num_partitions(self):
        # current behavior is to always limit the size of a label to 5
        # 3 features, 1 partition
        data = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        self.assertEqual(1, labeler.num_partitions())

        # 8 features, 2 partitions
        data = test_utils.get_reduced_dataset(test_utils.FINNVERB, [0, 1])
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        self.assertEqual(2, labeler.num_partitions())

        # 10 features, 2 partitions
        data = test_utils.get_dataset(test_utils.FINNVERB)
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        self.assertEqual(2, labeler.num_partitions())

    def test_partitions(self):
        """Tests the protected default partitioning scheme."""

        def assert_partition_equals(partition: Partition, start_index: int,
                                    cardinality: int):
            self.assertEqual(start_index, partition.get_start_index())
            self.assertEqual(cardinality, partition.get_cardinality())

        data = test_utils.get_dataset(test_utils.FINNVERB)
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        partitions = labeler.partitions()
        self.assertEqual(2, len(partitions))
        assert_partition_equals(partitions[0], 0, 5)
        assert_partition_equals(partitions[1], 5, 5)

        data = test_utils.get_reduced_dataset(test_utils.FINNVERB, [0, 1])
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        partitions = labeler.partitions()
        self.assertEqual(2, len(partitions))
        assert_partition_equals(partitions[0], 0, 4)
        assert_partition_equals(partitions[1], 4, 4)

    def test_partition(self):
        """Tests the default partitioning functionality."""
        data = test_utils.get_dataset(test_utils.FINNVERB)
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        label = labeler.label(data[1])

        self.assertEqual(label, Label({1, 4, 5}, 10))
        self.assertEqual(labeler.num_partitions(), 2)

        self.assertEqual(labeler.partition(label, 0), Label({1, 4}, 5))
        self.assertEqual(labeler.partition(label, 1), Label({0}, 5))

    def test_label(self):
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        self.assertEqual(Label(set(), 5), labeler.label(dataset[1]))
        self.assertEqual(Label({1, 2, 4}, 5), labeler.label(dataset[2]))
        self.assertEqual(Label({0, 1}, 5), labeler.label(dataset[3]))
        self.assertEqual(Label({0, 1, 4}, 5), labeler.label(dataset[4]))
        self.assertEqual(Label({0, 1, 2, 3, 4}, 5), labeler.label(dataset[5]))

    def test_label_with_alternative_class_index(self):
        """Test with a different class index to make sure its location is not
        hard coded."""
        dataset = test_utils.six_cardinality_data()
        dataset.set_class_index(2)
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        self.assertEqual(Label({2, 4}, 5), labeler.label(dataset[2]))
        self.assertEqual(Label({0, 1, 2}, 5), labeler.label(dataset[3]))
        self.assertEqual(Label({1, 2, 4}, 5), labeler.label(dataset[4]))
        self.assertEqual(Label({0, 1, 2, 3, 4}, 5), labeler.label(dataset[5]))

    def test_get_context_label_missing_data_compares(self):
        """Test that missing values are compared based on the input MissingDataCompare value."""
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[6], False, MissingDataCompare.MATCH)
        self.assertEqual(Label({2}, 5), labeler.label(dataset[0]))

        labeler = Labeler(dataset[6], False, MissingDataCompare.MISMATCH)
        self.assertEqual(Label({0, 2}, 5), labeler.label(dataset[0]))

        labeler = Labeler(dataset[6], False, MissingDataCompare.VARIABLE)
        self.assertEqual(Label({2}, 5), labeler.label(dataset[7]))
        self.assertEqual(Label({0, 1, 2}, 5), labeler.label(dataset[8]))

    def test_get_context_list(self):
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        label = Label({0, 1, 3}, 5)
        actual = labeler.get_context_list(label, "*")
        self.assertEqual(list("a*v**"), actual)

    def test_get_context_string(self):
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        label = Label({0, 1, 3}, 5)
        actual = labeler.get_context_string(label)
        self.assertEqual("a * v * *", actual)

    def test_get_instance_atts_list(self):
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        actual = labeler.get_instance_atts_values_list(dataset[0])
        self.assertEqual(list("axvus"), actual)

    def test_get_instance_atts_string(self):
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        actual = labeler.get_instance_atts_string(dataset[0], " ")
        self.assertEqual("a x v u s", actual)

    def test_get_context_list_with_ignored_attribute(self):
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        labeler.ignore_set = {0}
        label = Label({0, 1}, 4)
        actual = labeler.get_context_list(label, "*")
        self.assertEqual(list("xv**"), actual)

    def test_get_instance_atts_list_with_ignored_attribute(self):
        dataset = test_utils.six_cardinality_data()
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        labeler.ignore_set = {0}
        actual = labeler.get_instance_atts_values_list(dataset[0])
        self.assertEqual(list("xvus"), actual)

    def test_get_context_list_with_alternative_class_index(self):
        dataset = test_utils.six_cardinality_data()
        dataset.set_class_index(2)
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        label = Label({0, 1, 3}, 5)
        actual = labeler.get_context_list(label, "*")
        self.assertEqual(list("a*u**"), actual)

    def test_get_instance_atts_string_with_alternative_class_index(self):
        dataset = test_utils.six_cardinality_data()
        dataset.set_class_index(2)
        labeler = Labeler(dataset[0], False, MissingDataCompare.MATCH)
        actual = labeler.get_instance_atts_values_list(dataset[0])
        self.assertEqual(list("axusr"), actual)

    def test_label_larbe_instance(self):
        data = test_utils.get_dataset(test_utils.SOYBEAN)
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        label = labeler.label(data[1])
        bits = {15, 25, 26, 27, 28, 29, 34}
        self.assertEqual(Label(bits, 35), label)

    def test_partition_large_label(self):
        # 35 features, 7 partitions
        data = test_utils.get_dataset(test_utils.SOYBEAN)
        labeler = Labeler(data[0], False, MissingDataCompare.VARIABLE)
        self.assertEqual(7, labeler.num_partitions())
