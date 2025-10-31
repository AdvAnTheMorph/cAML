"""weka.classifiers.lazy.AM.data"""
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

from analogical_modeling.am import am_utils
from analogical_modeling.am.label.label import Label
from analogical_modeling.utils import Instance


class Subcontext:
    """
    Represents a subcontext, containing a list of Instances
    which belong to it, along with their shared Label and common outcome.
    If the contained instances do not have the same outcome, then the outcome is
    set to AMUtils.NONDETERMINISTIC.
    """
    SEED = 37


    def __init__(self, label: Label, display_label: str):
        """Initializes the subcontext by creating a list to hold the data

        :param label: Binary label of the subcontext
        :param display_label: user-friendly label string Labeler.get_context_string(Label)
        """
        self.label: Label = label
        self.display_label: str = display_label
        self.data: set[Instance] = set()
        self.outcome: str|int = ""  # private double outcome
        self.hash: int = -1

    def add(self, other):
        """
        Adds an exemplar e to the subcontext and sets the outcome accordingly. If
        different outcomes are present in the contained exemplars, the outcome is
        AMUtils.NONDETERMINISTIC
        """
        if len(self.data):
            if other.class_value() != next(iter(self.data)).class_value():
                self.outcome = am_utils.NONDETERMINISTIC
        else:
            self.outcome = other.class_value()
        self.data.add(other)

    def get_outcome(self) -> str:
        return self.outcome

    def get_label(self) -> Label:
        """Get binary label of of this subcontext"""
        return self.label

    def get_display_label(self) -> str:
        """
        see Labeler.get_context_string(Label)

        :return: User-friendly label string
        """
        return self.display_label

    def get_exemplars(self) -> set[Instance]:
        """

        :return: list of Exemplars contained in this subcontext
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
        elif len(self.data):
            middle_part = next(iter(self.data)).class_value()

        # str(Instance) separates attributes with commas, so we can't
        # use a comma here or it will be difficult to read
        return f"({self.label}|{middle_part}|{'/'.join(map(str, self.data))})"

    def is_nondeterministic(self) -> bool:
        return self.outcome == am_utils.NONDETERMINISTIC
