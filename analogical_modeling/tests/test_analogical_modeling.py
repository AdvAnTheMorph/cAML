# /*
#  * **************************************************************************
#  * Copyright 2021 Nathan Glenn                                              *
#  * Licensed under the Apache License, Version 2.0 (the "License");          *
#  * you may not use this file except in compliance with the License.         *
#  * You may obtain a copy of the License at                                  *
#  *                                                                          *
#  * http://www.apache.org/licenses/LICENSE-2.0                               *
#  *                                                                          *
#  * Unless required by applicable law or agreed to in writing, software      *
#  * distributed under the License is distributed on an "AS IS" BASIS,        *
#  * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. *
#  * See the License for the specific language governing permissions and      *
#  * limitations under the License.                                           *
#  ****************************************************************************/

import unittest

from analogical_modeling.aml import AnalogicalModeling
from analogical_modeling.tests.am import test_utils


class AnalogicalModelingTest(unittest.TestCase):
    @staticmethod
    def get_classifier():
        """Creates a default AnalogicalModeling"""
        am = AnalogicalModeling()
        am.set_remove_test_exemplar(False)
        # Ensure Johnsen-Johansson lattice runs deterministically
        am.set_random_provider(test_utils.get_deterministic_random_provider())
        return am

    def test_chapter_3_data(self):
        train = test_utils.get_dataset(test_utils.CHAPTER_3_DATA)
        test = train[0]
        am = self.get_classifier()
        # test that this method removes the exemplar
        am.set_remove_test_exemplar(True)
        am.build_classifier(train)

        prediction = am.distribution_for_instance(test)
        for k, v in {"r": 0.6923077, "e": 0.3076923}.items():
            self.assertAlmostEqual(v, prediction[k], delta=1e-7)

        self.assertEqual({"r": 9, "e": 4}, am.get_results().get_class_pointers())

    def test_finnverb(self):
        """
        Test accuracy with the finnverb dataset, a real data set with 10 features
        and lots of unknowns. First check the class pointers on one
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
            self.assertAlmostEqual(v, prediction.get(k, 0), delta=1e-7)  # doesn't return 0 probabilities, and I don't know why it should
        self.assertEqual({"A": 5094, "C": 50}, am.get_results().get_class_pointers())

        train.add(test)
        num_correct = test_utils.leave_one_out(self.get_classifier(), train)
        self.assertEqual(160, num_correct)

    def test_soybean(self):
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
            self.assertAlmostEqual(v, prediction.get(k, 0), delta=1e-7, msg=(k,v))

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
        # forces use of JohnsenJohanssonLattice
        train = test_utils.get_dataset(test_utils.AUDIOLOGY)
        num_correct = test_utils.leave_one_out(self.get_classifier(), train)
        self.assertTrue(num_correct >= 155)

    def test_get_options(self):
        am = AnalogicalModeling()
        self.assertEqual("Linear: False, Remove test exemplars: True, Ignore unknown values: False, Missing data: variable\nDrop duplicates: False, Ignore columns: --", am.get_options())

        am.set_remove_test_exemplar(False)
        am.set_missing_data_compare("mismatch")
        am.set_ignore_unknowns(True)
        self.assertEqual("Linear: False, Remove test exemplars: False, Ignore unknown values: True, Missing data: mismatch\nDrop duplicates: False, Ignore columns: --", am.get_options())

    def test_weights_linear(self):
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
