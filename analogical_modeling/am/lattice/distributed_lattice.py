"""weka.classifiers.lazy.AM.lattice
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

from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

from analogical_modeling.am.lattice.heterogeneous_lattice import HeterogeneousLattice
from analogical_modeling.am.lattice.canonicalizing_set import CanonicalizingSet
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.data.basic_supra import BasicSupra
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
from analogical_modeling.am.lattice.lattice import Lattice


class DistributedLattice(Lattice):
    """This lass manages several smaller, heterogeneous lattices. The
    supracontexts of smaller lattices are combined to create the final Supracontexts.
    """
    def __init__(self):
        self.supras: set[Supracontext] = set()
        self.filled: bool = False

    def get_supracontexts(self) -> set[Supracontext]:
        """

        :return: the list of homogeneous supracontexts created with this lattice
        """
        return self.supras

    def fill(self, sub_list: SubcontextList):
        """
        The number of sub-lattices is determined via Labeler.num_partitions()
        sub_list.get_labeler().num_partitions().

        :param sub_list: list of Subcontexts to add to the lattice
        :raises: ExecutionException If execution is rejected for some reason,
        :raises: InterruptedException If any thread is interrupted for any
        reason (user presses ctrl-C, etc.)
        """
        if self.filled:
            raise ValueError("Lattice is already filled and cannot be filled again.")
        self.filled = True
        if len(sub_list) == 0:
            return
        labeler = sub_list.get_labeler()
        num_lattices = labeler.num_partitions()

        with ThreadPoolExecutor() as executor:
            supras_futures = []
            for i in range(num_lattices):
                # fill each heterogeneous lattice with a given label partition
                partition_index = i
                future = executor.submit(self.fill_lattice_partition, sub_list, partition_index)
                supras_futures.append(future)

            # then combine them 2 at a time, consolidating duplicate supracontexts
            if num_lattices > 2:
                for _ in range(1, num_lattices - 1):
                    supras1 = supras_futures.pop(0).result()
                    supras2 = supras_futures.pop(0).result()
                    future = executor.submit(self.lattice_product, supras1, supras2, IntermediateProduct)
                    supras_futures.append(future)

            # the final combination creates ClassifiedSupras and ignores the heterogeneous ones.
            self.supras = self.lattice_product(supras_futures.pop(0).result(), supras_futures.pop(0).result(), FinalizingProduct)

    @staticmethod
    def fill_lattice_partition(sub_list: SubcontextList, partition_index: int) -> CanonicalizingSet:
        """Fills a heterogeneous lattice with subcontexts using the given label partition index."""
        lattice = HeterogeneousLattice(partition_index)
        lattice.fill(sub_list)
        return lattice.get_supracontexts()

    def lattice_product_accumulate(self, supras1: list[Supracontext], supras2: list[Supracontext], supra_product_constructor) -> set[Supracontext]:
        items1: list[tuple[frozenset, int, Supracontext]] = []
        items2: list[tuple[frozenset, int, Supracontext]] = []
        for supra in supras1:
            data_fs = frozenset(supra.get_data())
            items1.append((data_fs, supra.get_count(), supra))
        for supra in supras2:
            data_fs = frozenset(supra.get_data())
            items2.append((data_fs, supra.get_count(), supra))

        # Choose smaller outer loop
        if len(items2) < len(items1):
            items1, items2 = items2, items1

        # accumulate: key -> accumulated count (sum of products)
        accum: dict[frozenset, int] = defaultdict(int)

        for data1, count1, _ in items1:
            for data2, count2, _ in items2:
                inter = data1.intersection(data2)
                if not inter:
                    continue
                accum[frozenset(inter)] += (count1 * count2)

        if not accum:
            return CanonicalizingSet.empty_set()

        # Build final CanonicalizingSet (create appropriate object per intersection)
        final_set = CanonicalizingSet()
        # choose product constructor type to create the right object for each key
        is_final = ((supra_product_constructor is FinalizingProduct)
                    or isinstance(supra_product_constructor, FinalizingProduct))
        for inter_fs, total_count in accum.items():
            # create minimal supracontext object depending on product type
            if is_final:
                # create ClassifiedSupra and check heterogeneity/empty as FinalizingProduct would
                supra = ClassifiedSupra()
                for sub in inter_fs:
                    supra.add(sub)
                    if supra.is_heterogeneous():
                        supra = None
                        break
                if supra is None or supra.is_empty():
                    continue
                supra.set_count(total_count)
                final_set.merge(supra, lambda s1, s2: s1.set_count(s1.get_count() + s2.get_count()) or s1)
            else:
                # Intermediate / BasicSupra: keep BasicSupra with summed count
                new_supra = BasicSupra(set(inter_fs), total_count)
                final_set.merge(new_supra, lambda s1, s2: s1.set_count(s1.get_count() + s2.get_count()) or s1)

        return final_set

    def lattice_product(self, supras1: set[Supracontext], supras2: set[Supracontext], supra_product_constructor) -> set[Supracontext]:
        """
        Combines two sets of Supracontexts to make a new List representing the
        intersection of two lattices. The lattice-combining step is partitioned
        and run in several threads.

        :param supra_product_constructor: the constructor of the task which will
        produce the product of one supracontext with a set of supracontexts
        """
        results = []

        with ThreadPoolExecutor() as executor:
            futures = [executor.submit(supra_product_constructor(), supra, supras2)
                       for supra in supras1]
            for future in as_completed(futures):
                results.append(future.result())

        if results:
            combined = results[0]
            for r in results[1:]:
                combined = self.remove_duplicate_results(combined, r)
            return combined
        return CanonicalizingSet.empty_set()

    @staticmethod
    def remove_duplicate_results(supras1: CanonicalizingSet, supras2: CanonicalizingSet):
        """
        Find duplicate supracontexts in supras1 and supras2 and return a single set of supracontexts
	    with the combined counts from both sets.
	    """
        # make sure supras2 is the smaller set of supracontexts, since we will iterate over it
        if len(supras2) > len(supras1):
            supras1, supras2 = supras2, supras1
        for supra in supras2:
            # add to the existing count if the same supra was formed from a
            # previous combination
            supras1.merge(supra, lambda s1, s2: s1.set_count(s1.get_count() + s2.get_count()) or s1)
        return supras1


class IntermediateProduct:
    def __call__(self, supra1: Supracontext, supras2: set[Supracontext]) -> CanonicalizingSet:  # replaces Java's compute
        combined_supras = CanonicalizingSet()
        for supra2 in supras2:
            new_supra = self.product(supra1, supra2)
            if new_supra is not None:
                # add to the existing count if the same supra was formed from a
                # previous combination
                combined_supras.merge(new_supra, lambda s1, s2: s1.set_count(s1.get_count() + s2.get_count()) or s1)

        return combined_supras

    def product(self, supra1: Supracontext, supra2: Supracontext) -> BasicSupra|None:
        """
        Combine this partial supracontext with another to make a third which
        contains the subcontexts in common between the two, and a count which is
        set to the product of the two counts. Return None if the resulting object
        would have no subcontexts.

        :param supra1: first partial supracontext to combine
        :param supra2: econd partial supracontext to combine
        :return: A new partial supracontext, or None if it would have been empty.
        """
        if len(supra1.get_data()) > len(supra2.get_data()):
            larger = supra1.get_data()
            smaller = supra2.get_data()
        else:
            larger = supra2.get_data()
            smaller = supra1.get_data()
        combined_subs = set(smaller)
        combined_subs.intersection_update(larger)

        if not combined_subs:
            return None
        return BasicSupra(combined_subs, supra1.get_count() * supra2.get_count())


class FinalizingProduct:
    def __call__(self, supra1: Supracontext, supras2: set[Supracontext]) -> CanonicalizingSet:
        final_supras = CanonicalizingSet()

        for supra2 in supras2:
            supra = self.product(supra1, supra2)
            if supra is None:
                continue
            # add to the existing count if the same supra was formed from a
            # previous combination
            final_supras.merge(supra, lambda s1, s2: s1.set_count(s1.get_count() + s2.get_count()) or s1)

        return final_supras

    def product(self, supra1: Supracontext, supra2: Supracontext) -> ClassifiedSupra|None:
        """
        Combine this partial supracontext with another to make a
        ClassifiedSupra object. The new one contains the subcontexts
        found in both, and the pointer count is set to the product of the two
        pointer counts. If it turns out that the resulting supracontext would be
        heterogeneous or empty, then return None instead.

        :param supra1: first partial supracontext to combine
        :param supra2: second partial supracontext to combine
        :return: a combined supracontext, or None if supra1 and supra2 had no
        data in common or if the new supracontext is heterogeneous
        """
        if len(supra1.get_data()) > len(supra2.get_data()):
            larger = supra1.get_data()
            smaller = supra2.get_data()
        else:
            larger = supra2.get_data()
            smaller = supra1.get_data()

        supra = ClassifiedSupra()

        for sub in smaller:
            if sub in larger:
                supra.add(sub)
                if supra.is_heterogeneous():
                    return None

        if supra.is_empty():
            return None
        supra.set_count(supra1.get_count() * supra2.get_count())
        return supra
