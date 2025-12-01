"""Utility constants for Analogical Modeling."""

from os import linesep

# An unknown class value.
UNKNOWN = float("nan")

# A non-deterministic outcome, meaning that there is more than one
# possibility.
NONDETERMINISTIC = -1
NONDETERMINISTIC_STRING = "&nondeterministic&"

# A heterogeneous outcome, which means we don't bother with it.
HETEROGENEOUS = -2

LINE_SEPARATOR = linesep
