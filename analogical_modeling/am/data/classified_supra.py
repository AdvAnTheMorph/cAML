"""package weka.classifiers.lazy.AM.data
 * **************************************************************************
 * Copyright 2021 Nathan Glenn                                              *
 * Licensed under the Apache License, Version 2.0 (the "License");          *
 * you may not use this file except in compliance with the License.         *
 * You may obtain a copy of the License at                                  *
 *                                                                          *
 * http://www.apache.org/licenses/LICENSE-2.0                               *
 *                                                                          *
 * Unless required by applicable law or agreed to in writing, software      *
 * distributed under the License is distributed on an "AS IS" BASIS,        *
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. *
 * See the License for the specific language governing permissions and      *
 * limitations under the License.                                           *
 ****************************************************************************
"""

from .supracontext import Supracontext
from .subcontext import Subcontext
from .basic_supra import BasicSupra
from .. import am_utils
from ..label.label import Label

class ClassifiedSupra(Supracontext):
    """
    This supracontext is called "classified" because it keeps track of its
    outcome (or "class") at all times by inspecting the outcomes of the
    subcontexts added to it. It also provides special methods for determining
    its heterogeneity, and for determining if the addition of a subcontext would
    lead to heterogeneity.
    """

    def __init__(self):
        """Creates a supracontext with no data. The outcome will be
        am_utils.UNKNOWN until data is added.
        """
        self.supra = BasicSupra()
        # class attribute value, or nondeterministic, heterogeneous, or undetermined
        self.outcome: float = float("nan")

    def classified_supra(self, data: set, count: int):
        """Creates a new supracontext with the given parameters as the contents.

        :param data: The subcontexts contained in the supracontext
        :param count: The count of this supracontext
        :raises: ValueError if data or count are None, or count is less than 0
        """
        if data is None:
            raise ValueError("data must not be None")
        self.supra = BasicSupra()
        for sub in data:
            self.add(sub)
        self.supra.set_count(count)

    def add(self, other: Subcontext):
        if self.supra.is_empty():
            self.outcome = other.get_outcome()
        elif not self.is_heterogeneous() and self.would_be_hetero(other):
            self.outcome = am_utils.HETEROGENEOUS
        self.supra.add(other)

    def get_outcome(self):
        """
        Get the outcome of this supracontext. If all of the contained subcontexts
        have the same outcome, then this value is returned. If there are no
        subcontexts in this supracontext, {@link AMUtils#UNKNOWN} is returned. If
        there are multiple subs with an outcome of
        AMUtils.NONDETERMINISTIC or the subs with differing outcomes,
        AMUtils.HETEROGENEOUS is returned.
        :return: outcome of this supracontext
        """
        return self.outcome

    def is_heterogeneous(self) -> bool:
        """
        Determine if the supracontext is heterogeneous, meaning that
        get_outcome() returns AMUtils.HETEROGENEOUS.

        :return: True if the supracontext is heterogeneous, False if it is homogeneous.
        """
        return self.outcome == am_utils.HETEROGENEOUS

    def would_be_hetero(self, other) -> bool:
        """
        Test if adding a subcontext would cause this supracontext to become heterogeneous.
        :param other: subcontext to hypothetically add
        :return: True if adding the given subcontext would cause this supracontext to become heterogeneous.
        """
        # Heterogeneous if:
        # - there are subcontexts with different outcomes
        # - there are more than one sub which are non-deterministic
        if self.supra.is_empty():
            return False
        if other.get_outcome() != self.outcome:
            return True
        return other.get_outcome() == am_utils.NONDETERMINISTIC

    def copy(self):
        new_supra = ClassifiedSupra()
        new_supra.supra = self.supra.copy()
        new_supra.outcome = self.outcome
        return new_supra

    # methods below are simply forwarded to the wrapped supracontext
    def get_data(self):
        return self.supra.get_data()

    def is_empty(self) -> bool:
        return self.supra.is_empty()

    def get_count(self) -> int:
        return self.supra.get_count()

    def set_count(self, count: int):
        self.supra.set_count(count)

    def get_context(self):
        return self.supra.get_context()

    def __eq__(self, other) -> bool:
        if self is other:
            return True
        if other is None:
            return False
        return self.supra == other

    def __hash__(self):
        return hash(self.supra)

    def __repr__(self):
        return str(self.supra)
