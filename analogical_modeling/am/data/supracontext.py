"""weka.classifiers.lazy.AM.data"""

from abc import ABC, abstractmethod
from functools import reduce

from analogical_modeling.am.label.label import Label
from analogical_modeling.am.data.subcontext import Subcontext

class Supracontext(ABC):
    """ A supracontext contains a set of Subcontexts which have certain
    commonalities in their Labels.

    Classifying data sets with analogical modeling tends to create many
    supracontexts with the exact same set of subcontexts. To save time and
    space, duplicate supracontexts should be kept track of using the count
    instead of by saving separate Supracontext objects. The count is stored
    in a BigInteger object and starts out as 1 and is never allowed to fall
    below 0, which indicates that the object should be discarded.
    """
    @abstractmethod
    def copy(self) -> 'Supracontext':
        """Return an exact, deep copy of the supracontext.

        The new object should be an instance of the same class as the calling
        object.

        :return: a deep copy of this supracontext.
        """

    @abstractmethod
    def get_data(self) -> frozenset[Subcontext]:
        """

        :return: an unmodifiable view of the set of subcontexts contained in
        this supracontext.
        """

    @abstractmethod
    def add(self, other: Subcontext) -> None:
        """Add a subcontext to this supracontext.

        :param other: subcontext to add to the supracontext.
        """

    @abstractmethod
    def is_empty(self) -> bool:
        """

        :return: True if this supracontext contains no subcontexts; False
        otherwise.
        """

    @abstractmethod
    def get_count(self) -> int:
        """

        :return: the number of copies of this supracontext contained in the
        lattice
        """

    @abstractmethod
    def set_count(self, count: int) -> None:
        """Set the count of the supracontext.

        :param count: the count
        :raises: ValueError if the count is None or less than zero.
        """

    @abstractmethod
    def get_context(self) -> Label:
        """Retrieve the supracontextual context, represented with a Label
        object.

	    Label mismatches should be interpreted as "contained subcontexts may
	    or may not match for this attribute, while matches should be regarded
	    as "all contained subcontexts matched for this attribute".

	    The running time for this default implementation is linear in the
	    number of contained subcontexts.
        :return: The context for this supracontext, or None if the subcontexts
        are empty
        """
        return reduce(lambda x, y: x.intersect(y),
                      [subcontext.get_label() for subcontext in self.get_data()])

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """
        Two Supracontexts are equal if they are of the same class
        and contain the same subcontexts.
        """

    @abstractmethod
    def __hash__(self) -> int:
        """
        The hashcode depends solely on the set of subcontexts
        contained in a supracontext.
        """
