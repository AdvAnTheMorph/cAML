"""ClassifiedSupra

Supracontext which includes outcome ("classification") and determines
heterogeneity

- homogeneous if

  a) deterministic
  b) non-deterministic, but all occurrences occur within only one of its
     subcontexts

- heterogeneous otherwise
"""

from typing import Optional

from analogical_modeling.am import am_utils
from analogical_modeling.am.data.basic_supra import BasicSupra
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.label.label import Label


class ClassifiedSupra(Supracontext):
    """
    This supracontext is called "classified" because it keeps track of its
    outcome (or "class") at all times by inspecting the outcomes of the
    subcontexts added to it. It also provides special methods for determining
    its heterogeneity, and for determining if the addition of a subcontext would
    lead to heterogeneity.
    """

    def __init__(self, data: Optional[set] = None, count: Optional[int] = None):
        """Creates a supracontext with no data. The outcome will be
        `am_utils.UNKNOWN` until data is added.

        If parameters are given:
        Creates a new supracontext with the given parameters as the contents.

        :param data: subcontexts contained in the supracontext
        :param count: count of this supracontext
        :raises ValueError: if data XOR count is None, or count is less than 0
        """
        if data is None and count is not None:
            raise ValueError("data must not be None")
        self.supra = BasicSupra()

        # The outcome is:
        # - am_utils.UNKNOWN, if there are no subcontexts in this supracontext
        # - am_utils.NONDETERMINISTIC,
        # - am_utils.HETEROGENEOUS, if there are multiple subcontexts with the
        #   outcome am_utils.NONDETERMINISTIC, or subcontexts have differing
        #   outcomes
        # - the outcome of the contained subcontexts, otherwise
        self.outcome: float|str = am_utils.UNKNOWN

        if data is not None:
            for sub in data:
                self.add(sub)
            self.supra.count = count

    def add(self, other: Subcontext) -> None:
        """Add a subcontext to this supracontext.

        :param other: subcontext to add to the supracontext
        """
        if self.supra.is_empty():
            self.outcome = other.outcome
        elif not self.is_heterogeneous() and self.would_be_hetero(other):
            self.outcome = am_utils.HETEROGENEOUS
        self.supra.add(other)

    def is_heterogeneous(self) -> bool:
        """
        Determine if the supracontext is heterogeneous, meaning that
        :any:`self.outcome` equals `am_utils.HETEROGENEOUS`.

        :return: True if the supracontext is heterogeneous, False if it is
            homogeneous
        """
        return self.outcome == am_utils.HETEROGENEOUS

    def would_be_hetero(self, other) -> bool:
        """Test if adding a subcontext would cause this supracontext to become
        heterogeneous.

        :param other: subcontext to hypothetically add
        :return: True if adding the given subcontext would cause this
            supracontext to become heterogeneous
        """
        # Heterogeneous if:
        # - there are subcontexts with different outcomes
        # - there are more than one subcontext which are non-deterministic
        if self.supra.is_empty():
            return False
        if other.outcome != self.outcome:
            return True
        return other.outcome == am_utils.NONDETERMINISTIC

    def copy(self) -> 'ClassifiedSupra':
        """Return an exact, deep copy of the supracontext."""
        new_supra = ClassifiedSupra()
        new_supra.supra = self.supra.copy()
        new_supra.outcome = self.outcome
        return new_supra

    # methods below are simply forwarded to the wrapped supracontext
    def get_data(self) -> frozenset:
        return self.supra.get_data()

    def is_empty(self) -> bool:
        return self.supra.is_empty()

    @property
    def count(self) -> int:
        return self.supra.count

    @count.setter
    def count(self, count: int) -> None:
        self.supra.count = count

    def get_context(self) -> Label:
        return self.supra.get_context()

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if other is None:
            return False
        if isinstance(other, ClassifiedSupra):
            return self.supra == other.supra
        return self.supra == other

    def __hash__(self):
        return hash(self.supra)

    def __str__(self):
        return str(self.supra)
