r"""Johnsen-Johansson Lattice

The approximation algorithm from "Efficient Modeling of Analogy", Johnsen and
Johansson, DOI 10.1007/978-3-540-30586-6_77.

Terminology from the paper is as follows:

- :math:`p`: the subcontext whose count is being approximated
- :math:`size(p)`: the size of the subcontext :math:`p`; or, the number of 0's
  in its label
- :math:`\mathcal{H}(p)`: the sets found by intersecting :math:`p` with any
  subcontext that has a different outcome; the labels of such intersections
- :math:`max(p)`: the cardinality of the union of all :math:`x\in\mathcal{H}(p)`;
  the number of 0's in the union of the labels of all subcontexts in
  :math:`\mathcal{H}(p)`
- :math:`\mathcal{H}_{limit(p)}`: the heterogeneous elements under :math:`p`
  in the lattice
- :math:`min(p)`: the size of the largest child of :math:`p`; or, the number of
  0's in the label of the subcontext whose label has the most 0's and matches
  all the 1's in :math:`p`'s label.

We estimate the count of each subcontext by randomly unioning sets of
subcontexts from :math:`\{x_s\}` and checking for heterogeneity (union means
OR'ing labels). The count of a subcontext :math:`p` is the size of its power
set minus the heterogeneous elements in this set
(or :math:`|\wp(p)| - |\mathcal{H}_{limit(p)}|`).
We use these bounds in approximating :math:`|\mathcal{H}_{limit(p)}|`:

- lower bound (:math:`lb(p)`): the cardinality of the powerset of :math:`min(p)`.
- upper bound (:math:`ub(p)`): :math:`\sum_{k=1}^{min(p)}{max(p)\choose k}`

The estimate :math:`\hat{h}_p` of :math:`|\mathcal{H}_{limit(p)}|` is computed
by sampling random sets of subcontexts :math:`{x_s}` and combining them with:

:math:`\frac{|\{x_s \in \mathcal{H}(p)|}{|\{x_s\}|}=\frac{\hat{h}_p}{ub(p)}`

or

:math:`\hat{h}_p = \frac{ub(p)|x_s\in \mathcal{H}(p)|}{|\{x_s\}|}`


TODO: maybe if H(p) is small enough we could do exact counting with
      include-exclude
"""

import concurrent.futures
import random
from collections import defaultdict
from functools import lru_cache
from math import comb
from typing import Callable

from analogical_modeling.am import am_utils
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.lattice.lattice import Lattice

NUM_EXPERIMENTS = 10


class Pair:
    def __init__(self, first: int, second: int):
        self.first = first
        self.second = second

    def __hash__(self):
        return 37 * self.first + self.second

    def __eq__(self, other):
        return self.first == other.first and self.second == other.second


@lru_cache(maxsize=None)
def binomial_coefficient(p: Pair) -> int:
    """Calculate binomial coefficient."""
    n = p.first
    k = p.second
    if n == 0:
        return 1
    if k == 0:
        return 0
    # (n C k) and (n C (n-k)) are the same, so pick the smaller as k:
    k = min(k, n - k)
    return comb(n, k)


class SupraApproximator():
    """Approximator for Supracontexts"""

    def __init__(self, lattice: 'JohnsenJohanssonLattice', p: Subcontext,
                 outcome_sub_map: dict[float, list[Label]], rnd: random.Random):
        self.p = p
        self.outcome_sub_map = outcome_sub_map
        self.random = rnd
        self.jj_lattice = lattice

    def __call__(self) -> Supracontext:
        return self.approximate_supra(self.p, self.outcome_sub_map)

    def approximate_supra(self, p: Subcontext,
                          outcome_sub_map: dict[
                              float, list[Label]]) -> Supracontext:
        """Approximate supracontext."""
        p_label = p.label
        # H(p) is p intersected with labels of any subcontexts with a
        # different class, or all other sub labels if p is non-deterministic
        # (combination with these would lead to heterogeneity)
        hp = []
        for k, v in outcome_sub_map.items():
            if p.outcome != k or p.outcome == am_utils.HETEROGENEOUS:
                for x in v:
                    hp.append(p_label.intersect(x))

        # min(p) is the number of matches in the label in H(p) with the most
        # matches max(p) is the number of matches in the union of all labels
        # in H(p)
        min_p = 0
        hp_union: Label = p_label
        for l in hp:
            if l.num_matches() > min_p:
                min_p = l.num_matches()
            hp_union = hp_union.union(l)
        max_p = hp_union.num_matches()
        # the upper bound on H_limit(p)
        ub_p = 0
        for k in range(1, min_p + 1):
            ub_p += binomial_coefficient(Pair(max_p, k))
        # ratio of |{x_s in H(p)}| to |{x_s}|
        hetero_ratio: float = self.estimate_hetero_ratio(hp, hp_union,
                                                         NUM_EXPERIMENTS)
        # final estimation of total count of space subsumed by elements of
        # H(p); rounds down
        hetero_count_estimate = int(ub_p * hetero_ratio)
        # final count is 2^|p| - heteroCountEstimate
        count = 2 ** p_label.num_matches() - hetero_count_estimate

        # add the approximated sub as its own supra with the given count
        approximated_supra = ClassifiedSupra()
        approximated_supra.add(p)
        approximated_supra.count = count
        return approximated_supra

    def estimate_hetero_ratio(self, hp: list[Label], hp_union: Label,
                              num_experiments: int) -> float:
        """Estimate heterogeneous ratio."""
        hetero_count = 0
        cache: dict[Label, bool] = {}

        for _ in range(num_experiments):
            # choose x_s, a union of random items from H(p)
            xs: Label = self.jj_lattice.bottom
            random.shuffle(hp)
            for l in hp:
                # cannot use random.random() in parallel code
                if self.jj_lattice.random_provider().random() > 0.5:
                    # further union operations would do nothing since we are
                    # supposed to compare against hpUnion
                    unioned = xs.union(l)
                    if unioned == hp_union:
                        break
                    xs = unioned
            was_hetero = cache.get(xs)
            if was_hetero is not None:
                if was_hetero:
                    hetero_count += 1
                continue

            # x_s is hetero if it is a child of any element of H(p)
            hetero = False
            for l in hp:
                # use union to discover ancestor relationship
                if l.union(xs) == l:
                    hetero_count += 1
                    hetero = True
                    break
            cache[xs] = hetero
        return hetero_count / num_experiments


class JohnsenJohanssonLattice(Lattice):
    """Lattice for high cardinality data."""
    def __init__(self, random_provider: Callable[[], random.Random]):
        """

        :param random_provider: provides randomness used for performing Monte
            Carlo simulation in child threads
        """
        # TODO: should run until convergence, not a constant number of times
        self.supras = set()
        self.filled = False
        self.bottom: Label = None
        self.random_provider = random_provider

    def fill(self, sub_list: SubcontextList) -> None:
        """Fill the lattice with given subcontexts. This is meant to be done
        only once for a given Lattice instance.

        :raises ValueError: if the lattice was already filled
        """
        if self.filled:
            raise ValueError(
                "Lattice is already filled and cannot be filled again.")
        self.filled = True
        self.bottom = sub_list.labeler.get_lattice_bottom()
        # first organize sub labels by outcome for quick H(p) construction
        outcome_sub_map: dict[float, list[Label]] = defaultdict(list)
        for s in sub_list:
            outcome_sub_map[s.outcome].append(s.label)

        # Estimate the counts for each supracontext in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(
                SupraApproximator(self, p, outcome_sub_map,
                                  self.random_provider()))
                for p in sub_list]

            for future in concurrent.futures.as_completed(futures):
                self.supras.add(future.result())

    def get_supracontexts(self) -> set:
        """

        :return: List of supracontexts that were created by filling the
            supracontextual lattice. From this, you can compute the analogical
            set.
        """
        return self.supras
