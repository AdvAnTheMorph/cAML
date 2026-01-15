"""Match/Mismatch label"""

from typing import Iterator, Union, Optional


class Label:
    """This Label implementations stores match and mismatch data in a BitSet."""

    def __init__(self, l: Union[set, 'Label'], c: Optional[int] = None):
        """Create a new label by storing match/mismatch information in the given
        bitset.

        :param l: Label instance or set whose set bits represent mismatches and
            clear bits represent matches
        :param c: cardinality of the label
        """
        if isinstance(l, Label):
            self.label_bits = l.label_bits
            self.card = l.card
        elif c is not None:
            self.label_bits = l
            self.card = c
        else:
            raise ValueError(
                "Either a Label instance or a set and a cardinality must be "
                "given.")
        self.__hash_code = 37 * self.card + hash(frozenset(self.label_bits))

    def matches(self, index: int) -> bool:
        """Determine if the given index is marked as a match or a mismatch.

        :param index: index of the attribute being represented
        """
        if index > self.card - 1 or index < 0:
            raise ValueError(f"Illegal index: {index}")
        return index not in self.label_bits

    def num_matches(self) -> int:
        """Return the total number of matches marked in this label."""
        return self.card - len(self.label_bits)

    def intersect(self, other_label: 'Label') -> 'Label':
        """Create a new label for which each location is marked as a match if
        both this label and other_label are marked match, otherwise mismatch.
        In other words, keep all mismatches from both labels.

        :param other_label: the label to intersect with this one
        """
        if not isinstance(other_label, Label):
            raise ValueError("Labels can only be intersected with other Labels")
        bits = self.label_bits.union(other_label.label_bits)
        return Label(bits, self.card)

    def union(self, other: 'Label') -> 'Label':
        """Create a new label for which each location is marked as a match if
        either this label or other is marked match, otherwise mismatch. In
        other words, keep all matches from both labels.

        :param other: the other label
        """
        if not isinstance(other, Label):
            raise ValueError("Labels can only be unioned with other Labels")
        bits = self.label_bits.intersection(other.label_bits)
        return Label(bits, self.card)

    def all_matching(self) -> bool:
        """Check whether all attributes match"""
        return len(self.label_bits) == 0

    def __repr__(self):
        if self.card == 0:
            return ""
        # unioning with {-1} ensures that set not empty
        # indexing starts with 0, so add 1
        num_leading_zeroes = self.card - (max(self.label_bits.union({-1})) + 1)
        string = "0" * num_leading_zeroes
        if len(self.label_bits) > 0:
            for i in range(max(self.label_bits), -1, -1):  # go backwards
                string += "1" if i in self.label_bits else "0"
        return string

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        if not isinstance(other, Label):
            return False
        return other.card == self.card and other.label_bits == self.label_bits

    def __hash__(self):
        return self.__hash_code

    def descendant_iterator(self) -> Iterator['Label']:
        """Create iterator of all descendants of the label.

        The "descendants" of a label are the set of labels with the same
        "mismatch" entries, but with one or more of the "match" entries changed
        into a "mismatch" entry. For example, the children of
        {match, mismatch, mismatch, match} are:

        - {mismatch, mismatch, mismatch, match}
        - {match, mismatch, mismatch, mismatch}
        - {mismatch, mismatch, mismatch, mismatch}
        """
        return SubsetIterator(self)

    def is_descendant_of(self, possible_ancestor: 'Label') -> bool:
        """Determine if this label is the "descendant" of possible_ancestor.

        This label is a descendant of the other label if every mismatching
        entry in the other label is also a mismatching entry in this label.
        Any label is also a descendant of itself.

        :param possible_ancestor: possible label ancestor
        """
        if not isinstance(possible_ancestor, Label):
            return False
        # boolean lattice ancestor/descendants yield the descendant when ORed;
        # this label needs to have all of the same ones (and optionally more
        # ones)
        for i in possible_ancestor.label_bits:
            if i >= self.card or i not in self.label_bits:
                return False
        return True


class SubsetIterator:
    """Construct an iterator over all subsets of this label"""

    def __init__(self, bitset_label: Label):
        self.card = bitset_label.card
        self.current = set(bitset_label.label_bits)  # copy
        # the indices of the 0 entries
        self.gaps = []

        # iterate over the clear bits and record their locations
        for i in range(self.card):
            if i not in bitset_label.label_bits:
                self.gaps.append(i)
        # if there were no gaps, then there is nothing to iterate over
        if not self.gaps:
            self.has_next = False
            return
        # binCounter needs a trailing 1 for each gap
        self.bin_counter = set(range(len(self.gaps)))
        self.has_next = True

    def __iter__(self):
        return self

    def __next__(self):
        if not self.has_next:
            raise StopIteration
        # we use bin_counter like a binary integer in order to permute all
        # combinations of 1's and 0's for the gaps
        # choose gap bit to flip; it's whichever is the rightmost 1 in
        # bin_counter.
        right_most = min(self.bin_counter)  # since we count from 0 upward
        self.bin_counter.discard(right_most)
        # then subtract 1 from rightMost (do the binary arithmetic by hand here)
        if right_most != 0:
            for i in range(right_most - 1, -1, -1):
                self.bin_counter.add(i)

        # flip
        gap_index = self.gaps[right_most]
        if gap_index in self.current:
            self.current.remove(gap_index)
        else:
            self.current.add(gap_index)

        # we are done permuting when bin_counter hits all zeros
        if not self.bin_counter:
            self.has_next = False
        return Label(self.current.copy(), self.card)
