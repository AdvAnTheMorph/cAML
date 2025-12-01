"""Specification of how to handle missing data"""

from enum import Enum

from analogical_modeling.utils import Instance


class MissingDataCompare(Enum):
    """Enum specifying missing data comparison."""
    MATCH = ("match", "Consider the missing attribute value to match anything")
    MISMATCH = ("mismatch", "Consider the missing attribute value to be a mismatch")
    VARIABLE = ("variable",
                "Treat the the missing attribute value as an attribute value of its own; "
                "a missing value will match another missing value, but nothing else."
                )

    def __init__(self, option_string: str, description: str):
        """

        :param option_string: The string required to choose this comparison
        strategy from the command line
        :param description: A description of the comparison strategy for the
        given value
        """
        # string used on command line to indicate the use of this strategy
        self.option_string = option_string
        # string which describes comparison strategy for a given entry
        self.description = description

    def get_option_string(self) -> str:
        """

        :return: string used on command line to indicate the use of this strategy
        """
        return self.option_string

    def get_description(self) -> str:
        """

        :return: string which describes comparison strategy for a given entry
        """
        return self.description

    def matches(self, i1: Instance, i2: Instance, idx: int) -> bool:
        """Compare the two instances and return the comparison result.

        It is assumed that the first instance has a missing value for the
        given attribute.

        :param i1: first instance
        :param i2: second instance
        :param idx: index of attribute to be compared between the two instances
        :return: True if the attributes match, False if they do not; the
        matching mechanism depends on the chosen algorithm.
        """
        if self is self.MATCH:
            return True  # matches anything
        if self is self.MISMATCH:
            return False  # mismatch
        if self is self.VARIABLE:
            return i1.is_missing(idx) and i2.is_missing(idx)
        raise NotImplementedError(f"Unknown MissingDataCompare: {self}")
