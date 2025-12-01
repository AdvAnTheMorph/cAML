"""Lattice Factory

Creates suitable lattice based on cardinality
"""

import random
from abc import ABC, abstractmethod
from typing import Optional

from analogical_modeling.am.lattice.lattice import Lattice
from analogical_modeling.am.lattice.johnsen_johansson_lattice import JohnsenJohanssonLattice
from analogical_modeling.am.lattice.distributed_lattice import DistributedLattice
from analogical_modeling.am.lattice.basic_lattice import BasicLattice


class LatticeFactory(ABC):
    """"Factory for creating Lattices."""

    @abstractmethod
    def create_lattice(self) -> Lattice:
        """

        :return: Lattice implementation
        """


class CardinalityBasedLatticeFactory(LatticeFactory):
    """Chooses the lattice implementation based on the cardinality of
	   the instances in the subcontext list."""
    def __init__(self, cardinality: int, num_partitions: int, random_provider: Optional[random.Random] = None):
        self.cardinality = cardinality
        self.num_partitions = num_partitions

        if random_provider is None:
            self.random_provider = lambda: random.Random(random.getrandbits(32))
        else:
            self.random_provider = random_provider

    def create_lattice(self) -> Lattice:
        """Create lattice based on cardinality."""
        if self.cardinality >= 50:
            return JohnsenJohanssonLattice(self.random_provider)
        if self.num_partitions > 1:
            # TODO: is it weird that the labeler determines the lattice implementation? Choosing the
            # number of partitions should not be the labeler's responsibility
            return DistributedLattice()
        return BasicLattice()
