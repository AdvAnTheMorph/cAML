"""Subcontext

A subcontext specifies all variables of its supracontext and more.
Example: (a-cd) is a subcontext of (a-c-)
"""

from analogical_modeling.am import am_utils
from analogical_modeling.am.label.label import Label
from analogical_modeling.utils import Instance


class Subcontext:
    """
    Represents a subcontext, containing a list of Instances which belong to
    it, along with their shared Label and common outcome.
    If the contained instances do not have the same outcome, then the outcome is
    set to am_utils.NONDETERMINISTIC.
    """
    SEED = 37

    def __init__(self, label: Label, display_label: str):
        """Initializes the subcontext by creating a list to hold the data

        :param label: Binary label of the subcontext
        :param display_label: user-friendly label string
        Labeler.get_context_string(Label)
        """
        self.label: Label = label
        self.display_label: str = display_label
        self.data: set[Instance] = set()
        self.outcome: str | int = ""
        self.hash: int = -1

    def add(self, other):
        """Add an exemplar to the subcontext and set the outcome accordingly.

        If different outcomes are present in the contained exemplars, the
        outcome is am_utils.NONDETERMINISTIC
        """
        if len(self.data) > 0:
            if other.class_value() != next(iter(self.data)).class_value():
                self.outcome = am_utils.NONDETERMINISTIC
        else:
            self.outcome = other.class_value()
        self.data.add(other)

    def get_exemplars(self) -> set[Instance]:
        """

        :return: list of exemplars contained in this subcontext
        """
        return self.data

    def __eq__(self, other):
        """Two Subcontexts are considered equal if they have the same label and
        contain the same instances."""
        if self is other:
            return True
        if other is None:
            return False
        if not isinstance(other, Subcontext):
            return False
        if not self.label == other.label:
            return False
        return self.data == other.data

    def __hash__(self):
        if self.hash != -1:
            return self.hash
        self.hash = self.SEED * hash(self.label) + hash(frozenset(self.data))
        return self.hash

    def __str__(self):
        middle_part = ""
        if self.outcome == am_utils.NONDETERMINISTIC:
            middle_part = am_utils.NONDETERMINISTIC_STRING
        elif len(self.data) > 0:
            middle_part = next(iter(self.data)).class_value()

        # str(Instance) separates attributes with commas, so we can't
        # use a comma here, or it will be difficult to read
        return f"({self.label}|{middle_part}|{'/'.join(map(str, self.data))})"

    def is_nondeterministic(self) -> bool:
        """Check whether the outcome is nondeterministic."""
        return self.outcome == am_utils.NONDETERMINISTIC
