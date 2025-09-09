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

from analogical_modeling.am.lattice.heterogeneous_lattice import HeterogeneousLattice
from analogical_modeling.am.lattice.canonicalizing_set import CanonicalizingSet
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.data.basic_supra import BasicSupra
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
from analogical_modeling.am.lattice.lattice import Lattice
from analogical_modeling.am.label.labeler import Labeler


class DistributedLattice(Lattice):
    """This lass manages several smaller, heterogeneous lattices. The
    supracontexts of smaller lattices are combined to create the final Supracontexts.

    @author Nathan Glenn
    """
    def __init__(self):
        # super.__init__(self)
        self.supras: set[Supracontext] = set()
        self.filled: bool = False

    def get_supracontexts(self) -> set[Supracontext]:
        """

        :return: the list of homogeneous supracontexts created with this lattice
        """
        return self.supras

    def distributed_lattice(self):
        pass

    def fill(self, sub_list: SubcontextList):
        """
        The number of sub-lattices is determined via Labeler.num_partitions() sub_list.get_labeler().num_partitions().

        :param sub_list: list of Subcontexts to add to the lattice
        :raises: ExecutionException If execution is rejected for some reason,
        :raises: InterruptedException If any thread is interrupted for any reason (user presses ctrl-C, etc.)
        """
        if self.filled:
            raise ValueError("Lattice is already filled and cannot be filled again.")
        self.filled = True
        if not sub_list:
            return
        labeler = sub_list.get_labeler()
        num_lattices = labeler.num_partitions()

        supras_futures = []
        with ThreadPoolExecutor() as executor:
            for partition_index in range(num_lattices):
                # fill each heterogeneous lattice with a given label partition
                future = executor.submit(self.fill_lattice_partition, sub_list, partition_index)
                supras_futures.append(future)

            results = []
            for future in as_completed(supras_futures):
                results.append(future.result())

            # then combine them 2 at a time, consolidating duplicate supracontexts
            if num_lattices > 2:
                intermediate_futures = []
                for i in range(1, num_lattices - 1):
                    supras1 = results.pop()
                    supras2 = results.pop()
                    future = executor.submit(self.lattice_product, supras1, supras2, IntermediateProduct)
                    intermediate_futures.append(future)
            for future in as_completed(supras_futures):
                results.append(future.result())

            # the final combination creates ClassifiedSupras and ignores the heterogeneous ones.
            self.supras = self.lattice_product(results.pop(), results.pop(), FinalizingProduct)

    @staticmethod
    def fill_lattice_partition(sub_list: SubcontextList, partition_index: int) -> set[Supracontext]:
        """Fills a heterogeneous lattice with subcontexts using the given label partition index."""
        lattice = HeterogeneousLattice(partition_index)
        lattice.fill(sub_list)
        return lattice.get_supracontexts()

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
            futures = [executor.submit(supra_product_constructor, supra, supras2) for supra in supras1]
            for future in as_completed(futures):
                results.append(future.result())

        if results:
            combined = results[0]
            for r in results[1:]:
                combined = self.remove_duplicate_results(combined, r)
            return combined
        else:
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
    def __init__(self, supra1: Supracontext, supras2: set[Supracontext]):
        self.supra1 = supra1
        self.supras2 = supras2

    def __call__(self) -> CanonicalizingSet:  # replaces Java's compute
        combined_supras = CanonicalizingSet()
        for supra2 in self.supras2:
            new_supra = self.product(self.supra1, supra2)
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


# Got it 👍 — in Java you have something like:
#
# java
#
# class FinalizingProduct extends RecursiveTask<CanonicalizingSet<Supracontext>> {
#     // implementation...
# }
#
# That’s a ForkJoin RecursiveTask which runs in parallel and returns a CanonicalizingSet<Supracontext>.
#
# In Python, there’s no RecursiveTask, but since we already mapped your concurrency to concurrent.futures, the closest equivalent is just a callable class (or function) that returns a CanonicalizingSet.
#
# Here’s the skeleton translation:
#
# python
#
# class FinalizingProduct:
#     def __init__(self, supra: "Supracontext", supras: "CanonicalizingSet[Supracontext]"):
#         self.supra = supra
#         self.supras = supras
#
#     def __call__(self) -> "CanonicalizingSet[Supracontext]":
#         """
#         Equivalent to compute() in Java's RecursiveTask.
#         Should return a CanonicalizingSet[Supracontext].
#         """
#         # TODO: implement the actual lattice-finalizing logic
#         result = CanonicalizingSet()
#         # Example: maybe process self.supra and merge into result
#         # result.merge(self.supra, lambda s1, s2: ...)
#         return result
#
# 🔑 Key points:
#
#     In Java, compute() is the main method of RecursiveTask.
#     In Python, making the class callable (__call__) allows us to use it with executor.submit(FinalizingProduct(...)).
#     That means you don’t need to change the code in lattice_product, because Python will treat the class instance as a task.
#
# 👉 Do you want me to also create a parallel stub for IntermediateProduct in the same style, so both task types are ready to plug into your translated lattice code?
class FinalizingProduct:
    def __init__(self, supra1: Supracontext, supras2: set[Supracontext]):
        self.supra1 = supra1
        self.supras2 = supras2

    def __call__(self) -> CanonicalizingSet:
        final_supras = CanonicalizingSet()

        for supra2 in self.supras2:
            supra = self.product(self.supra1, supra2)
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
        :return: a combined supracontext, or None if supra1 and supra2 had no data in common or if the new
        supracontext is heterogeneous
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
