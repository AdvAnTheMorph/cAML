"""Integration test for Analogical Modeling."""

import sys
import unittest

from analogical_modeling.aml import AnalogicalModeling
from analogical_modeling.tests.am import test_utils


@unittest.skipUnless("run_integration_tests" in sys.argv,
                     "Run only during integration tests")
class IntegrationTests(unittest.TestCase):
    def test_spanish_stress(self):
        """Compare AML accuracy on spanish_stress with publication.

        Long test, so only run it during integration tests.
        """

        train = test_utils.get_dataset(test_utils.SPANISH_STRESS)
        am = AnalogicalModeling()
        # Ensure Johnsen-Johansson lattice runs deterministically
        am.set_random_provider(test_utils.get_deterministic_random_provider())

        num_correct = test_utils.leave_one_out(am, train)
        self.assertEqual(4727, num_correct)
