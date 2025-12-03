"""Analogical Modeling Algorithm

Implements the Analogical Modeling algorithm, invented by Royal Skousen.
Analogical modeling is an instance-based algorithm designed to model human
behavior.
"""

import argparse
import os
import sys
from pathlib import Path
from random import Random

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from tqdm import tqdm

am_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(am_path, '..'))
from analogical_modeling.am.data.am_results import AMResults
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.am.label.missing_data_compare import \
    MissingDataCompare
from analogical_modeling.am.lattice.lattice_factory import \
    CardinalityBasedLatticeFactory
from analogical_modeling.utils import Instance, Dataset


class HeaderMissmatchError(Exception):
    """Exception if headers don't match.'"""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AnalogicalModeling:
    """Analogical modeling algorithm."""

    def __init__(self):
        # The training instances used for classification.
        self.training_instances: Dataset = None
        # The training exemplars used for classification.
        self.training_exemplars: list[Instance] = []
        # The number of attributes.
        self.cardinality: int = 0
        # The Constant serialVersionUID.
        self.__serial_version_uid = 1212462913157286103
        self.mdc = MissingDataCompare.VARIABLE
        self.random_provider: Random | None = None

        # instances with a weight below this threshold will be ignored
        self.threshold = None

        # The analogical set from the last call to distributionForInstance
        self.results: AMResults = None

        # option storage variables
        # By default, we use quadratic calculation of pointer values.
        self.linear_count = False
        self.ignore_unknowns = False
        # By default, we remove any exemplar with the same features as the
        # test exemplar
        self.remove_test_exemplar = True
        # whether to drop duplicate entries
        self.drop_duplicates = False
        # indices of columns to ignore
        self.ignore_columns = []

        # debugging
        self.debug = False

    def get_linear_count(self):
        """

        :return: True if counting of pointers is linear; False if quadratic.
        """
        return self.linear_count

    def set_linear_count(self, linear: bool):
        """

        :param linear: True if counting of pointers should be linear; false
        if quadratic.
        :return:
        """
        self.linear_count = linear

    def get_ignore_unknowns(self) -> bool:
        return self.ignore_unknowns

    def set_ignore_unknowns(self, ignore_unknowns: bool):
        self.ignore_unknowns = ignore_unknowns

    def get_remove_test_exemplar(self) -> bool:
        """

        :return: True if we remove a test instance from training before
        predicting its outcome
        """
        return self.remove_test_exemplar

    def set_remove_test_exemplar(self, remove_test_exemplar: bool):
        """

        :param remove_test_exemplar: True if we should remove a test instance
        from training before predicting its outcome
        :return:
        """
        self.remove_test_exemplar = remove_test_exemplar

    def get_drop_duplicates(self) -> bool:
        return self.drop_duplicates

    def set_drop_duplicates(self, drop_duplicates: bool):
        self.drop_duplicates = drop_duplicates

    def get_ignore_columns(self) -> list[str]:
        return self.ignore_columns

    def set_ignore_columns(self, ignore_list: list[str]):
        self.ignore_columns = ignore_list

    def set_threshold(self, threshold: float | None):
        if threshold is None:
            self.threshold = None
            return
        self.threshold = max(threshold, 0.0)  # no negative thresholds

    def get_threshold(self) -> float | None:
        return self.threshold

    def classify(self, test_item: Instance) -> AMResults:
        """
        This method is where all of the action happens! Given a test item,
        it uses existing exemplars to assign outcome probabilities to it.

        Note that this method sets the results variable without any
        synchronization.
        This means that if you want to print results from multiple calls
        to this method, you should not call it in parallel. If you want
        to make multiple classify() calls in parallel, you should
        create multiple classifier instances. This sort of parallelism
        for large-cardinality datasets is inadvisable, anyway, since a
        single classifier instance will attempt to saturate all of the
        available CPUs.

        :param test_item: Item to make context base on
        :return: Analogical set which holds results of the classification
        for the given item
        :raises: RuntimeError if execution is rejected for some reason
        # @throws InterruptedException If any thread is interrupted for
        any reason (user presses ctrl-C, etc.)
        """
        if self.debug:
            print(f"Classifying {test_item}")
        labeler = Labeler(test_item, self.ignore_unknowns, self.mdc)

        # 3 steps to assigning outcome probabilities:

        # 1. Place each data item in a subcontext
        sub_list = SubcontextList(labeler, self.training_exemplars,
                                  self.get_remove_test_exemplar())

        # 2. Create a supracontextual lattice and fill it with subcontexts
        lattice_factory = CardinalityBasedLatticeFactory(
            sub_list.get_cardinality(),
            sub_list.labeler.num_partitions(),
            self.random_provider)

        lattice = lattice_factory.create_lattice()
        lattice.fill(sub_list)

        # 3. record the analogical set and other statistics from the pointers
        # in the resulting homogeneous supracontexts
        # we save the results for use with AnalogicalModelingOutput
        return AMResults(lattice, sub_list, test_item, self.linear_count,
                         labeler)

    def get_missing_data_compare(self):
        """

        :return: Selected strategy used when comparing missing values with
        other data
        """
        return self.mdc.name
        # return SelectedTag(self.mdc.ordinal(), TAGS_MISSING)

    def set_missing_data_compare(self, new_mode: str):
        """Return method to deal with missing data"""
        match new_mode:
            case "match":
                self.mdc = MissingDataCompare.MATCH
            case "mismatch":
                self.mdc = MissingDataCompare.MISMATCH
            case _:
                self.mdc = MissingDataCompare.VARIABLE

    def set_random_provider(self, random_provider: Random):
        """Provide the source of randomness for algorithms that require it
        (e.g. JohnsenJohanssonLattice).

        The provider must be thread-safe."""
        self.random_provider = random_provider

    def get_options(self):
        """Return options of the algorithm"""
        return f"Linear: {self.linear_count}, " \
               f"Remove test exemplars: {self.remove_test_exemplar}, " \
               f"Ignore unknown values: {self.ignore_unknowns}, " \
               f"Missing data: {self.mdc.option_string}\n" \
               f"Drop duplicates: {self.drop_duplicates}, " \
               f"Ignore columns: {self.ignore_columns or '--'}"

    def build_classifier(self, instances: Dataset):
        """This is used to build the classifier; it specifies the
        capabilities of the classifier and loads in exemplars to be used for
        prediction. No actual analysis happens here because AM is a lazy
        classifier."""

        # remove instances with missing class value,
        instances.delete_with_missing_class()

        self.cardinality = instances.num_counted_attributes()
        # save instances for checking headers
        self.training_instances = instances  # , 0, instances.num_attributes())

        # create exemplars for actually running the classifier
        self.training_exemplars = list(instances)

    def update_classifier(self, instance: Instance):
        """This is used to add more information to the classifier."""
        self.check_header(instance)

        if instance.is_missing(instance.get_class_index()):
            return
        self.training_instances.add(instance)
        self.training_exemplars.append(instance)
        if self.debug:
            print(f"Added instance: {instance}")

    def distribution_for_instance(self, instance: Instance) -> dict[str, float]:
        """Calculate class distribution for instance

        :param instance: instance to predict
        :return: mapping between classes and their selection probability for
        the instance
        """
        # self.check_header(instance)

        if len(self.training_instances) == 0:
            raise RuntimeError("No training instances!")

        if self.training_instances.num_classes() == 1:
            if self.debug:
                print("Training data have only one class")
            # 100 percent likelihood of belonging to the one class
            return {self.training_instances[0].class_value(): 1.0}

        self.results = self.classify(instance)
        return self.results.get_class_likelihood()

    def get_results(self) -> AMResults:
        """

        :return: The classification results from the last call to
        distribution_for_instance
        :raises RuntimeError if you've never called distribution_for_instance
        from this object
        """
        if self.results is None:
            raise RuntimeError(
                "Call distributionForInstance before calling this")
        return self.results

    @staticmethod
    def to_summary_string() -> str:
        """Return summary"""
        return "Analogical Modeling module (2021) by Nathan Glenn"

    def __str__(self) -> str:
        """

        :return: String containing name of the classifier and number of
        training instances.
        """
        string = "Analogical Modeling Classifier (2021 Nathan Glenn)\n"
        if self.training_exemplars:
            return string + (f"Training instances: "
                             f"{len(self.training_exemplars)}\n")
        return string

    def run_classifier(self, csv: str, out_path: Path, test: str, weights: str):
        """runs the classifier instance with the given options.

        :param csv: lexicon
        :param out_path: where to save output files
        :param test: test data (use lexicon if not given)
        :param weights: column name for weights in dataset, if given
        """
        instances = Dataset().from_csv(csv, weights)
        if self.threshold is not None:
            instances.filter_threshold(self.threshold)

        instances.set_ignored(self.ignore_columns)
        if self.drop_duplicates:
            instances.data.drop_duplicates(inplace=True)
        self.build_classifier(instances)

        # use test set, if available
        if test:
            instances = Dataset().from_csv(test)
            instances.set_ignored(self.ignore_columns)
            self.check_header(instances)

        results = []
        total = len(instances)
        for i in tqdm(range(total), desc="Classifying instances",
                      colour="green", leave=False):
            self.distribution_for_instance(instances[i])
            results.append(self.get_results())

        acc, conf_matrix = self.evaluate(instances, results)
        print(f"Accuracy: {round(acc * 100, 3)}%")
        self.create_output_files(out_path, results, instances)
        conf_matrix.plot()
        plt.show()

    def create_output_files(self, dest: Path, results: list[AMResults],
                            instances: Dataset) -> None:
        """Store information on analogical sets, gang effects and distributions

        :param dest: start name for output files
        :param results: list of AMResults
        :param instances: dataset used for prediction
        """
        print("Generating output files...")
        # information equal for all exemplars
        feats = results[0].classified_exemplar.real_data.keys()
        classes = list(instances.get_classes())
        cls_header = ([f"Class {i + 1}" for i in range(len(classes))] +
                      sum([[f"{cls}: pointers", f"{cls}: pct"] for cls in
                           classes], []))
        cls_header_gang = sum(
            [[f"{cls}: pointers", f"{cls}: pct", f"{cls}: size"] for cls in
             classes], [])
        num_feats = instances.num_attributes() - 1  # - class attribute
        ignore = self.ignore_unknowns
        mdc = self.mdc.name
        ignore_given = self.remove_test_exemplar
        count_strategy = "linear" if self.linear_count else "quadratic"

        gang_header = (feats.tolist() + ["Weight"] + cls_header_gang +
                       ["Gang pointers", "Gang pct", "Rank", "Size",
                        "Total pointers", "Classified item index",
                        "Classified item class"] +
                       [f"Classified item {el}" for el in feats])
        analog_header = (feats.tolist() +
                         ["Weight", "Class", "Percentage", "Pointers",
                          "Classified item index", "Classified item class"] +
                         [f"Classified item {el}" for el in feats])
        distr_header = (
                ["Judgement", "Expected", "Predicted"] + feats.tolist() +
                cls_header +
                ["Train size", "Num feats", "Ignore unknown values",
                 "Missing data compare", "Ignore given",
                 "Count strategy", "Classified item index"])

        gangs = []
        analogs = []
        distributions = []
        for idx, res in enumerate(results):
            classified = res.classified_exemplar

            # gang effects
            effects = res.get_gang_effects()
            total_pointers = sum(effect.total_pointers for effect in effects)
            pointers_rank = sorted(
                list(set(effect.total_pointers for effect in effects)),
                reverse=True
            )
            for effect in effects:
                effect_pointers = effect.total_pointers
                rank = pointers_rank.index(effect_pointers) + 1
                gang_pct = effect_pointers / total_pointers * 100

                cls_info = {inst: sum([
                    [effect.class_to_pointers.get(cls, 0),  # cls: pointers
                     round(effect.class_to_pointers.get(cls,
                                                        0) / effect_pointers
                           * gang_pct,
                           3),  # cls: pct
                     len(effect.class_to_instances.get(cls, []))  # cls: size
                     ] if inst in effect.class_to_instances.get(cls, []) else [
                        0, 0, 0]
                    for cls in classes
                ], []) for inst in effect.subcontext.data}

                gangs += [
                    inst.real_data.tolist() + [inst.weight] + cls_info[inst] + [
                        effect_pointers,  # gang pointers
                        round(gang_pct, 3),  # gang pct
                        rank,  # rank
                        sum(map(len, effect.class_to_instances.values())),
                        # size
                        total_pointers,  # total pointers
                        idx,  # classified item index
                        classified.class_value()  # classified item class
                    ] + classified.real_data.tolist()
                    for inst in
                    sum(map(list, effect.class_to_instances.values()), [])]

            # analogical sets
            pointers = res.ex_pointer_map
            effects = res.ex_effect_map
            analogs += [
                inst.real_data.to_list() + [
                    inst.weight,  # weight
                    inst.class_value(),  # class
                    effects.get(inst) * 100,  # percentage
                    ptrs,  # pointers
                    idx,  # index
                    classified.class_value()  # instance class
                ] + classified.real_data.tolist() for inst, ptrs in
                pointers.items()]

            # distribution
            pred = res.predicted_classes
            gold = res.get_expected_class_name()
            train_size = res.sub_list.considered_exemplar_count

            cls_info = classes + sum([[
                res.class_pointer_map.get(cls, 0),  # cls: pointers
                res.class_likelihood_map.get(cls, 0.0) * 100]  # cls: pct
                for cls in classes], [])
            distributions += [
                [res.get_judgement().value,  # judgement
                 gold,  # expected
                 '|'.join(pred)  # predicted
                 ] + classified.real_data.tolist() + cls_info + [
                    train_size,  # train size
                    num_feats,  # num feats
                    ignore,  # ignore unknown values
                    mdc,  # missing data compare
                    ignore_given,  # ignore given
                    count_strategy,  # count strategy
                    idx  # index
                ]]

        gang = pd.DataFrame(gangs, columns=gang_header)
        analog = pd.DataFrame(analogs, columns=analog_header)
        distr = pd.DataFrame(distributions, columns=distr_header)

        out_gang = dest.with_name(dest.stem + "_gangs.csv")
        out_analog = dest.with_name(dest.stem + "_analogical_sets.csv")
        out_distribution = dest.with_name(dest.stem + "_distributions.csv")

        if not dest.parent.exists():
            dest.parent.mkdir(parents=True)

        gang.to_csv(out_gang, index=False)
        analog.to_csv(out_analog, index=False)
        distr.to_csv(out_distribution, index=False)
        print(f"Outputs saved to {out_gang}, {out_analog}, {out_distribution}.")

    @staticmethod
    def evaluate(instances: Dataset, results: list[AMResults]) -> tuple[
        float, ConfusionMatrixDisplay]:
        """Calculate accuracy and plot confusion matrix

        :param instances: dataset used for prediction
        :param results: list of AMResults
        :return: accuracy
        """
        # inaccurate in the case of ties
        preds = [list(res.predicted_classes)[0] for res in results]
        golds = [inst.class_value() for inst in instances]

        correct = sum(
            [inst.class_value() in res.predicted_classes
             for inst, res in zip(instances, results)])
        acc = correct / len(results)
        cnf = confusion_matrix(golds, preds,
                               labels=list(instances.get_classes()))
        disp = ConfusionMatrixDisplay(cnf, display_labels=list(
            instances.get_classes()))

        return acc, disp

    def check_header(self, instances):
        """Headers of lexicon and test data must be equal"""
        l_header = self.training_instances.data.columns.tolist()
        t_header = instances.data.columns.tolist()
        if t_header != l_header:
            raise HeaderMissmatchError(
                f"Expected header is {l_header}, but test data header is "
                f"{t_header}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lexicon", type=Path,
                        help="csv containing the data", required=True)
    parser.add_argument("-t", "--test",
                        help="csv containing test data")
    parser.add_argument("-o", "--output",
                        help="output path", type=Path, required=True)
    parser.add_argument("-w", "--weight_colum",
                        help="name of column for weights")
    parser.add_argument("-th", "--threshold", type=float,
                        help="lower threshold for instance weights",
                        default=None)
    parser.add_argument("-d", "--drop_duplicates",
                        action="store_true", help="Drop duplicated instances")
    parser.add_argument("--ignore_columns", nargs="*",
                        help="Columns to ignore", type=str, default=[])
    parser.add_argument("-L", "--linear", action="store_true")
    parser.add_argument("-K", "--keep_test", action="store_false",
                        help="Keep test exemplar in training set (default: "
                             "False)")  # !keep_test = remove, which is default
    parser.add_argument("-I", "--ignore_unknowns", action="store_true",
                        help="Ignore attributes with unknown values in the "
                             "test exemplar")
    parser.add_argument("-D", "--debug", action="store_true",
                        help="Run classifier in debug mode; may output "
                             "additional info to the console")
    parser.add_argument("-M", "--missing_data",
                        choices=["match", "mismatch", "variable"],
                        default="variable",
                        help="Method of dealing with missing data. The options "
                             "are 'variable', 'match' or 'mismatch'; "
                             "'variable' means to treat missing data as a all "
                             "one variable, 'match' means that missing data "
                             "will be considered the same as whatever it is "
                             "compared with, and 'mismatch' means that "
                             "missing data will always be unequal to "
                             "whatever it is compared with. Default is "
                             "'variable'")

    args = parser.parse_args()

    # validation
    if not args.lexicon.exists():
        sys.exit(f"File {args.lexicon} not found.")
    if args.test and not Path(args.test).exists():
        sys.exit(f"Test file given, but {args.test} not found.")

    am = AnalogicalModeling()
    am.set_linear_count(args.linear)
    am.set_remove_test_exemplar(args.keep_test)
    am.set_ignore_unknowns(args.ignore_unknowns)
    am.debug = args.debug
    am.set_missing_data_compare(args.missing_data)
    am.set_drop_duplicates(args.drop_duplicates)
    am.set_ignore_columns(args.ignore_columns)
    am.set_threshold(args.threshold)
    am.run_classifier(args.lexicon, args.output.with_suffix(".csv"), args.test,
                      args.weight_colum)
