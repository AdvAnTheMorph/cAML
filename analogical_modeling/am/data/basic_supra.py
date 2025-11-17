"""weka.classifiers.lazy.AM.data"""

from typing import Optional

from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.label.label import Label


class BasicSupra(Supracontext):
    """Basic implementation of Supracontext with no extra features."""
    def __init__(self, data: Optional[set] = None, count: Optional[int] = None):
        """Creates a new supracontext with the given parameters as the contents.
        If no args given: create a new supracontext with an empty data set.

        :param data: The subcontexts contained in the supracontext
        :param count: The count of this supracontext
        :raises: ValueError if data XOR count are None, or count is less than 0
        """
        if data is None and count is not None:
            raise ValueError("data must not be null")
        self.set_count(count or 1)
        if data is None:
            self.data = set()
        else:
            self.data = data
        # cached on first calculation
        self.context: Optional[Label] = None

    def add(self, other: Subcontext):
        """Add a subcontext to this supracontext.

        :param other: subcontext to add to the supracontext.
        """
        # the value is cached when get_context is called, but is invalidated
        # when new data is added
        self.context = None
        self.data.add(other)

    def get_data(self) -> frozenset:
        return frozenset(self.data)

    def is_empty(self):
        return len(self.data) == 0

    def get_count(self) -> int:
        return self.count

    def set_count(self, count: int):
        if count is None:
            raise ValueError("count must not be null")
        if count < 0:
            raise ValueError("count must not be less than zero")
        self.count = count

    def get_context(self) -> Label:
        if not self.context:
            self.context = super().get_context()
        return self.context

    def copy(self):
        new_supra = BasicSupra()
        new_supra.data = self.data.copy()
        new_supra.count = self.count
        return new_supra

    def __eq__(self, other):
        if not other:
            return False
        if not isinstance(other, BasicSupra):
            return False
        return self.get_data() == other.get_data()

    def __hash__(self):
        return hash(self.get_data())

    def __str__(self):
        """

        :return: String representation of this supracontext in this form:
                 "[" count "x" sub1.toString() "," sub2.toString() ... "]"
        """
        if self.is_empty():
            return "[EMPTY]"
        return f"[{self.count}x{','.join([str(sub) for sub in self.data])}]"
