"""Test Lattices"""

import unittest
from unittest.mock import Mock

import analogical_modeling.tests.am.test_utils as test_utils
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.am.label.missing_data_compare import MissingDataCompare
from analogical_modeling.am.lattice.basic_lattice import BasicLattice
from analogical_modeling.am.lattice.distributed_lattice import \
    DistributedLattice
from analogical_modeling.am.lattice.heterogeneous_lattice import \
    HeterogeneousLattice
from analogical_modeling.am.lattice.johnsen_johansson_lattice import \
    JohnsenJohanssonLattice
from analogical_modeling.utils import Dataset, Instance

lattices = [BasicLattice, DistributedLattice,
            lambda: JohnsenJohanssonLattice(
                test_utils.get_deterministic_random_provider()),
            lambda: HeterogeneousLattice(0)]


class FullSplitLabeler(Labeler):
    """Create a labeler which splits labels into labels of cardinality 1."""

    def __init__(self, test: Instance, ignore_unknowns: bool,
                 mdc: MissingDataCompare):
        super().__init__(test, ignore_unknowns, mdc)
        self.wrapped = Labeler(test, False, MissingDataCompare.VARIABLE)

    def label(self, data):
        return self.wrapped.label(data)

    def partition(self, label: Label, partition_index: int):
        label_bit = set() if label.matches(partition_index) else {0}
        return Label(label_bit, 1)

    def num_partitions(self) -> int:
        return self.get_cardinality()

    def get_lattice_top(self) -> Label:
        return self.wrapped.get_lattice_top()

    def get_lattice_bottom(self) -> Label:
        return self.wrapped.get_lattice_bottom()

    def from_bits(self, _label_bits: int) -> None:
        return None


class LatticeTest(unittest.TestCase):
    """Test the lattices that can be used for item classification. These are
       implementations of the Lattice interface"""

    @staticmethod
    def get_full_split_labeler(test) -> Labeler:
        """create a labeler which splits labels into labels of cardinality 1"""
        return FullSplitLabeler(test, False, MissingDataCompare.VARIABLE)

    def do_test_supras(self, train: Dataset, test_index: int,
                       expected_supras: list[str], lattice_supplier):
        """Test that the given test/train combination yields the given list
        of supracontexts.

        :param train: Dataset to train with
        :param test_index: Index of item in dataset to remove and use as a
            test item
        :param expected_supras: String representations of the supracontexts that
            should be created from the train/test combo
        """
        test = train[test_index]
        train.data.drop(index=test_index, inplace=True)

        sub_list = SubcontextList(self.get_full_split_labeler(test), train,
                                  False)
        test_lattice = lattice_supplier()
        test_lattice.fill(sub_list)
        actual_supras = test_lattice.get_supracontexts()  # filled with empty supras

        self.assertEqual(len(expected_supras), len(actual_supras),
                         f"{lattice_supplier}: {actual_supras} != {expected_supras}")
        for expected in expected_supras:
            supra = test_utils.get_supra_from_string(expected, train)
            self.assertTrue(test_utils.contains_supra(actual_supras,
                                                      supra))  # fails because self.label != other.label

    def test_filling_with_empty_subcontext_list(self):
        for lattice_supplier in lattices:
            lattice = lattice_supplier()
            lattice.fill(SubcontextList(Mock(spec=Labeler), Dataset([]), False))

    def test_lattice_cannot_be_filled_twice(self):
        for lattice_supplier in lattices:
            lattice = lattice_supplier()
            lattice.fill(SubcontextList(Mock(spec=Labeler), Dataset([]), False))

            with self.assertRaises(ValueError):
                lattice.fill(
                    SubcontextList(Mock(spec=Labeler), Dataset([]), False))

    def test_chapter3_data(self):
        expected_supras = ["[2x(001|&nondeterministic&|3,1,0,e/3,1,1,r)]",
                           "[1x(100|r|2,1,2,r)]",
                           "[1x(100|r|2,1,2,r),(110|r|0,3,2,r)]"]

        for lattice_supplier in lattices:
            if isinstance(lattice_supplier(),
                          (HeterogeneousLattice, JohnsenJohanssonLattice)):
                # HeterogeneousLattice not designed for prediction
                # JohnsenJohanssonLattice inaccurate for small datasets
                continue
            train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
            self.do_test_supras(train, 0, expected_supras, lattice_supplier)

    def test_heterogeneous_marking(self):
        """Test that supracontexts are properly marked heterogeneous."""
        expected_supras = [
            "[1x(01010|&nondeterministic&|H,A,V,I,0,A/H,A,V,A,0,B)]",
            "[2x(10000|A|K,U,V,U,0,A)]",
            "[2x(00011|C|H,U,V,O,S,C)]",
            "[1x(10010|A|U,U,V,I,0,A),(10000|A|K,U,V,U,0,A)]",
            "[1x(10010|A|U,U,V,I,0,A),(10110|A|P,U,0,?,0,A),(10000|A|K,U,V,U,0,A)]"]

        for lattice_supplier in lattices:
            if isinstance(lattice_supplier(),
                          (HeterogeneousLattice, JohnsenJohanssonLattice)):
                # HeterogeneousLattice not designed for prediction
                # JohnsenJohanssonLattice inaccurate for small datasets
                continue
            train = test_utils.get_reduced_dataset(test_utils.FINNVERB_MIN,
                                                   [5, 6, 7, 8, 9])
            self.do_test_supras(train, 0, expected_supras, lattice_supplier)

    def test_clean_supra_timing(self):
        """Test that :fun:`BasicLattice.clean_supra` is only run after a
        subcontext is inserted completely, not after each single insertion."""
        expected_supras = ["[6x(00000|A|U,V,U,0,?,A)]",
                           "[3x(00000|A|U,V,U,0,?,A),(00100|A|U,V,I,0,?,A)]",
                           "[3x(00000|A|U,V,U,0,?,A),(01100|A|U,0,?,0,?,A),(00100|A|U,V,I,0,?,A)]"]

        for lattice_supplier in lattices:
            if isinstance(lattice_supplier(),
                          (HeterogeneousLattice, JohnsenJohanssonLattice)):
                # HeterogeneousLattice not designed for prediction
                # JohnsenJohanssonLattice inaccurate for small datasets
                continue
            train = test_utils.get_reduced_dataset(test_utils.FINNVERB_MIN,
                                                   [0, 6, 7, 8, 9])
            self.do_test_supras(train, 0, expected_supras, lattice_supplier)
