"""weka.classifiers.lazy.AM.data"""

import unittest
from importlib.metadata import distribution

from analogical_modeling.analogical_modeling import AnalogicalModeling
from analogical_modeling.tests.am import test_utils


class AMResultsTest(unittest.TestCase):
    """Test the data contained in AMResults after classifying the chapter 3 data."""
    def setUp(self):
        self.train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        self.test = self.train[0]
        self.train.data.drop(index=0, inplace=True)

        self.am = AnalogicalModeling()
        self.am.build_classifier(self.train)
        self.am.distribution_for_instance(self.test)

        self.as_quadratic = self.am.get_results()
        self.am.set_linear_count(True)
        self.am.distribution_for_instance(self.test)
        self.as_linear = self.am.get_results()

    def test_exemplar_quadratic_effects(self):
        effects = {str(k): v for k, v in self.as_quadratic.get_exemplar_effect_map().items()}
        self.assertEqual(4, len(effects))

        self.assertIn("3,1,0,e", effects)
        self.assertAlmostEqual(0.3076923, effects["3,1,0,e"], delta=1e-7)
        self.assertIn("0,3,2,r", effects)
        self.assertAlmostEqual(0.1538462, effects["0,3,2,r"], delta=1e-7)
        self.assertIn("2,1,2,r", effects)
        self.assertAlmostEqual(0.2307692, effects["2,1,2,r"], delta=1e-7)
        self.assertIn("3,1,1,r", effects)
        self.assertAlmostEqual(0.3076923, effects["3,1,1,r"], delta=1e-7)

    def test_exemplar_linear_effects(self):
        effects = {str(k): v for k, v in self.as_linear.get_exemplar_effect_map().items()}
        self.assertEqual(4, len(effects))

        self.assertIn("3,1,0,e", effects)
        self.assertAlmostEqual(0.2857143, effects["3,1,0,e"], delta=1e-7)
        self.assertIn("0,3,2,r", effects)
        self.assertAlmostEqual(0.1428571, effects["0,3,2,r"], delta=1e-7)
        self.assertIn("2,1,2,r", effects)
        self.assertAlmostEqual(0.2857143, effects["2,1,2,r"], delta=1e-7)
        self.assertIn("3,1,1,r", effects)
        self.assertAlmostEqual(0.2857143, effects["3,1,1,r"], delta=1e-7)

    def test_quadratic_pointers(self):
        self.assertEqual(13, self.as_quadratic.get_total_pointers())
        self.assertEqual({"r": 9, "e": 4}, self.as_quadratic.get_class_pointers())

        pointers = {str(k): v for k, v in self.as_quadratic.get_exemplar_pointers().items()}
        self.assertEqual(4, len(pointers))

        self.assertIn("3,1,0,e", pointers)
        self.assertEqual(4, pointers["3,1,0,e"])
        self.assertIn("0,3,2,r", pointers)
        self.assertEqual(2, pointers["0,3,2,r"])
        self.assertIn("2,1,2,r", pointers)
        self.assertEqual(3, pointers["2,1,2,r"])
        self.assertIn("3,1,1,r", pointers)
        self.assertEqual(4, pointers["3,1,1,r"])

    def test_linear_pointers(self):
        self.assertEqual(7, self.as_linear.get_total_pointers())
        self.assertEqual({"r": 5, "e": 2}, self.as_linear.get_class_pointers())

        pointers = {str(k): v for k, v in self.as_linear.get_exemplar_pointers().items()}
        self.assertEqual(4, len(pointers))

        self.assertIn("3,1,0,e", pointers)
        self.assertEqual(2, pointers["3,1,0,e"])
        self.assertIn("0,3,2,r", pointers)
        self.assertEqual(1, pointers["0,3,2,r"])
        self.assertIn("2,1,2,r", pointers)
        self.assertEqual(2, pointers["2,1,2,r"])
        self.assertIn("3,1,1,r", pointers)
        self.assertEqual(2, pointers["3,1,1,r"])

    def test_quadratic_class_distribution(self):
        distr = self.as_quadratic.get_class_likelihood()
        self.assertEqual(2, len(distr))

        # test to 10 decimal places, the number used by AMUtils.mathContext
        self.assertAlmostEqual(0.6923077, distr["r"], delta=1e-7)
        self.assertAlmostEqual(0.3076923, distr["e"], delta=1e-7)

        self.assertEqual({"r"}, self.as_quadratic.get_predicted_classes())
        self.assertAlmostEqual(0.6923077, self.as_quadratic.get_class_probability(), delta=1e-7)

    def test_linear_class_distribution(self):
        distr = self.as_linear.get_class_likelihood()
        self.assertEqual(2, len(distr))

        # test to 10 decimal places, the number used by AMUtils.mathContext
        self.assertAlmostEqual(0.7142857, distr["r"], delta=1e-7)
        self.assertAlmostEqual(0.2857143, distr["e"], delta=1e-7)

        self.assertEqual({"r"}, self.as_linear.get_predicted_classes())
        self.assertAlmostEqual(0.7142857, self.as_linear.get_class_probability(), delta=1e-7)

    def test_classified_ex(self):
        self.assertEqual(self.test, self.as_quadratic.get_classified_ex())

    # TODO: test with linear counting
    # TODO: test toString

    def test_get_gang_effects(self):
        effects = self.as_quadratic.get_gang_effects()
        self.assertEqual(["3 1 *", "* 1 2", "* * 2"], [e.subcontext.get_display_label() for e in effects])
