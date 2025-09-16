"""weka.classifiers.lazy.AM.label"""


from typing import Iterator, Union


class Label:
    """This Label implementations sores match and mismatch data in a
    BitSet, so there is no limit on the cardinality."""
    def __init__(self, l: Union[set,'Label'], c: int|None = None):
        """Create a new label by storing match/mismatch information in the given
        bitset.

        :param l: Set whose set bits represent mismatches and clear bits represent matches
        :param c: cardinality of the label
        """
        if c is not None:
            self.label_bits = l
            self.card = c
            self.hash_code = 37 * self.get_cardinality() + hash(frozenset(self.label_bits))
        elif isinstance(l, Label):
            self.label_bits = l.label_bits
            self.card = l.card
            self.hash_code = l.hash_code
        else:
            raise ValueError("Either a Label instance or a set and a cardinality must be given.")

    def get_cardinality(self) -> int:
        return self.card

    def matches(self, index: int) -> bool:
        if index > self.get_cardinality() - 1 or index < 0:
            raise ValueError(f"Illegal index: {index}")
        return index not in self.label_bits

    def num_matches(self) -> int:
        return self.get_cardinality() - len(self.label_bits)

    def intersect(self, other_label: 'Label') -> 'Label':
        if not isinstance(other_label, Label):
            raise ValueError("BitSetLabel can only be intersected with other BitSetLabel")
        bits = self.label_bits.union(other_label.label_bits)
        return Label(bits, self.get_cardinality())

    def union(self, other: 'Label') -> 'Label':
        if not isinstance(other, Label):
            raise ValueError("BitSetLabel can only be unioned with other BitSetLabel")
        bits = self.label_bits.intersection(other.label_bits)
        return Label(bits, self.get_cardinality())

    def all_matching(self) -> bool:
        return len(self.label_bits) == 0

    def __str__(self):
        if self.get_cardinality() == 0:
            return ""
        num_leading_zeroes = self.get_cardinality() - (max(self.label_bits.union({-1}))+1)
        string = "0" * num_leading_zeroes
        if len(self.label_bits) > 0:
            for i in range(max(self.label_bits), -1, -1):
                string += "1" if i in self.label_bits else "0"
        return string

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        if not isinstance(other, Label):
            return False
        return other.get_cardinality() == self.get_cardinality() and other.label_bits == self.label_bits

    def __hash__(self):
        return self.hash_code

    def descendant_iterator(self) -> Iterator['Label']:
        return SubsetIterator(self)

    def is_descendant_of(self, possible_descendant: 'Label') -> bool:
        if not isinstance(possible_descendant, Label):
            return False
        # boolean lattice ancestor/descendants yield the descendant when ORed;
        # this label needs to have all of the same ones (and optionally more
        # ones)
        for i in possible_descendant.label_bits:
            if i >= self.card or i not in self.label_bits:
                return False
        return True


class SubsetIterator:
    def __init__(self, bitset_label: Label):
        """Construct an iterator over all subsets of this label"""
        self.card = bitset_label.get_cardinality()
        self.current = bitset_label.label_bits
        # the indices of the 0 entries
        self.gaps = []

        # iterate over the clear bits and record their locations
        for i in range(self.card):
            if i not in self.current:
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
        # we use binCounter like a binary integer in order to permute
        # all combinations of 1's and 0's for the gaps
        # choose gap bit to flip; it's whichever is the rightmost
        # 1 in binCounter.
        right_most = min(self.bin_counter) # since we count from 0 upward
        self.bin_counter.discard(right_most)
        # then subtract 1 from rightMost (do the binary arithmetic by hand here)
        if right_most != 0:
            for i in range(right_most-1, -1, -1):
                self.bin_counter.add(i)

        # flip
        gap_index = self.gaps[right_most]
        if gap_index in self.current:
            self.current.remove(gap_index)
        else:
            self.current.add(gap_index)

        # we are done permuting when binCounter hits all zeros
        if not self.bin_counter:
            self.has_next = False
        return Label(self.current.copy(), self.card)

    def remove(self):
        raise NotImplementedError("remove() is not supported")
