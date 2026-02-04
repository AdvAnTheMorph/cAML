"""Analogical Modeling Algorithm

Implements the Analogical Modeling algorithm, invented by Royal Skousen.
Analogical modeling is an instance-based algorithm designed to model human
behavior.

:func:`AnalogicalModeling.run_classifier` starts the algorithm. It calls
:func:`AnalogicalModeling.classify` which does the actual classification.
"""

import argparse
import logging
import sys
from os import path, PathLike
from pathlib import Path
from random import Random
from typing import Iterable, Optional

import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay
from tqdm import tqdm

# necessary for accessing analogical_modeling
am_path = path.dirname(path.abspath(__file__))
sys.path.append(path.join(am_path, '..'))
from analogical_modeling.am.data.gang_effect import GangEffect
from analogical_modeling.am.data.am_results import AMResults
from analogical_modeling.am.data.subcontext_list import SubcontextList
from analogical_modeling.am.label.labeler import Labeler
from analogical_modeling.am.label.missing_data_compare import \
    MissingDataCompare
from analogical_modeling.am.lattice.lattice_factory import \
    CardinalityBasedLatticeFactory
from analogical_modeling.utils import Instance, Dataset, InvalidColumnError

logging.basicConfig(format="({asctime}) {name} {levelname}: {message}",
                    datefmt="%H:%M:%S", style="{", filename=".log")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class HeaderMismatchError(Exception):
    """Exception if headers don't match."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class AnalogicalModeling:
    """Implementation of the Analogical Modeling algorithm, invented by Royal
    Skousen.

    Analogical modeling is an instance-based algorithm designed to model human
    behavior.

    :func:`~AnalogicalModeling.run_classifier` starts the algorithm. It calls
    :func:`~AnalogicalModeling.classify` which does the actual classification.
    """

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
        self._threshold = None

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

        # used by GUI to cancel program
        self.cancel_event = False
        self.gui_queue = None

    def set_linear_count(self, linear: bool) -> None:
        """

        :param linear: True if counting of pointers should be linear; false
            if quadratic
        """
        self.linear_count = linear

    def set_ignore_unknowns(self, ignore_unknowns: bool) -> None:
        self.ignore_unknowns = ignore_unknowns

    def set_remove_test_exemplar(self, remove_test_exemplar: bool) -> None:
        """

        :param remove_test_exemplar: True if we should remove a test instance
            from training before predicting its outcome
        """
        self.remove_test_exemplar = remove_test_exemplar

    def set_drop_duplicates(self, drop_duplicates: bool) -> None:
        self.drop_duplicates = drop_duplicates

    def set_ignore_columns(self, ignore_list: list[str]) -> None:
        self.ignore_columns = ignore_list

    @property
    def threshold(self) -> tuple[float, bool]:
        """Get minimum weight threshold for instances to be considered."""
        return self._threshold

    @threshold.setter
    def threshold(self, threshold: tuple[float, bool]) -> None:
        self.set_threshold(*tuple(threshold))

    def set_threshold(self, th: float | None, inclusive: bool = False):#, max_th: Optional[float] = None, max_include: bool = False) -> None:
        """Set upper and lower threshold.

        :param th: lower threshold
        :param inclusive: whether lower threshold should be inclusive
        # :param max_th: upper threshold
        # :param max_include: whether upper threshold should be inclusive
        """
        if th is None:# and max_th is None:
            self._threshold = None
            return
        self._threshold = (max(th, 0.0), inclusive)
        # threshold = [th, include, max_th, max_include]
        #
        # # no negative thresholds
        # if th is not None:
        #     threshold[0] = max(th, 0.0)
        # if max_th is not None:
        #     threshold[2] = min(0.0, max_th)
        # self._threshold = tuple(threshold)

    def set_missing_data_compare(self, new_mode: str) -> None:
        """Set method to deal with missing data."""
        match new_mode:
            case "match":
                self.mdc = MissingDataCompare.MATCH
            case "mismatch":
                self.mdc = MissingDataCompare.MISMATCH
            case _:
                self.mdc = MissingDataCompare.VARIABLE

    def set_random_provider(self, random_provider: Random) -> None:
        """Provide the source of randomness for algorithms that require it
        (e.g. :py:class:`JohnsenJohanssonLattice`).

        The provider must be thread-safe."""
        self.random_provider = random_provider

    def get_options(self) -> str:
        """Return options of the algorithm."""
        return f"Linear: {self.linear_count}, " \
               f"Remove test exemplars: {self.remove_test_exemplar}, " \
               f"Ignore unknown values: {self.ignore_unknowns}, " \
               f"Missing data: {self.mdc.option_string}\n" \
               f"Drop duplicates: {self.drop_duplicates}, " \
               f"Ignore columns: {self.ignore_columns or '--'}"

    def check_header(self, instances) -> None:
        """Headers of lexicon and test data must be equal.

        Ignored columns are ignored both in lexicon and test data.

        :raises HeaderMismatchError: if headers don't match
        """
        class_column = self.training_instances.class_column_name()
        l_header = self.training_instances.data.columns.tolist()
        t_header = instances.data.columns.tolist()

        # remove ignored columns,
        # don't consider class column (might not be specified in test data)
        ignored = self.ignore_columns + [class_column]
        l_header = list(filter(lambda x: x not in ignored, l_header))
        t_header = list(filter(lambda x: x not in ignored, t_header))

        if t_header != l_header:
            raise HeaderMismatchError(
                f"Expected header is {l_header}, but test data header is "
                f"{t_header}")

    # actual classification part
    def classify(self, test_item: Instance) -> AMResults:
        """
        This method is where all the action happens! Given a test item,
        it uses existing exemplars to assign outcome probabilities to it.

        Note that this method sets the results variable without any
        synchronization.
        This means that if you want to print results from multiple calls
        to this method, you should not call it in parallel. If you want
        to make multiple :func:`classify` calls in parallel, you should
        create multiple classifier instances. This sort of parallelism
        for large-cardinality datasets is inadvisable, anyway, since a
        single classifier instance will attempt to saturate all available CPUs.

        :param test_item: item to make context base on
        :return: Analogical set which holds results of the classification
            for the given item
        """
        logger.debug(f"Classifying {test_item}")
        labeler = Labeler(test_item, self.ignore_unknowns, self.mdc)

        # 3 steps to assigning outcome probabilities:

        # 1. Place each data item in a subcontext
        sub_list = SubcontextList(labeler, self.training_exemplars,
                                  self.remove_test_exemplar)

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

    def run_classifier(self, csv: PathLike | pd.DataFrame,
                       out_path: Optional[Path], test: str,
                       weights: str, sheet: str = None, test_sheet: str = None) -> tuple[
        Optional[float], Optional[ConfusionMatrixDisplay], tuple]:
        """Run the classifier instance with the given options.

        :param csv: lexicon
        :param out_path: where to save output files
        :param test: test data (use lexicon if not given)
        :param weights: column name for weights in dataset, if given
        :raises InvalidColumnError: if column configuration invalid
        :raises HeaderMismatchError: if headers don't match
        """
        if weights in self.ignore_columns:
            raise InvalidColumnError(
                f"Weights column '{weights}' must not be ignored.")

        if self.cancel_event:
            logger.info("Cancelled by user")
            sys.exit()

        if isinstance(csv, pd.DataFrame):
            instances = Dataset(csv, weights)
        else:
            instances = Dataset().from_file(csv, weights, sheet)

        if self._threshold is not None:
            logger.debug(
                f"Threshold set to {self._threshold[0]}, filtering instances")
            instances.filter_threshold(*self._threshold)

        instances.set_ignored(self.ignore_columns)
        if self.drop_duplicates:
            logger.debug("Dropping duplicates")
            instances.data.drop_duplicates(inplace=True)
        self.build_classifier(instances)

        # use test set, if available
        if test:
            logger.debug(f"Using testset {test}")
            if isinstance(test, pd.DataFrame):
                instances = Dataset(test)
            else:
                instances = Dataset().from_file(test, sheet=test_sheet)

            # add class column, if necessary
            class_column_name = self.training_instances.class_column_name()
            if class_column_name not in instances.data.columns:
                instances.add_class_column(class_column_name)
                instances.class_index = instances.num_attributes() - 1

            instances.set_ignored(self.ignore_columns, silent=True)
            self.check_header(instances)

        # do this first, just in case it fails
        if out_path and not out_path.parent.exists():
            out_path.parent.mkdir(parents=True)

        results = []
        total = len(instances)

        # progress bar for GUI
        if self.gui_queue:
            self.gui_queue.put((0, total))

        for i in tqdm(range(total), desc="Classifying instances",
                      colour="green", leave=False):

            # GUI things
            if self.gui_queue:
                self.gui_queue.put((i + 1, total))
            if self.cancel_event:
                logger.info(f"Cancelled by user at step {i} of {total}")
                sys.exit()

            self.distribution_for_instance(instances[i])
            results.append(self.get_results())

        # evaluate if there is a ground truth answer
        if results[0].get_expected_class_name() is None:
            files = self.create_output_files(out_path, results, instances)
            return None, None, files

        acc, conf_matrix = self.evaluate(instances, results)
        print(f"Accuracy: {round(acc * 100, 3)}%")
        files = self.create_output_files(out_path, results, instances)

        # for GUI
        return acc, conf_matrix, files

    def build_classifier(self, instances: Dataset) -> None:
        """This is used to build the classifier; it specifies the
        capabilities of the classifier and loads in exemplars to be used for
        prediction. No actual analysis happens here because AM is a lazy
        classifier."""

        # remove instances with missing class value
        instances.delete_with_missing_class()

        self.cardinality = instances.num_counted_attributes()
        logger.debug(f"Cardinality is {self.cardinality}")
        # save instances for checking headers
        self.training_instances = instances  # , 0, instances.num_attributes())

        # create exemplars for actually running the classifier
        self.training_exemplars = list(instances)

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
            logger.debug("Only one class in training data.")
            # 100 percent likelihood of belonging to the one class
            return {self.training_instances[0].class_value(): 1.0}

        self.results = self.classify(instance)
        return self.results.get_class_likelihood()

    def get_results(self) -> AMResults:
        """

        :return: classification results from the last call to
            :func:`distribution_for_instance`
        :raises RuntimeError: if you've never called
            :func:`distribution_for_instance` from this object
        """
        if self.results is None:
            raise RuntimeError(
                "Call distributionForInstance before calling this")
        return self.results

    @staticmethod
    def evaluate(instances: Dataset, results: list[AMResults]) -> tuple[
        float, ConfusionMatrixDisplay]:
        """Calculate accuracy and plot confusion matrix.

        The confusion matrix can be inaccurate, as it does not
        consider ties.

        :param instances: dataset used for prediction
        :param results: list of AMResults
        :return: accuracy and confusion matrix
        """
        # inaccurate in the case of ties
        preds = ["".join(res.predicted_classes) for res in results]
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

    def __str__(self) -> str:
        """

        :return: String containing name of the classifier and number of
            training instances
        """
        string = "Analogical Modeling Classifier (2025 Jasmin Wiese)\n"
        if self.training_exemplars:
            return string + (f"Training instances: "
                             f"{len(self.training_exemplars)}\n")
        return string

    # following methods for output files
    @staticmethod
    def create_headers(lex_feats: pd.Index, test_feats, classes: list) -> tuple[
        list, list, list]:
        """Create headers for output files.

        :param lex_feats: attributes of lexicon
        :param test_feats: attributes of test data (or lexicon, if no test data)
        :param classes: possible class values
        :return: headers for gang effects, analogical sets and distributions
        """

        l_feats_list = lex_feats.tolist()
        t_feats_list = test_feats.tolist()
        cls_header = ([f"Class {i + 1}" for i in range(len(classes))] +
                      sum([[f"{cls}: pointers", f"{cls}: pct"]
                           for cls in classes], []))
        cls_header_gang = sum(
            [[f"{cls}: pointers", f"{cls}: pct", f"{cls}: size"]
             for cls in classes], [])

        gang_header = (l_feats_list + ["Weight"] + cls_header_gang +
                       ["Gang pointers", "Gang pct", "Rank", "Size",
                        "Total pointers", "Classified item index",
                        "Classified item class"] +
                       [f"Classified item {el}" for el in test_feats])
        analog_header = (l_feats_list +
                         ["Weight", "Class", "Percentage", "Pointers",
                          "Classified item index", "Classified item class"] +
                         [f"Classified item {el}" for el in test_feats])
        distr_header = (
                ["Judgement", "Expected", "Predicted"] + t_feats_list +
                cls_header +
                ["Train size", "Num feats", "Ignore unknown values",
                 "Missing data compare", "Ignore given",
                 "Count strategy", "Classified item index"])

        return gang_header, analog_header, distr_header

    @staticmethod
    def create_gangs(effects: Iterable[GangEffect], classified: Instance,
                     classes: Iterable[str], idx: int) -> list:
        """Create list of gang effects for output.

        :param effects: Gang effects for classified instance
        :param classified: instance for which to store gang effects
        :param classes: possible classes
        :param idx: index of the instance
        """

        def get_cls_pct(effect, cls, pointers, gang_pct):
            """Helper to handle potential divisions by zero"""
            try:
                return round(effect.class_to_pointers.get(cls, 0)
                             / pointers * gang_pct,
                             3)
            except ZeroDivisionError:
                return 0.0

        total_pointers = sum(effect.total_pointers for effect in effects)
        pointers_rank = sorted(
            list(set(effect.total_pointers for effect in effects)),
            reverse=True
        )
        gangs = []

        for effect in effects:
            effect_pointers = effect.total_pointers
            rank = pointers_rank.index(effect_pointers) + 1
            gang_pct = effect_pointers / total_pointers * 100

            cls_info = {inst: sum([
                [effect.class_to_pointers.get(cls, 0),  # cls: pointers
                 get_cls_pct(effect, cls, effect_pointers, gang_pct),
                 # cls: pct
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
        return gangs

    @staticmethod
    def create_analogical_set(res: AMResults, classified: Instance,
                              idx: int) -> list:
        """Create list of analogical sets for output.

        :param res: result of AnalogicalModeling
        :param classified: instance for which to create analogical sets
        :param idx: index of instance
        """
        pointers = res.exemplar_pointers
        effects = res.exemplar_effects
        return [
            inst.real_data.to_list() + [
                inst.weight,  # weight
                inst.class_value(),  # class
                effects.get(inst) * 100,  # percentage
                ptrs,  # pointers
                idx,  # index
                classified.class_value()  # instance class
            ] + classified.real_data.tolist() for inst, ptrs in
            pointers.items()]

    def create_distribution(self, res: AMResults, classified: Instance,
                            classes: list[str], idx: int,
                            instances: Dataset) -> list:
        """Create list of distribution information for output.

        :param res: result of AnalogicalModeling
        :param classified: instance for which to create distribution
        :param classes: possible classes
        :param idx: index of instance
        :param instances: dataset from which the instance comes
        """
        pred = res.predicted_classes
        gold = res.get_expected_class_name()
        train_size = res.sub_list.considered_exemplar_count
        num_feats = instances.num_attributes() - 1  # - class attribute
        ignore = self.ignore_unknowns
        mdc = self.mdc.name
        ignore_given = self.remove_test_exemplar
        count_strategy = "linear" if self.linear_count else "quadratic"

        cls_info = classes + sum([[
            res.class_pointers.get(cls, 0),  # cls: pointers
            res.class_likelihood_map.get(cls, 0.0) * 100]  # cls: pct
            for cls in classes], [])

        return [
            [res.get_judgement().value,  # judgement
             gold,  # expected
             '|'.join(map(str, pred))  # predicted
             ] + classified.real_data.tolist() + cls_info + [
                train_size,  # train size
                num_feats,  # num feats
                ignore,  # ignore unknown values
                mdc,  # missing data compare
                ignore_given,  # ignore given
                count_strategy,  # count strategy
                idx  # index
            ]]

    def create_output_files(self, dest: Path, results: list[AMResults],
                            instances: Dataset) -> tuple:
        """Store information on analogical sets, gang effects and distributions.

        :param dest: start name for output files
        :param results: list of AMResults
        :param instances: dataset used for prediction
        """
        if self.cancel_event:
            logger.info("Cancelled by user before generating output")
            sys.exit()

        print("Generating output files...")

        # headers
        classes = list(self.training_instances.get_classes())
        gang_header, analog_header, distr_header = self.create_headers(
            self.training_instances[0].real_data.keys(),
            results[0].classified_exemplar.real_data.keys(), classes)

        gangs = []
        analogs = []
        distributions = []
        for idx, res in enumerate(results):
            if self.cancel_event:
                logger.info("Cancelled by user")
                sys.exit()
            classified = res.classified_exemplar

            # gang effects
            gangs += self.create_gangs(res.get_gang_effects(), classified,
                                       classes, idx)
            # analogical sets
            analogs += self.create_analogical_set(res, classified, idx)
            # distribution
            distributions += self.create_distribution(res, classified, classes,
                                                      idx, instances)

        gang = pd.DataFrame(gangs, columns=gang_header)
        analog = pd.DataFrame(analogs, columns=analog_header)
        distr = pd.DataFrame(distributions, columns=distr_header)

        if self.cancel_event:
            logger.info("Cancelled by user before saving")
            sys.exit()

        if dest:
            out_gang = dest.with_name(dest.stem + "_gangs.csv")
            out_analog = dest.with_name(dest.stem + "_analogical_sets.csv")
            out_distribution = dest.with_name(dest.stem + "_distributions.csv")

            gang.to_csv(out_gang, index=False)
            analog.to_csv(out_analog, index=False)
            distr.to_csv(out_distribution, index=False)
            print(f"Outputs saved to {out_gang}, {out_analog}, "
                  f"{out_distribution}.")
        return gang, analog, distr

    def update_classifier(self, instance: Instance) -> None:
        """This is used to add more information to the classifier."""
        self.check_header(instance)

        if instance.is_missing(instance.get_class_index()):
            return
        self.training_instances.add(instance)
        self.training_exemplars.append(instance)
        logger.debug(f"Added instance: {instance}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--lexicon", type=Path,
                        help="csv containing the data", required=True)
    parser.add_argument("--sheet", type=str,
                        help="sheet name for Excel sheet", required=False)
    parser.add_argument("-t", "--test",
                        help="csv containing test data")
    parser.add_argument("--test_sheet", type=str,
                        help="sheet name for Excel sheet", required=False)
    parser.add_argument("-o", "--output",
                        help="output path", type=Path, required=True)
    parser.add_argument("-w", "--weight_colum",
                        help="Name of column for weights")
    parser.add_argument("-th", "--threshold", type=float,
                        help="lower threshold for instance weights",
                        default=None)
    parser.add_argument("--inclusive", action="store_true",
                        help="make lower threshold inclusive")
    parser.add_argument("-mt", "--max_threshold", type=float,
                        help="upper threshold for instance weights",
                        default=None)
    parser.add_argument("--max_inclusive", action="store_true",
                        help="make upper threshold inclusive")
    parser.add_argument("-d", "--drop_duplicates",
                        action="store_true", help="Drop duplicated instances")
    parser.add_argument("--ignore_columns", nargs="*",
                        help="Columns to ignore", type=str, default=[])
    parser.add_argument("-L", "--linear", action="store_true")
    parser.add_argument("-k", "--keep_test", action="store_false",
                        help="Keep test exemplar in training set (default: "
                             "False)")  # !keep_test = remove, which is default
    parser.add_argument("-i", "--ignore_unknowns", action="store_true",
                        help="Ignore attributes with unknown values in the "
                             "test exemplar")
    parser.add_argument("-D", "--debug", action="store_true",
                        help="Run classifier in debug mode; will write "
                             "additional information to .log")
    parser.add_argument("-m", "--missing_data",
                        choices=["match", "mismatch", "variable"],
                        default="variable",
                        help="Method of dealing with missing data. The options "
                             "are 'variable', 'match' or 'mismatch'; "
                             "'variable' means to treat missing data as all "
                             "one variable (matching only missing values), "
                             "'match' means that missing data will be "
                             "considered the same as whatever it is "
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

    if args.debug:
        logger.setLevel(logging.DEBUG)

    # setting all values
    am = AnalogicalModeling()
    am.set_linear_count(args.linear)
    am.set_remove_test_exemplar(args.keep_test)
    am.set_ignore_unknowns(args.ignore_unknowns)
    am.set_missing_data_compare(args.missing_data)
    am.set_drop_duplicates(args.drop_duplicates)
    am.set_ignore_columns(args.ignore_columns)

    am.threshold = (args.threshold, args.inclusive)#, args.max_threshold, args.max_inclusive)

    # running actual algorithm
    try:
        _, matrix, _ = am.run_classifier(args.lexicon,
                                         args.output,
                                         args.test,
                                         args.weight_colum,
                                         args.sheet,
                                         args.test_sheet)
        if matrix:
            matrix.plot()
            plt.xlabel("Predicted label\nTies are excluded from the plot")
            plt.tight_layout()
            plt.show()
    except Exception as e:
        logger.exception(e)
        raise e
