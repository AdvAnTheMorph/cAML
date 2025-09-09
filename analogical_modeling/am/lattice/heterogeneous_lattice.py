"""weka.classifiers.lazy.AM.lattice
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

from analogical_modeling.am.lattice.lattice import Lattice
from analogical_modeling.am.lattice.linked_lattice_node import LinkedLatticeNode
from analogical_modeling.am.data.basic_supra import BasicSupra
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.label.labeler import Labeler


class HeterogeneousLattice(Lattice):
    """
     * Same as a normal lattice, except no supracontext is deemed heterogeneous and
     * hence everything is kept.
     *
     * Represents a lattice which is to be combined with other sublattices to
     * determine predictions later on. When a sublattice is filled, there are two
     * main differences:
     * <ol>
     * <li>Only a part of a an exemplar's features are used to assign lattice
     * locations.</li>
     * <li>No supracontext is ever determined to be heterogeneous. This is, of
     * course, less efficient in some ways.</li>
     * </ol>
     * Inefficiencies brought about by not eliminating heterogeneous supracontexts
     * and by having to combine sublattices are a compromise to the alternative,
     * using a single lattice for any size exemplars. Remember that the underlying
     * structure of a lattice is an array of size 2^n, n being the size of the
     * exemplars contained. So if the exemplars are 20 features long, a single
     * lattice would be 2^20 or 1M elements long. On the other hand, if the
     * exemplars are split in 4, then 4 sublattices of size 2^5, or 32, can be used
     * instead, making for close to 100,000 times less memory used.
     * <p>
     * In terms of processing power, more is required to use sublattices. However,
     * using threads the processing of each can be done in parallel.
     *
     * @author Nate Glenn
     * @author Nathan Glenn
    """
    def __init__(self, partition_index: int):
        """
        Initializes Supracontextual lattice to a 2^n length array of
        Supracontexts, as well as the empty and the heterogeneous supracontexts.

        :param partition_index: which label partition to use in assigning subcontexts to supracontexts
        """
        self.partition_index: int = partition_index
        # Lattice is a 2^n array of Supracontexts
        self.lattice: dict[Label, LinkedLatticeNode[BasicSupra]] = {}
        # the current number of the subcontext being added
        self.index: int = -1
        # All points in the lattice point to the empty supracontext by default.
        self.empty_supracontext = LinkedLatticeNode(BasicSupra())
        self.empty_supracontext.set_next(self.empty_supracontext)

        self.filled: bool = False

    def fill(self, sub_list: SubcontextList) -> None:
        if self.filled:
            raise ValueError("Lattice is already filled and cannot be filled again.")
        self.filled = True

        labeler: Labeler = sub_list.get_labeler()
        # Fill the lattice with all of the subcontexts, masking labels
        for sub in sub_list:
            self.index += 1
            self.insert(sub, labeler.partition(sub.get_label(), self.partition_index))

    def insert(self, sub: Subcontext, label: Label) -> None:
        """Inserts sub into the lattice, into location given by label

        :param sub: Subcontext to be inserted
        :param label: label to be assigned to the subcontext
        """
        self.add_to_context(sub, label)
        for si in label.descendant_iterator():
            self.add_to_context(sub, si)

        # remove supracontexts with count = 0 after every pass
        self.clean_supra()

    def add_to_context(self, sub: Subcontext, label: Label) -> None:
        """Add the given subcontext to the supracontext with the given label"""
        # the default value is the empty supracontext (leave null until now to
        # save time/space)
        if not label in self.lattice.keys():
            self.lattice[label] = self.empty_supracontext

        # if the following supracontext matches the current index, just repoint
        # to that one; this is a supracontext that was made in the final else
        # statement below this one.
        if self.lattice.get(label).get_next().get_index() == self.index:
            # don't decrement count on emptySupracontext!
            if self.lattice.get(label) != self.empty_supracontext:
                self.lattice.get(label).decrement_count()
            self.lattice[label] = self.lattice.get(label).get_next()
            self.lattice.get(label).increment_count()
        # otherwise make a new Supracontext and add it
        else:
            # don't decrement the count for the emptySupracontext!
            if self.lattice.get(label) != self.empty_supracontext:
                self.lattice.get(label).decrement_count()
            self.lattice[label] = self.lattice.get(label).insert_after(sub, self.index)

    def clean_supra(self) -> None:
        """Cycles through the the supracontexts and deletes ones with count=0"""
        supra = self.empty_supracontext
        while supra.get_next() != self.empty_supracontext:
            if supra.get_next().get_count() == 0:
                supra.set_next(supra.get_next().get_next())
            else:
                supra = supra.get_next()

        assert self.no_zero_supras()

    def no_zero_supras(self) -> bool:
        for supra in self.get_supracontexts():
            if supra.get_count() == 0:
                return False
        return True

    def get_supracontexts(self) -> set[Supracontext]:
        """

        :return: The list of supracontexts that were created by filling the supracontextual lattice. From this, you can
                 compute the analogical set.
        """
        sup_list = set()
        supra = self.empty_supracontext.get_next()
        while supra != self.empty_supracontext:
            assert supra.get_count() != 0
            sup_list.add(supra)
            supra = supra.get_next()
        return sup_list

    def supra_list_to_string(self):
        """

        :return: A string representation of the list of Supracontexts created when the Lattice was filled
        """
        supra = self.empty_supracontext.get_next()
        if supra == self.empty_supracontext:
            return "EMPTY"
        string = ""
        while supra != self.empty_supracontext:
            string += f"{supra}->"
            supra = supra.get_next()
        return string
