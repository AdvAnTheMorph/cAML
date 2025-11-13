"""weka.classifiers.lazy.AM.lattice"""

from abc import ABC, abstractmethod

from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.data.supracontext import Supracontext


class Lattice(ABC):
    """Abstract base class for lattices."""
    @abstractmethod
    def fill(self, sub_list: SubcontextList):
        """Fill the lattice with given subcontexts. This is meant to be done
        only once for a given Lattice instance.

        :raises: ValueError if the lattice was already filled
        """

    @abstractmethod
    def get_supracontexts(self) -> set[Supracontext]:
        """

        :return: The list of supracontexts that were created by filling the
        supracontextual lattice. From this, you can
        compute the analogical set.
        """
