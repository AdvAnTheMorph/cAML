"""Basic Lattice"""

from analogical_modeling.am import am_utils
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.lattice.lattice import Lattice
from analogical_modeling.am.lattice.linked_lattice_node import LinkedLatticeNode


class BasicLattice(Lattice):
    """
    This class holds the supracontextual lattice and does the work of filling
    itself during classification.

    This class represents the supracontextual lattice. The supractontextual
    lattice is a boolean algebra which models supra- and subcontexts for the AM
    algorithm. Using boolean algebra allows efficient computation of these as
    well as traversal of all subcontexts within a supracontext.
    """

    def __init__(self):
        """
        Initializes Supracontextual lattice to a `2^n` length array of
        Supracontexts, as well as the empty and heterogeneous supracontexts.
        """
        # points to nothing, has no data or outcome
        self.hetero_supra = LinkedLatticeNode(ClassifiedSupra())
        # all points in the lattice point to the empty supracontext by default
        self.empty_supracontext = LinkedLatticeNode(ClassifiedSupra())
        self.empty_supracontext.next = self.empty_supracontext

        self.lattice: dict[Label, LinkedLatticeNode] = {}
        self.filled = False
        # the current number of the subcontext being added
        self.index = -1

    def fill(self, sub_list: SubcontextList) -> None:
        """Fill the lattice with given subcontexts. This is meant to be done
        only once for a given Lattice instance.

        :raises ValueError: if the lattice was already filled
        """
        if self.filled:
            raise ValueError(
                "Lattice is already filled and cannot be filled again.")
        self.filled = True
        # fill the lattice with all the subcontexts
        for sub in sub_list:
            self.index += 1
            self.insert(sub)

    def insert(self, sub: Subcontext):
        """Insert sub into the lattice.

        :param sub: Subcontext to be inserted
        """
        # skip this if the supracontext to be added to is already heterogeneous;
        # it would not be possible to make any non-heterogeneous supracontexts.

        if self.lattice.get(sub.label) is self.hetero_supra:
            return
        # add the sub to its label position
        self.add_to_context(sub, sub.label)
        # then add the sub to all the children of its label position
        for el in sub.label.descendant_iterator():
            self.add_to_context(sub, el)
        # remove supracontexts with count = 0 after every pass
        self.clean_supra()

    def add_to_context(self, sub: Subcontext, label: Label):
        """

        :param sub: subcontext to be added
        :param label: label of supracontext to add the subcontext to
        """
        # the default value is the empty supracontext (leave None until now to
        # save time/space)
        if label not in self.lattice:
            self.lattice[label] = self.empty_supracontext

        # if the Supracontext is heterogeneous, ignore it
        if self.lattice.get(label) is self.hetero_supra:
            return

        # if the following supracontext matches the current index, just
        # re-point to that one; this is a supracontext that was made in
        # the final else statement below this one.
        if self.lattice.get(label).next.get_index() == self.index:
            # don't decrement count on empty_supracontext!
            if self.lattice.get(label) != self.empty_supracontext:
                self.lattice.get(label).decrement_count()
            self.lattice[label] = self.lattice.get(label).next
            self.lattice[label].increment_count()
        # we now know that we will have to make a new Supracontext to contain
        # this subcontext; don't bother making heterogeneous supracontexts
        elif self.lattice.get(label).get_supracontext().would_be_hetero(sub):
            self.lattice.get(label).decrement_count()
            self.lattice[label] = self.hetero_supra
            return
        # otherwise make a new Supracontext and add it
        else:
            # don't decrement the count for the empty_supracontext!
            if self.lattice.get(label) != self.empty_supracontext:
                self.lattice.get(label).decrement_count()
            self.lattice[label] = self.lattice.get(label).insert_after(sub,
                                                                       self.index)

    def clean_supra(self):
        """Cycles through the supracontexts and deletes ones with count 0"""
        supra = self.empty_supracontext
        while supra.next != self.empty_supracontext:
            if supra.next.count == 0:
                supra.next = supra.next.next
            else:
                supra = supra.next
        assert self.no_zero_supras()

    def get_supracontexts(self) -> set:
        """

        :return: the list of supracontexts that were created by filling the
        supracontextual lattice. From this, you can compute the analogical set.
        """
        sup_list = set()
        supra = self.empty_supracontext.next
        while supra != self.empty_supracontext:
            sup_list.add(supra)
            supra = supra.next
        return sup_list

    # Below methods are for private debugging and asserting
    def dump_lattice(self):
        # useful for private debugging on occasion
        return am_utils.LINE_SEPARATOR.join([
            f"{k}:[hetero]" if v is self.hetero_supra else f"{k}:{v}"
            for k, v in self.lattice.items()
        ])

    def no_zero_supras(self):
        """Check for presence of supracontexts with count 0"""
        for supra in self.get_supracontexts():
            if supra.count == 0:
                return False
        return True
