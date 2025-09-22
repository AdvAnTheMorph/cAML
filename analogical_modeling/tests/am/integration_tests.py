"""weka.classifiers.lazy.AM"""

import unittest

from analogical_modeling.analogical_modeling import AnalogicalModeling
from analogical_modeling.tests.am import test_utils


class IntegrationTests(unittest.TestCase):
    def test_spanish_stress(self):
        # This dataset has published results with AM, so we ensure our accuracy matches the publication
        # It's a long test, though, so only run it during integration tests
        #Assume.assumeTrue(TestUtils.RUN_INTEGRATION_TESTS);

        train = test_utils.get_dataset(test_utils.SPANISH_STRESS)
        am = AnalogicalModeling()
        # Ensure Johnsen-Johansson lattice runs deterministically
        am.set_random_provider(test_utils.get_deterministic_random_provider())

        num_correct = test_utils.leave_one_out(am, train)
        self.assertEqual(4727, num_correct)
