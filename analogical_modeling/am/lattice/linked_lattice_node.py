"""Lattice wrapper"""

from typing import TypeVar, Optional

from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.label.label import Label

T = TypeVar("T")


class LinkedLatticeNode(Supracontext):
    """
    This class is a decorator which wraps a Supracontext and adds the
    functionality of a linked node used in certain lattice-filling algorithms.
    An index is also provided for use in determining when the node was created.
    """

    def __init__(self, supra: T, ind: Optional[int] = None):
        """Create a new node containing the given supracontext. The index is
        set to -1.

        :param supra: Supracontext to store in this node
        """
        #  the wrapped supracontext
        self.supra = supra
        # a number representing when this supracontext was created
        if ind is None:
            self.index = -1
        else:
            self.index = ind  # used by insert_after
        # pointer to the next node; this is used during lattice filling to
        # create a circular linked list
        self.next: 'LinkedLatticeNode' = None

    def insert_after(self, sub: Subcontext, ind: int) -> 'LinkedLatticeNode':
        """Create a new node by copying this one, adding the given subcontext
        and setting the index to that provided.

        Insert the new node between this node and its next node by setting
        the new node to be the next node and setting the previous next node
        to be the new node's next node.

        :param sub: Subcontext to insert into the copied Supracontext
        :param ind: index of new node
        """
        new_supra = self.get_supracontext().copy()
        new_supra.count = 1
        new_supra.add(sub)
        new_node = LinkedLatticeNode(new_supra, ind)
        new_node.next = self.next
        self.next = new_node
        return new_node

    def get_index(self) -> int:
        """

        :return: index of this node
        """
        return self.index

    def increment_count(self) -> None:
        """Increases count by one"""
        self.supra.count += 1

    def decrement_count(self) -> None:
        """Decreases the count by one.

        If this reaches 0, then this Supracontext should be discarded
        (by the caller).

        :raises ValueError: if the count is already zero
        """
        if self.supra.count <= 0:
            raise ValueError('Count cannot be less than zero.')
        self.supra.count -= 1

    def get_supracontext(self) -> T:
        """Return supracontext."""
        return self.supra

    def copy(self) -> Supracontext:
        """Return an exact, deep copy of the supracontext.

        :return: deep copy of this supracontext
        """
        new_supra = self.get_supracontext().copy()
        new_node = LinkedLatticeNode(new_supra, self.index)
        new_node.next = self.next
        return new_node

    # Below methods are delegated to the contained supracontext
    def add(self, other: Subcontext) -> None:
        """Add subcontext to contained supracontext."""
        self.supra.add(other)

    def get_data(self) -> frozenset[Subcontext]:
        """Get data of contained supracontext."""
        return self.supra.get_data()

    def is_empty(self) -> bool:
        """Check if contained supracontext is empty."""
        return self.supra.is_empty()

    @property
    def count(self) -> int:
        return self.supra.count

    @count.setter
    def count(self, count: int) -> None:
        self.supra.count = count

    def get_context(self) -> Label:
        """Get context of contained supracontext"""
        return self.supra.get_context()

    def __eq__(self, other):
        if self is other:
            return True
        if other is None:
            return False
        if isinstance(other, LinkedLatticeNode):
            return self.supra == other.supra
        return self.supra == other

    def __hash__(self):
        return hash(self.supra)

    def __str__(self):
        return str(self.supra)
