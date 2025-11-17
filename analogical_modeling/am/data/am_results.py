"""weka.classifiers.lazy.AM.data
 * **************************************************************************
 * Copyright 2021 Nathan Glenn                                              *
 * Licensed under the Apache License, Version 2.0 (the "License");          *
 * you may not use this file except in compliance with the License.         *
 * You may obtain a copy of the License at                                  *
 *                                                                          *
 * http://www.apache.org/licenses/LICENSE-2.0                               *
 *                                                                          *
 * Unless required by applicable law or agreed to in writing, software      *
 * distributed under the License is distributed on an "AS IS" BASIS,        *
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. *
 * See the License for the specific language governing permissions and      *
 * limitations under the License.                                           *
 ****************************************************************************
"""

from enum import Enum
from os import linesep
from collections import defaultdict

from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.gang_effect import GangEffect
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am import am_utils
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.am.lattice.lattice import Lattice
from analogical_modeling.utils import Instance


class PointerCountingStrategy(Enum):
    """Enum specifying possible counting strategies"""
    LINEAR = 1
    QUADRATIC = 2


class Judgement(Enum):
    """Enum specifying the classification outcome"""
    # Only the correct class was predicted
    CORRECT = "correct"
    # The correct class and others were tied in the prediction
    TIE = "tie"
    # The correct class was not predicted
    INCORRECT = "incorrect"
    # The correct class was not specified in the dataset
    UNKNOWN = "unknown"



class AMResults:
    """The results of running AM containing the analogical effects of the
    individual training instances as well as the relevant supracontexts and
    overall class likelihoods."""
    def __init__(self, lattice: Lattice, sub_list: SubcontextList,
                 test_item: Instance, linear: bool, labeler: Labeler):
        """

        :param lattice: filled lattice, which contains the data for calculating
        the analogical set
        :param sub_list: list of subcontexts
        :param test_item: exemplar being classified
        :param linear: True if counting of pointers should be done linearly;
        False if quadratically.
        :param labeler: The labeler that was used to assign contextual labels;
        this is made available for printing purposes.
        """
        # The exemplar whose class is being predicted by this set
        self.classified_exemplar: Instance = test_item
        self.supra_list: set[Supracontext] = lattice.get_supracontexts()
        self.labeler: Labeler = labeler
        self.sub_list: SubcontextList = sub_list

        if linear:
            self.pointer_counting_strategy = PointerCountingStrategy.LINEAR
        else:
            self.pointer_counting_strategy = PointerCountingStrategy.QUADRATIC

        # find numbers of pointers to individual exemplars
        self.ex_pointer_map: dict[Instance, int] = self.get_pointers(self.supra_list, linear)
        # find the total number of pointers
        self.total_pointers: int = sum(self.ex_pointer_map.values())

        # find the analogical effect of an exemplar by dividing its pointer
        # count by the total pointer count
        self.ex_effect_map: dict[Instance, float] = {
            e: self.ex_pointer_map[e] / self.total_pointers
            for e in self.ex_pointer_map
        }

        # find the likelihood for a given outcome based on the pointers
        self.class_pointer_map: dict[str, int] = defaultdict(int)
        for e in self.ex_pointer_map:
            class_name = e.class_value()
            self.class_pointer_map[class_name] += self.ex_pointer_map[e]

        # set the likelihood of each possible class index to be its share of
        # the total pointers
        self.class_likelihood_map: dict[str, float] = {
            name: self.class_pointer_map[name] / self.total_pointers
            for name in self.class_pointer_map
        }

        # Find the classes with the highest likelihood (there may be a tie)
        self.predicted_classes: set = set()
        self.class_probability = -1
        for cls_name  in self.class_likelihood_map:
            temp = self.class_likelihood_map[cls_name]
            if temp > self.get_class_probability():
                self.class_probability = temp
                self.predicted_classes = {cls_name}
            elif temp == self.get_class_probability():
                self.predicted_classes.add(cls_name)

    @staticmethod
    def get_pointers(supracontexts: set[Supracontext], linear: bool) -> dict[Instance, int]:
        """See page 392 of the red book.

        :param supracontexts: List of Supracontexts created by filling the
        supracontextual lattice.
        :param linear: True if pointer counting should be done linearly; False
        if it should be done quadratically
        :return: A mapping of each exemplar to the number of pointers pointing
        to it.
        """
        pointers: dict[Instance, int] = defaultdict(int)

        # number of pointers in a supracontext,
        # that is the number of exemplars in the whole thing
        pointers_in_list = 0
        # iterate all supracontexts
        for supra in supracontexts:
            if not linear:
                pointers_in_list = 0
                for sub in supra.get_data():
                    pointers_in_list += len(sub.get_exemplars())
            # iterate subcontexts in supracontext
            for sub in supra.get_data():
                # iterate subcontexts in supracontext
                pointers_to_supra = supra.get_count()
                # iterate exemplars in subcontext
                for e in sub.get_exemplars():
                    # pointers to exemplar = pointersToSupra * pointers in list
                    # add together if already in the map
                    if linear:
                        pointer_product = pointers_to_supra
                    else:
                        pointer_product = pointers_in_list * pointers_to_supra
                    pointers[e] += pointer_product
        return pointers

    def __str__(self):
        effects = ""
        for k, v in self.get_exemplar_pointers().items():
            effects += f"{k} : {v} ({v / self.total_pointers}){am_utils.LINE_SEPARATOR}"
        effects += f"Outcome likelihoods:{linesep}"

        sorted_entries = sorted(self.get_class_pointers().items(), key=lambda entry: entry[1])
        # Set<Entry<String, BigInteger>> sortedEntries2 = new TreeSet<>(Entry.comparingByValue());
        # sortedEntries2.addAll(getClassPointers().entrySet());
        for k, v in sorted_entries:
            effects += f"{k} : {v} ({v / self.total_pointers}){am_utils.LINE_SEPARATOR}"

        return f"classifying: {self.get_classified_ex()}{linesep}outcome: " \
               f"{self.predicted_classes} ({self.class_probability}){linesep}" \
               f"Exemplar effects:{am_utils.LINE_SEPARATOR}{effects}"

    def get_exemplar_effect_map(self) -> dict[Instance, float]:
        """

        :return: A mapping between exemplars and their analogical effect
        (decimal percentage)
        """
        return self.ex_effect_map

    def get_exemplar_pointers(self) -> dict[Instance, int]:
        """

        :return: Mapping of exemplars in the analogical set to the number of
        pointers to it
        """
        return self.ex_pointer_map

    def get_total_pointers(self) -> int:
        """

        :return: The total number of pointers in this analogical set
        """
        return self.total_pointers

    def get_class_pointers(self) -> dict[str, int]:
        """

        :return: A mapping between a class value index the number of pointers
        pointing to it
        """
        return self.class_pointer_map

    def get_class_likelihood(self) -> dict[str, float]:
        """

        :return: A mapping between the class name and its selection probability
        """
        return self.class_likelihood_map

    def get_classified_ex(self) -> Instance:
        """

        :return: The exemplar which was classified
        """
        return self.classified_exemplar

    def get_class_probability(self) -> float:
        """

        :return: Probability of the predicted class
        """
        return self.class_probability

    def get_predicted_classes(self) -> set[str]:
        """

        :return: Index of the predicted class attribute value
        """
        return self.predicted_classes

    def get_supra_list(self) -> frozenset[Supracontext]:
        """

        :return: The Supracontexts that comprise the analogical set.
        """
        return frozenset(self.supra_list)

    def get_subcontexts(self) -> set[Subcontext]:
        """

        :return: All subcontexts contained in all of the supracntexts of the
        analogical set.
        """
        return {data for supra in self.get_supra_list() for data in supra.get_data()}

    def get_gang_effects(self) -> list[GangEffect]:
        """

        :return: The gang effects, sorted by size of the effect and then
        alphabetically by the subcontext display label
        """
        effects = [GangEffect(sub, self.get_exemplar_pointers()) for sub in self.get_subcontexts()]
        return sorted(effects, key=lambda e: (-e.total_pointers, e.subcontext.get_display_label()))

    def get_labeler(self) -> Labeler:
        """

        :return: The Labeler object that was used to assign all of the
        contextual labels.
        """
        return self.labeler

    def get_expected_class_name(self) -> str:
        """Return actual class"""
        classified_ex = self.get_classified_ex()
        return classified_ex.class_value()

    def get_sub_list(self) -> SubcontextList:
        """Return the subcontext list"""
        return self.sub_list

    def get_judgement(self):
        """

        :return: a judgement of the prediction
        """
        expected = self.get_expected_class_name()
        if expected is None:
            return Judgement.UNKNOWN
        predicted = self.get_predicted_classes()
        if expected in predicted:
            if len(predicted) == 1:
                return Judgement.CORRECT
            return Judgement.TIE
        return Judgement.INCORRECT

    def get_pointer_counting_strategy(self):
        """Return pointer counting strategy (linear or quadratic)"""
        return self.pointer_counting_strategy
