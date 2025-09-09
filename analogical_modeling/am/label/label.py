"""weka.classifiers.lazy.AM.label

 * Analogical Modeling uses labels composed of boolean vectors in order to group
 * instances into subcontexts and subcontexts into supracontexts. Training set
 * instances are assigned labels by comparing them with the instance to be
 * classified and encoding matched attributes and mismatched attributes in a
 * boolean vector.
 *
 * Labels should implement __eq__() and __hash__() for use in hashed
 * collections; however, Labels of two different classes do not have to be
 * equals() or have equal hash codes, even if the information they contain is
 * equivalent.
 """

from sys import maxsize
from typing import Iterator, Union


class Label:
    """
    A Label implementation that stores match/mismatch data in a single
    long for compactness and speed. The use of a long as storage, however,
    creates a limit to the size of the label. See {MAX_CARDINALITY.

    @author Nathan Glenn
    """
    def __init__(self, bits_or_label: Union[int,'Label'], cardinality: int = None):
        """
        The maximum cardinality of a long label, which is limited by the number
        of bits in a long in Java.

        :param bits: binary label represented by bits in a long
        :param cardinality: cardinality of the label
        """
        if cardinality is not None:
            if cardinality > maxsize:
                raise ValueError(f"Input cardinality too high ({cardinality}); max cardinality for this labeler is {maxsize}")
            self._label_bits = bits_or_label
            self.card = cardinality
            self.hash_code = self.calculate_hash_code()
        elif bits_or_label:
            self._label_bits = bits_or_label.label_bits()
            self.card = bits_or_label.get_cardinality()
            self.hash_code = bits_or_label.hash_code


    def calculate_hash_code(self):
        return 37 * hash(self.label_bits()) + self.get_cardinality()


    def label_bits(self):
        """

        :return: A long whose 1 bits represent the mismatches and 0 bits represent the matches in this label.
        """
        return self._label_bits

    def get_cardinality(self) -> int:
        """

        :return: The number of attributes represented in this label.
        """
        return self.card

    def matches(self, index: int) -> bool:
        """Determine if the given index is marked as a match or a mismatch.

        :param index: Index of the attribute being represented
        :return: True if the index is a match, false otherwise.
        :raises: ValueError if the index is less than 0 or greater than get_cardinality() - 1.
        """
        if index > self.get_cardinality() -1 or index < 0:
            raise ValueError(f"Illegal index: {index}")
        mask = 1 << index
        return (mask & self._label_bits) == 0


    def num_matches(self) -> int:
        """

        :return: The total number of matches marked in this label.
        """
        return self.get_cardinality() - self._label_bits.bit_count()


    def descendant_iterator(self) -> Iterator['Label']:
        """
        The "descendants" of a label are the set of labels with the same
        "mismatch" entries, but with one or more of the "match" entries changed
        into a "mismatch" entry. For example, the children of
        {match, mismatch, mismatch, match} are:
        - {mismatch, mismatch, mismatch, match}
        - {match, mismatch, mismatch, mismatch}
        - {mismatch, mismatch, mismatch, mismatch}

        :return: An iterator over the label descendants
        """
        return SubsetIterator(self)

    def is_descendant_of(self, possible_ancestor: 'Label') -> bool:
        """
        Determine if this label is the "descendant" of possibleAncestor. This
        label is a descendant of the other label if every mismatching entry in
        the other label is also a mismatching entry in this label. Any label is
        also a descendant of itself.

        :param possible_ancestor: possible label ancestor
        :return: True if possible_ancestor is an ancestor of this label; False otherwise.
        """
        if not isinstance(possible_ancestor, Label):
            return False
        # boolean lattice ancestor/descendants yield the descendant when ORed
        return possible_ancestor.label_bits() | self.label_bits() == self.label_bits()

    def intersect(self, other: 'Label') -> 'Label':
        """
        Create a new label for which each location is marked as a match if both
        this label and otherLabel are marked match, otherwise mismatch. In other
        words, keep all mismatches from both labels.

        :param other: the label to intersect with this one
        :return: an intersected label
        """
        if not isinstance(other, Label):
            raise ValueError("Cannot intersect Label with a non-Label instance")
        return Label(self.label_bits()|other.label_bits(), self.get_cardinality())

    def union(self, other: 'Label') -> 'Label':
        """
        Create a new label for which each location is marked as a match if either
        this label or {@code other} is marked match, otherwise mismatch. In other
        words, keep all matches from both labels.
        """
        if not isinstance(other, Label):
            raise ValueError("Cannot union Label with a non-Label instance")
        return Label(self.label_bits() & other.label_bits(), self.get_cardinality())

    def all_matching(self) -> bool:
        """

        :return: True if every feature of this label is a match (i.e. this is the
        Labeler.get_lattice_top() -> top of the lattice); False otherwise
        """
        return self._label_bits == 0

    def __repr__(self):
        if self.get_cardinality() == 0:
            return ""
        binary = bin(self.label_bits())[2:]
        num_leading_zeroes = self.get_cardinality() - len(binary)
        return f"{'0'*num_leading_zeroes}{binary}"

    def __eq__(self, other: 'Label') -> bool:
        if self is other:
            return True
        if other is None or not isinstance(other, Label):
            return False
        return other.label_bits() == self.label_bits() and other.get_cardinality() == self.get_cardinality()

    def __hash__(self):
        return self.hash_code


class SubsetIterator:
    def __init__(self, label: Label):
        """Construct an iterator over all subsets of this label"""
        self.card = label.get_cardinality()
        self.current = label.label_bits()
        # the indices of the 0 entries
        self.gaps = []

        gaps_temp = []
        # iterate over the clear bits and create a list of gaps;
        # each gap in the list is an int with all 0 bits except
        # where the gap was found in the supracontext. So 10101
        # would create two gaps: 01000 and 00010.
        for i in range(self.card):
            if 1 << i & self.current == 0:
                # create a long with only bit i set to 1
                gaps_temp.append(1 << i)

        # if there were no gaps, then there is nothing to iterate over
        size = len(gaps_temp)
        if not size:
            self.has_next = False
            return

        # binCounter needs to be all ones for the last n bits, where n is
        # numGaps;
        self.bin_counter = 0
        for i in range(size):
            self.bin_counter |= 1 << i
        self.has_next = True

        self.gaps = [gaps_temp[i] for i in range(size)]

    def __iter__(self):
        return self

    def __next__(self):
        if not self.has_next:
            raise StopIteration
        # choose gap to choose bit to flip; it's whichever is the rightmost
        # 1 in binCounter
        # first find the rightmost 1 in t; from HAKMEM, I believe
        i = 0
        tt = ~ self.bin_counter & (self.bin_counter - 1)
        while tt > 0:
            tt >>= 1
            i += 1

        self.current ^= self.gaps[i]
        self.bin_counter -= 1
        if self.bin_counter == 0:
            self.has_next = False
        return Label(self.current, self.card)

    def remove(self):
        raise NotImplementedError("remove() is not supported")
