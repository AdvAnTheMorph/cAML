"""Separate test for Heterogeneous Lattice"""

import unittest
from unittest import mock

from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.am.label.missing_data_compare import MissingDataCompare
from analogical_modeling.am.lattice.heterogeneous_lattice import \
    HeterogeneousLattice
from analogical_modeling.tests.am import test_utils


class HeterogeneousLatticeTest(unittest.TestCase):
    """Test the HeterogeneousLattice, which does not remove heterogeneous
       supracontexts and therefore cannot be tested with the other Lattice
       implementations in LatticeTest.
    """

    def test_chapter_3_data(self):
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        test = train[0]
        train.data.drop(0, inplace=True)
        # Define a labeler which doesn't partition labels so that we can just
        # test with the chapter 3 data without it being reduced to a
        # cardinality of one
        no_partition_labeler = Labeler(test, False, MissingDataCompare.MATCH)
        no_partition_labeler = mock.Mock(wraps=no_partition_labeler)
        no_partition_labeler.num_partitions.return_value = 1

        sub_list = SubcontextList(no_partition_labeler, train, False)
        hetero_lattice = HeterogeneousLattice(0)
        hetero_lattice.fill(sub_list)

        actual_supras = hetero_lattice.get_supracontexts()
        expected_supras = ["[2x(001|&nondeterministic&|3,1,0,e/3,1,1,r)]",
                           "[1x(100|r|2,1,2,r)]",
                           "[1x(001|&nondeterministic&|3,1,0,e/3,1,1,r),(100|r|2,1,2,r),(101|r|2,1,0,r)]",
                           "[1x(110|r|0,3,2,r),(100|r|2,1,2,r)]",
                           "[1x(001|&nondeterministic&|3,1,0,e/3,1,1,r),(110|r|0,3,2,r),(100|r|2,1,2,r),(101|r|2,1,0,r)]"]
        self.assertEqual(len(expected_supras), len(actual_supras))
        for expected in expected_supras:
            supra = test_utils.get_supra_from_string(expected, train)
            self.assertTrue(test_utils.contains_supra(actual_supras, supra))
