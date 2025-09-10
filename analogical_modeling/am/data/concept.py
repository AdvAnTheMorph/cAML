"""weka.classifiers.lazy.AM.data"""

from analogical_modeling.am.label.label import Label
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.data.subcontext import Subcontext


class Concept(Supracontext):
    """
    This class is a decorator which wraps a Supracontext and adds the
    functionality of a node (concept) used in the ImprovedAddIntent algorithm
    (see SparseLattice.
    # TODO: did this really need to be genericized? Won't you always use a classifiedSupra?
    """
    def __init__(self, intent: Label, extent: Supracontext):
        # wrapped supracontext
        self.intent: Label = intent
        self.extent: Supracontext = extent
        self.parents: set = set()
        self.tag: bool = False
        self.candidate_parent: Concept|None = None

    def get_extent(self):
        return self.extent.get_data()

    def get_supra(self):
        return self.extent

    def add_to_extent(self, new_sub: Subcontext):
        """Add the given subcontext to the extent of this concept."""
        self.extent.add(new_sub)

    def get_intent(self) -> Label:
        return self.intent

    def get_parents(self) -> frozenset:
        return frozenset(self.parents)

    def add_parent(self, new_parent):
        self.parents.add(new_parent)

    def remove_parent(self, old_parent):
        self.parents.remove(old_parent)

    def __repr__(self):
        return f"{self.intent}({self.extent})->[{self.parents}]"

    def copy(self):
        new_node = Concept(self.intent, self.extent.copy())
        new_node.parents = self.parents.copy()
        return new_node

    def __eq__(self, other):
        """
        This equals method differs from the specification in
        Supracontext.__eq__; it compares the concept intent
        (label), instead of the extent (contained subcontexts).
        """
        if self is other:
            return True
        if other is None:
            return False
        if not isinstance(other, Concept):
            return False
        return self.intent == other.intent

    def __hash__(self):
        """
        This implementation differs from the specification in
        Supracontext.__hash__; it returns the hash of the intent
        (label), instead of the extent (contained subcontexts).
        """
        return hash(self.intent)

    # the following methods forward to the contained Supracontext
    def get_data(self):
        return self.extent.get_data()

    def add(self, other):
        self.extent.add(other)

    def is_empty(self) -> bool:
        return self.extent.is_empty()

    def get_count(self):
        return self.extent.get_count()

    def set_count(self, count: int):
        self.extent.set_count(count)

    def get_context(self) -> Label:
        return self.intent

    def not_tagged(self) -> bool:
        return not self.tag

    def set_tagged(self, tag: bool):
        self.tag = tag

    def get_candidate_parent(self):
        return self.candidate_parent

    def set_candidate_parent(self, candidate_parent):
        self.candidate_parent = candidate_parent
