"""weka.classifiers.lazy.AM.lattice

 * This class is a decorator which wraps a {@link Supracontext} and adds the
 * functionality of a linked node used in certain lattice-filling algorithms. An
 * index is also provided for use in determining when the node was created.
 *
 * @param <T> The implementation of Supracontext to be stored in this node.
"""

from ..data.subcontext import Subcontext
from ..data.supracontext import Supracontext
from ..label.label import Label


class LinkedLatticeNode(Supracontext):
    def __init__(self, supra):
        """Create a new node containing the given supracontext. The index is set to
           -1.

        :param supra: Supracontext to store in this node.
        """
        #  the wrapped supracontext
        self.supra = supra
        # a number representing when this supracontext was created
        self.index: int = -1
        # pointer to the next node; this is used during lattice filling to create a
        # circular linked list
        self.next: 'LinkedLatticeNode' = None

    # FIXME: ?????
    def __linked_lattice_node(self, supra, ind: int):
        """used privately by insertAfter"""
        node = LinkedLatticeNode(supra)
        node.index = ind
        return node

    def insert_after(self, sub: Subcontext, ind: int):
        """
        Create a new node by copying this one, adding the given subcontext and
        setting the index to that provided. Insert the new node between this node
        and its next node by setting the new node to be the next node and setting
        the previous next node to be the new node's next node.

        :param sub: Subcontext to insert into the copied Supracontext
        :param ind: index of new node
        """
        new_supra = self.get_supracontext().copy()
        new_supra.set_count(1)
        new_supra.add(sub)
        new_node = self.__linked_lattice_node(new_supra, ind)
        new_node.set_next(self.get_next())
        self.set_next(new_node)
        return new_node

    def get_next(self) -> 'LinkedLatticeNode':
        """

        :return: the next node linked to by this node
        """
        return self.next

    def set_next(self, node: 'LinkedLatticeNode'):
        """Set the next node linked to by this node

        :param node: the node to link to
        """
        self.next = node

    def get_index(self) -> int:
        """

        :return: The index of this node.
        """
        return self.index

    def increment_count(self):
        """Increases count by one"""
        self.supra.set_count(self.supra.get_count() + 1)

    def decrement_count(self):
        """
        Decreases the count by one; if this reaches 0, then this Supracontext
        should be discarded (by the caller).

        :raises: ValueError if the count is already zero.
        """
        if self.supra.get_count() <= 0:
            raise ValueError('Count cannot be less than zero.')
        self.supra.set_count(self.supra.get_count() - 1)

    def get_supracontext(self):
        return self.supra

    def copy(self) -> Supracontext:
        new_supra = self.get_supracontext().copy()
        new_node = self.__linked_lattice_node(new_supra, self.index)
        new_node.set_next(self.next)
        return new_node

    # Below methods are delegated to the contained supracontext
    def add(self, other: Subcontext):
        self.supra.add(other)

    def get_data(self) -> set[Subcontext]:
        return self.supra.get_data()

    def is_empty(self) -> bool:
        return self.supra.is_empty()

    def get_count(self) -> int:
        return self.supra.get_count()

    def set_count(self, count: int):
        self.supra.set_count(count)

    def get_context(self) -> Label:
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
