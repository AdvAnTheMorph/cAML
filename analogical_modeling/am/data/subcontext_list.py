"""SubcontextList

Iterable storing subcontexts
"""

from typing import Iterable

from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.utils import Instance


class SubcontextList:
    """
    This class creates and manages a list of subcontexts from
    a set of previously classified exemplars and an exemplar to be classified.

    After creating a list of subcontexts, iterate through the subcontexts using
    the Iterator returned by iterator().
    """

    # TODO: why use an iterator, instead of just returning a list?

    def __init__(self, labeler: Labeler, data: Iterable[Instance],
                 ignore_full_matches: bool):
        """
        This is the easiest to use constructor. It creates and stores a list of
        subcontexts given classified exemplars and an exemplar to be classified.

        :param labeler: Labeler for assigning labels to items in data
        :param data: Training data (exemplars)
        :param ignore_full_matches: if true, will not add entirely matching
        contexts
        """
        self.label_to_subcontext: dict[Label, Subcontext] = {}
        self.labeler: Labeler = labeler
        self.ignore_full_matches: bool = ignore_full_matches
        # number of exemplars considered accepted into the list,
        # i.e. added and not ignored
        self.considered_exemplar_count: int = 0

        for se in data:
            self.add(se)

    def get_cardinality(self) -> int:
        """Get the number of attributes used to predict an outcome"""
        return self.labeler.get_cardinality()

    def add(self, exemplar: Instance):
        """Add an exemplar"""
        label = self.labeler.label(exemplar)

        if self.ignore_full_matches and label.all_matching():
            return

        if not label in self.label_to_subcontext:
            self.label_to_subcontext[label] = Subcontext(label,
                                                         self.labeler.get_context_string(
                                                             label))
        self.label_to_subcontext[label].add(exemplar)
        self.considered_exemplar_count += 1

    def add_all(self, data: Iterable[Instance]):
        """Adds the exemplars to the correct subcontexts.

        :param data: Exemplars to add
        """
        for d in data:
            self.add(d)

    def __str__(self) -> str:
        """
        This method is not particularly speedy, since it sorts the contained
        subcontexts by label. It is meant for test purposes only; do not rely
        on exact output being the same in the future.
        """
        # sort the labels by hashcode so that output is consistent for testing
        # purposes
        sorted_labels = sorted(self.label_to_subcontext.keys(), key=hash)
        return ",".join(
            [str(self.label_to_subcontext[label]) for label in sorted_labels])

    def __eq__(self, other):
        """Equal if both lists contain the same data in the same subcontexts.

        Labeler object is not compared.
        """
        if self is other:
            return True
        if other is None:
            return False
        if not isinstance(other, SubcontextList):
            return False
        return self.label_to_subcontext == other.label_to_subcontext

    def __iter__(self):
        """

        :return: An iterator which returns each of the contained subcontexts.
        """
        yield from self.label_to_subcontext.values()

    def __len__(self) -> int:
        return len(self.label_to_subcontext)
