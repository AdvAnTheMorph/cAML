"""weka.classifiers.lazy.AM.data"""


import unittest

from analogical_modeling.am.data.gang_effect import GangEffect
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.tests.am.test_utils import six_cardinality_data


class GangEffectTest(unittest.TestCase):
    def test_constructor(self):
        dataset = six_cardinality_data()
        sub = Subcontext(Label({0, 2}, 4), "foo")
        for i in range(6):
            sub.add(dataset[i])
        effect = GangEffect(sub, {dataset[0]: 1, dataset[1]: 2, dataset[2]: 3, dataset[3]: 4, dataset[4]: 5, dataset[5]: 6})

        self.assertEqual(sub, effect.subcontext)  # effect.get_subcontext()
        self.assertEqual({"e": {dataset[1], dataset[3], dataset[5]}, "r": {dataset[0], dataset[2], dataset[4]}}, effect.class_to_instances)
        self.assertEqual({"e": 12, "r": 9}, effect.class_to_pointers)
        self.assertEqual(21, effect.total_pointers)
