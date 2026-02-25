"""Specification of how to handle non-specified data."""

from enum import Enum

from analogical_modeling.utils import Instance


class NonspecifiedDataCompare(Enum):
    """Enum specifying non-specified data comparison."""
    MATCH = ("match", "Consider the non-specified attribute value to "
             "match anything")
    MISMATCH = ("mismatch",
                "Consider the non-specified attribute value to be a mismatch")
    VARIABLE = ("variable",
                "Treat the the non-specified attribute value as an attribute "
                "value of its own; a non-specified value will match another "
                "non-specified value, but nothing else."
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

    def matches(self, i1: Instance, i2: Instance, idx: int) -> bool:
        """Compare the two instances and return the comparison result.

        It is assumed that the first instance has a non-specified value for the
        given attribute.

        :param i1: first instance
        :param i2: second instance
        :param idx: index of attribute to be compared between the two instances
        :return: True if the attributes match, False if they do not; the
            matching mechanism depends on the chosen algorithm
        """
        if self is self.MATCH:
            return True  # matches anything
        if self is self.MISMATCH:
            return False  # mismatch
        if self is self.VARIABLE:
            return i1.is_unspecified(idx) and i2.is_unspecified(idx)
        raise NotImplementedError(f"Unknown NonspecifiedDataCompare: {self}")
