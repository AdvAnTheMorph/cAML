"""weka.classifiers.lazy.AM.label"""
# * **************************************************************************
 # * Copyright 2021 Nathan Glenn                                              *
 # * Licensed under the Apache License, Version 2.0 (the "License");          *
 # * you may not use this file except in compliance with the License.         *
 # * You may obtain a copy of the License at                                  *
 # *                                                                          *
 # * http://www.apache.org/licenses/LICENSE-2.0                               *
 # *                                                                          *
 # * Unless required by applicable law or agreed to in writing, software      *
 # * distributed under the License is distributed on an "AS IS" BASIS,        *
 # * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. *
 # * See the License for the specific language governing permissions and      *
 # * limitations under the License.                                           *
 # ****************************************************************************

from enum import Enum

from ...utils import Instance


class MissingDataCompare(Enum):
    MATCH = ("match", "Consider the missing attribute value to match anything")
    MISMATCH = ("mismatch", "Consider the missing attribute value to be a mismatch")
    VARIABLE = ("variable",
                "Treat the the missing attribute value as an attribute value of its own; "
                "a missing value will match another missing value, but nothing else."
                )

    def __init__(self, option_string: str, description: str):
        """

        :param option_string: The string required to choose this comparison strategy from the command line
        :param description: A description of the comparison strategy for the given value
        """
        self.option_string = option_string  # string used on command line to indicate the use of this strategy
        self.description = description  # string which describes comparison strategy for a given entry

    def get_option_string(self) -> str:
        """

        :return: string used on command line to indicate the use of this strategy
        """
        return self.option_string

    def get_description(self) -> str:
        """

        :return: string which describes comparison strategy for a given
        """
        return self.description

    def matches(self, i1: Instance, i2: Instance, idx: int) -> bool:
        """Compare the two instances and return the comparison result. It is assumed
        that has a missing value for the given attribute.

        :param i1: First instance
        :param i2: Second instance
        :param idx: Index of attribute to be compared between the two instances
        :return: True if the attributes match, False if they do not; the matching mechanism depends on the chosen
        algorithm.
        """
        if self is self.MATCH:
            return True  # matches anything
        elif self is self.MISMATCH:
            return False  # mismatch
        elif self is self.VARIABLE:
            return i1.is_missing(idx) and i2.is_missing(idx)
        else:
            raise NotImplementedError(f"Unknown MissingDataCompare: {self}")
