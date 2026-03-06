"""Integration tests for analogical modeling."""

import math
import unittest
import warnings

import pandas as pd

from analogical_modeling.aml import AnalogicalModeling, HeaderMismatchError
from analogical_modeling.tests.am import test_utils
from analogical_modeling.utils import Dataset, InvalidColumnError, \
    EmptyLexiconError, TooFewAttributesError


class AnalogicalModelingTest(unittest.TestCase):

    def setUp(self) -> None:
        """Reset handling of warnings to `error`."""
        warnings.filterwarnings("error", module="analogical_modeling*")

    @staticmethod
    def get_classifier() -> AnalogicalModeling:
        """Creates a default AnalogicalModeling."""
        am = AnalogicalModeling()
        am.set_remove_test_exemplar(False)
        # Ensure Johnsen-Johansson lattice runs deterministically
        am.set_random_provider(test_utils.get_deterministic_random_provider())
        return am

    @staticmethod
    def get_data() -> pd.DataFrame:
        """Get dummy dataset."""
        return pd.DataFrame({'attr1': [3, 3, 2, 3],
                             'attr2': [1, 1, 1, 1],
                             'ignore': ['s', 't', 'r', 'i'],
                             'w_neg': [-0.4, 0.1, 0.19, 0.106],
                             'w': [0.4, 0.1, 0.19, 0.106],
                             'class': ['r', 'r', 'e', 'r']})

    def test_chapter_3_data(self):
        """Test data from Chapter 3."""
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        test = train[0]
        am = self.get_classifier()
        # test that this method removes the exemplar
        am.set_remove_test_exemplar(True)
        am.build_classifier(train)

        prediction = am.distribution_for_instance(test)
        for k, v in {"r": 0.6923077, "e": 0.3076923}.items():
            self.assertAlmostEqual(v, prediction[k], delta=1e-7)

        self.assertEqual({"r": 9, "e": 4},
                         am.get_results().get_class_pointers())

    def test_finnverb(self):
        """
        Test accuracy with the finnverb dataset, a real data set with 10
        features and lots of unknowns. First check the class pointers on one
        classification, then do a leave-one-out classification for the whole set
        and verify the accuracy.
        """
        train = test_utils.get_dataset(test_utils.FINNVERB)
        test = train[15]
        train.data.drop(index=15, inplace=True)
        am = self.get_classifier()
        am.build_classifier(train)

        prediction = am.distribution_for_instance(test)
        for k, v in {"B": 0.0, "A": 0.9902799, "C": 0.0097201}.items():
            # doesn't return 0 probabilities, and I don't know why it should
            self.assertAlmostEqual(v, prediction.get(k, 0),
                                   delta=1e-7)
        self.assertEqual({"A": 5094, "C": 50},
                         am.get_results().get_class_pointers())

        train.add(test)
        num_correct = test_utils.leave_one_out(self.get_classifier(), train)
        self.assertEqual(160, num_correct)

    def test_soybean(self):
        """Test larger dataset."""
        train = test_utils.get_dataset(test_utils.SOYBEAN)
        test = train[15]
        train.data.drop(index=15, inplace=True)
        am = self.get_classifier()
        am.build_classifier(train)

        prediction = am.distribution_for_instance(test)
        expected = {"diaporthe-stem-canker": 0.0000296,
                    "charcoal-rot": 0.9969953,
                    "rhizoctonia-root-rot": 0.0,
                    "phytophthora-rot": 0.000006,
                    "brown-stem-rot": 0.0028873,
                    "powdery-mildew": 0.0000351,
                    "downy-mildew": 0.0000001,
                    "brown-spot": 0.0000063,
                    "bacterial-blight": 0.0000085,
                    "bacterial-pustule": 0.0,
                    "purple-seed-stain": 0.0000043,
                    "anthracnose": 0.0000158,
                    "phyllosticta-leaf-spot": 0.0000000,
                    "alternarialeaf-spot": 0.0000089,
                    "frog-eye-leaf-spot": 0.0000026,
                    "diaporthe-pod-&-stem-blight": 0.0,
                    "cyst-nematode": 0.0,
                    "herbicide-injury": 0.0,
                    "2-4-d-injury": 0.0}
        for k, v in expected.items():
            self.assertAlmostEqual(v, prediction.get(k, 0), delta=1e-7,
                                   msg=(k, v))

        expected = {"anthracnose": 5358272,
                    "bacterial-blight": 2880000,
                    "alternarialeaf-spot": 3016836,
                    "powdery-mildew": 11869024,
                    "downy-mildew": 50688,
                    "charcoal-rot": 337300810464,
                    "frog-eye-leaf-spot": 890880,
                    "phytophthora-rot": 2028992,
                    "brown-spot": 2134080,
                    "diaporthe-pod-&-stem-blight": 140,
                    "purple-seed-stain": 1463456,
                    "diaporthe-stem-canker": 10013312,
                    "brown-stem-rot": 976826156}
        self.assertEqual(expected, am.get_results().get_class_pointers())

    def test_audiology(self):
        """Test classification with JohnsenJohanssonLattice."""
        train = test_utils.get_dataset(test_utils.AUDIOLOGY)
        num_correct = test_utils.leave_one_out(self.get_classifier(), train)
        self.assertTrue(num_correct >= 155)

    def test_get_options(self):
        """Test correct creation of options string."""
        am = AnalogicalModeling()
        self.assertEqual(
            "Linear: False, Remove test exemplars: True, Ignore unknown "
            "values: False, Non-specified data: variable\nDrop duplicates: False, "
            "Ignore columns: --",
            am.get_options())

        am.set_remove_test_exemplar(False)
        am.set_nonspecified_data_compare("mismatch")
        am.set_ignore_unknowns(True)
        self.assertEqual(
            "Linear: False, Remove test exemplars: False, Ignore unknown "
            "values: True, Non-specified data: mismatch\nDrop duplicates: False, "
            "Ignore columns: --",
            am.get_options())

    def test_weights_linear(self):
        """Test linear weights calculation."""
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA_W, "w")
        test = train[0]
        train.data.drop(index=0, inplace=True)

        am = self.get_classifier()
        am.build_classifier(train)
        am.set_linear_count(True)

        distr = am.distribution_for_instance(test)
        for k, v in {"e": 0.401606426, "r": 0.598393574}.items():
            self.assertAlmostEqual(v, distr.get(k, 0), delta=1e-7)

        prediction = am.get_results().get_class_pointers()
        # without weights: {"e": 2, "r": 5}
        for k, v in {"e": 0.4, "r": 0.596}.items():
            self.assertAlmostEqual(v, prediction.get(k, 0), delta=1e-7)

    def test_weights_quadratic(self):
        """Test quadratic weights calculation."""
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA_W, "w")
        test = train[0]
        train.data.drop(index=0, inplace=True)

        am = self.get_classifier()
        am.build_classifier(train)
        am.set_linear_count(False)

        distr = am.distribution_for_instance(test)
        for k, v in {"e": 0.443951165, "r": 0.556048835}.items():
            self.assertAlmostEqual(v, distr.get(k, 0), delta=1e-7)
        prediction = am.get_results().get_class_pointers()

        for k, v in {"e": 0.8, "r": 1.002}.items():
            self.assertAlmostEqual(v, prediction.get(k, 0), delta=1e-7)

    def test_weights(self):
        """Test assignment of weights column.

        - correct extraction of weights
        - weights are dropped from data
        - weights must be numeric and non-negative
        """
        data = self.get_data()

        self.assertEqual(Dataset(data).weights, [1] * 4)
        # should work
        self.assertEqual(Dataset(data, "w").weights, [0.4, 0.1, 0.19, 0.106])
        self.assertEqual(Dataset(data, "w").data.shape, (4, 5))

        # shouldn't work
        with self.assertRaises(InvalidColumnError):  # negative
            Dataset(data, weights="w_neg")
        with self.assertRaises(InvalidColumnError):  # not numeric
            Dataset(data, weights="ignore")

    def test_empty_data(self):
        """Test handling of empty datasets.

        - at least 1 instance
        - at least 1 attribute besides class
        - correct handling of empty cells (NaN -> None)
        - distinction between empty cells and non-specified values
        """
        am = self.get_classifier()
        data = pd.DataFrame(columns=["attr1", "attr2"])

        with self.assertRaises(UserWarning) as ex:  # no instances
            am.run_classifier(data, None, None, "")
        self.assertEqual(ex.exception.args[0],
                         "The lexicon does not contain any Instances.")

        data = pd.DataFrame({"col": ["attr1", "attr2"]})
        with self.assertRaises(UserWarning) as ex:  # not enough attributes
            am.run_classifier(data, None, None, "")
        self.assertEqual(ex.exception.args[0],
                         "There should be at least 1 attribute beside the class.")

        data = pd.DataFrame({"attr1": ["a", math.nan], "attr2": [None, "="]})
        self.assertIsNotNone(Dataset(data))  # don't raise Errors
        data = Dataset(data)
        self.assertFalse(data[0].is_unspecified(1), "None != non-specified")  # math.nan
        self.assertFalse(data[1].is_unspecified(0), "None != non-specified")  # None
        self.assertTrue(data[1].is_unspecified(1), "= == non-specified")  # =

    def test_headers(self):
        """Test header comparison.

        - same attributes in same order
        - class column can be anywhere
        - ignored columns can be anywhere
        """
        am = self.get_classifier()
        lex = pd.DataFrame(
            {"attr1": ["a", "b"], "attr2": ["c", "d"], "cls": ["e", "f"]})
        test = pd.DataFrame({"attr1": ["a"], "attr3": ["d"], "cls": ["e"]})

        # names relevant
        with self.assertRaises(HeaderMismatchError):
            am.run_classifier(lex, None, test, "")
        # order relevant
        test = pd.DataFrame({"attr2": ["a"], "attr1": ["d"], "cls": ["e"]})
        with self.assertRaises(HeaderMismatchError):
            am.run_classifier(lex, None, test, "")

        # cls optional
        test = pd.DataFrame({"attr1": ["a"], "attr2": ["d"]})
        self.assertTrue(am.run_classifier(lex, None, test, ""))
        # cls location irrelevant
        test = pd.DataFrame({"attr1": ["a"], "cls": ["e"], "attr2": ["d"]})
        self.assertTrue(am.run_classifier(lex, None, test, ""))

        # ignored columns irrelevant
        warnings.resetwarnings()  # ignore warning due to short test instance
        am.ignore_columns = ["attr2"]
        test = pd.DataFrame({"attr1": ["a"]})
        self.assertTrue(am.run_classifier(lex, None, test, ""))


    def test_lower_threshold(self):
        """Test lower threshold.

        - no impact if lower than min weight
        - error if higher than max weight (dropping all instances)
        - no dropping of instances if this would result in an error
        - inclusivity/exclusivity
        - no impact if not specified
        """
        lex = Dataset(self.get_data(), weights="w")

        instances = list(lex)
        weights = lex.weights
        self.assertEqual(len(instances), 4)

        # no threshold - no change
        lex.filter_threshold(None, inclusive=True)
        self.assertEqual(len(list(lex)), 4)
        self.assertEqual(lex.weights, weights)

        # inclusive: drop all instances -> Exception
        with self.assertRaises(EmptyLexiconError):
            lex.filter_threshold(0.4, inclusive=True)
        # threshold above max weight -> Exception
        with self.assertRaises(EmptyLexiconError):
            lex.filter_threshold(100, inclusive=False)
        # Exceptions raised -> no impact
        self.assertEqual(list(lex), instances, "No change in case of Exception")
        self.assertEqual(lex.weights, weights)

        # negative threshold -> no impact
        lex.filter_threshold(-0.4, inclusive=True)
        self.assertEqual(len(list(lex)), 4)
        self.assertEqual(list(lex), instances)
        self.assertEqual(lex.weights, weights)

        # exclusive threshold below any weight value
        lex.filter_threshold(0.1, inclusive=False)
        self.assertEqual(len(list(lex)), 4)
        self.assertEqual(list(lex), instances)
        self.assertEqual(lex.weights, weights)

        # inclusive: drop instance 1
        lex.filter_threshold(0.1, inclusive=True)
        self.assertEqual(len(list(lex)), 3)
        self.assertEqual(list(lex), instances[:1] + instances[2:])
        self.assertEqual(lex.weights, weights[:1] + weights[2:])

        # exclusive: drop all but instance 0
        lex.filter_threshold(0.4, inclusive=False)
        self.assertEqual(len(list(lex)), 1)
        self.assertEqual(list(lex), instances[:1])
        self.assertEqual(lex.weights, weights[:1])


    def test_upper_threshold(self):
        """Test upper threshold.

        - no impact if higher than max weight
        - error if lower than min weight (dropping all instances)
        - no dropping of instances if this would result in an error
        - inclusivity/exclusivity
        - no impact if not specified
        """
        lex = Dataset(self.get_data(), weights="w")

        instances = list(lex)
        weights = lex.weights
        self.assertEqual(len(instances), 4)

        # no threshold - no change
        lex.filter_threshold(None, inclusive=True, upper=True)
        self.assertEqual(len(list(lex)), 4)
        self.assertEqual(lex.weights, weights)

        # inclusive: drop all instances -> Exception
        with self.assertRaises(EmptyLexiconError):
            lex.filter_threshold(0.1, inclusive=True, upper=True)
        # threshold above max weight -> Exception
        with self.assertRaises(EmptyLexiconError):
            lex.filter_threshold(-1, inclusive=False, upper=True)
        # Exceptions raised -> no impact
        self.assertEqual(list(lex), instances, "No change in case of Exception")
        self.assertEqual(lex.weights, weights)

        # exclusive threshold above any weight value
        lex.filter_threshold(100, inclusive=False, upper=True)
        self.assertEqual(len(list(lex)), 4)
        self.assertEqual(list(lex), instances)
        self.assertEqual(lex.weights, weights)

        # inclusive: drop instance 0
        lex.filter_threshold(0.4, inclusive=True, upper=True)
        self.assertEqual(len(list(lex)), 3)
        self.assertEqual(list(lex), instances[1:])
        self.assertEqual(lex.weights, weights[1:])

        # exclusive: drop all but instance 1
        lex.filter_threshold(0.1, inclusive=False, upper=True)
        self.assertEqual(len(list(lex)), 1)
        self.assertEqual(list(lex), instances[1:2])
        self.assertEqual(lex.weights, [weights[1]])

    def test_threshold_and_weights(self):
        """Test correct interworking of threshold and weights.

        - accept 0 weights if filtered out by threshold
        - don't accept 0 weights otherwise
        """

        # no error, since weights filtered out
        lex = Dataset(self.get_data(), weights="w_neg", threshold=(0, True))
        instances = list(lex)
        weights = lex.weights
        self.assertEqual(len(instances), 3)
        self.assertGreater(min(weights), 0)

        # error, since negative weights not filtered out
        with self.assertRaises(InvalidColumnError):
            Dataset(self.get_data(), weights="w_neg", threshold=(None, True))

        print(weights)
        # TODO: more tests

    def test_ignore(self):
        """Test ignoring of columns.

        - impact on counted attributes
        - class can't be ignored
        - weights can't be ignored
        - at least 1 attribute besides class must remain
        - same column can be ignored multiple times
        - ignored columns required to be in data unless silent == True
        """
        data = Dataset(self.get_data())

        total = data.num_attributes()
        self.assertEqual(data.num_attributes(), data.num_counted_attributes())

        # now one counted attribute less
        data.set_ignored(["ignore"])
        self.assertEqual(data.num_attributes(), total)
        self.assertEqual(data.num_counted_attributes(), total - 1)
        self.assertEqual(list(data[0].keys()),
                         ["attr1", "attr2", "w_neg", "w", "class"])

        # multiple ignored columns
        data.set_ignored(["ignore", "w"])
        self.assertEqual(data.num_attributes(), total)
        self.assertEqual(data.num_counted_attributes(), total - 2)
        self.assertEqual(list(data[0].keys()),
                         ["attr1", "attr2", "w_neg", "class"])

        # class can't be ignored
        with self.assertRaises(InvalidColumnError):
            data.set_ignored(["class"])

        # weights can't be ignored (dropped from dataa)
        with self.assertRaises(InvalidColumnError):
            Dataset(self.get_data(), weights="w").set_ignored(["w"])

        # possible to ignore same column multiple times
        data.set_ignored(["ignore", "ignore"])
        self.assertEqual(data.num_attributes(), total)
        self.assertEqual(data.num_counted_attributes(), total - 1)
        self.assertEqual(list(data[0].keys()),
                         ["attr1", "attr2", "w_neg", "w", "class"])

        # recover
        data.set_ignored([])
        self.assertEqual(data.num_attributes(), total)
        self.assertEqual(data.num_counted_attributes(), total)

        # required to be in data
        with self.assertRaises(InvalidColumnError):
            data.set_ignored(["not_in_data"])

        # ignore if silent == True
        data.set_ignored(["not_in_data"], silent=True)
        self.assertEqual(data.num_attributes(), total)
        self.assertEqual(data.num_counted_attributes(), total)

        # impossible to ignore all columns
        with self.assertRaises(TooFewAttributesError):
            data.set_ignored(["attr1", "attr2", "w_neg", "w", "ignore"])
