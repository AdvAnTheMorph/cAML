"""weka.classifiers.lazy.AM.lattice"""

from typing import Callable, TypeVar

T = TypeVar('T')


class CanonicalizingSet:
    """
    A set implementation that can be used to retrieve canonical versions of objects; this is not
    possible with Set because of the lack of a get method."""

    def __init__(self):
        # TODO: private static final CanonicalizingSet EMPTY_SET = new CanonicalizingSet<>(Collections.EMPTY_MAP);
        self.__backing_map: dict = {}

    @staticmethod
    def empty_set():
        return CanonicalizingSet()  # backing_mapp defaults to an empty dict

    def get(self, t):
        """

        :return: None if t is not contained in the set; otherwise the object contained in the set for which
	    t == theObject is true.
        """
        return self.__backing_map.get(t)

    def merge(self, t, remapping_function: Callable[[T, T], T]):
        """Key and value are the same, otherwise the same as Java's Map.merge"""
        if t in self.__backing_map:
            self.__backing_map[t] = remapping_function(self.__backing_map[t], t)
        else:
            self.__backing_map[t] = t

    def unwrap(self) -> set:
        """

        :return: the underlying set
        """
        return set(self.__backing_map.keys())

    def __len__(self) -> int:
        return len(self.__backing_map)

    def is_empty(self) -> bool:
        return len(self.__backing_map) == 0

    def __contains__(self, item) -> bool:
        return item in self.__backing_map

    def __iter__(self):
        return iter(self.__backing_map.keys())

    def add(self, obj) -> bool:
        self.__backing_map[obj] = obj
        return True
