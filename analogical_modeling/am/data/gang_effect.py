"""weka.classifiers.lazy.AM.data"""

from collections import defaultdict

from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.utils import Instance


class GangEffect:
    """
    Exemplars that seem less similar to the test item than those that seem
    more similar can still have a magnified effect if there are many of
    them. This is known as the <em>gang effect</em>.
    <p>
    This class represents the total effect that exemplars in one subcontext have
    on the predicted outcome.
    """

    def __init__(self, sub: Subcontext, exemplar_pointers = dict[Instance, int]):
        self.subcontext = sub
        # Maps outcome to the exemplars supporting that outcome
        # TODO: list or SortedSet would be better, but Instance is not comparable :(
        # TODO: is it?
        self.class_to_instances: dict[str, set[Instance]] = defaultdict(set)
        for i in sub.get_exemplars():
            key = i.string_value(i.class_index)
            self.class_to_instances[key].add(i)
        # Maps each outcome to the total pointers for all exemplars supporting that outcome
        self.class_to_pointers: dict[str, int] = {
            key: sum(exemplar_pointers[i] for i in instances)
            for key, instances in self.class_to_instances.items()
        }
        # Total pointers for all exemplars in the subcontext
        self.total_pointers = sum(self.class_to_pointers.values())
