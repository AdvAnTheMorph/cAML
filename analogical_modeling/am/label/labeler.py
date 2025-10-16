"""weka.classifiers.lazy.AM.label

Analogical Modeling uses labels composed of boolean vectors in order to group
instances into subcontexts and subcontexts in supracontexts. Training set
instances are assigned labels by comparing them with the instance to be
classified and encoding matched attributes and mismatched attributes in a
boolean vector.

This class is used to assign context labels to training instances by
comparison with the instance being classified.
"""

from math import ceil, floor

from analogical_modeling.am.label.label import Label
from analogical_modeling.am.label.missing_data_compare import MissingDataCompare
from analogical_modeling.utils import Instance


# The default (max) size of a label partition
PARTITION_SIZE = 5


class Labeler:
    def __init__(self, test: Instance, ignore_unknowns: bool, mdc: MissingDataCompare):
        """

        :param test: Instance being classified
        :param ignore_unknowns: True if attributes with undefined values in the test item should be ignored; False if not.
        :param mdc: Specifies how to compare missing attributes
        """
        self.mdc = mdc
        self.test_instance = test
        self.ignore_unknowns = ignore_unknowns
        ignore_set = set()

        if self.ignore_unknowns:
            length = self.test_instance.num_attributes() - 1
            for i in range(length):
                if self.test_instance.is_missing(i):
                    ignore_set.add(i)
        self.ignore_set = frozenset(ignore_set)

        spans = self.partitions()
        self.partitioners = [Partitioner(spans[i]) for i in range(self.num_partitions())]

    def get_cardinality(self):
        """

        :return: The cardinality of the generated labels, or how many instance attributes are considered during labeling.
        """
        return self.test_instance.num_attributes() - len(self.ignore_set) - 1

    @staticmethod
    def get_cardinality_of(test_instance: Instance, ignore_unknowns: bool):  # TODO: was get_cardinality -> check that right method used!
        """Calculate the label cardinality for a given test instance

        :param test_instance: instance to assign labels
        :param ignore_unknowns: True if unknown values are ignored; False otherwise
        :return: the cardinality of labels generated from testInstance and ignoreUnknowns
        """
        cardinality = 0
        for i in range(test_instance.num_attributes()):
            if i != test_instance.class_index and not (test_instance.is_missing(i) and ignore_unknowns):
                cardinality += 1
        return cardinality

    def get_ignore_unknowns(self):
        """

        :return: True if attributes with undefined values in the test item are ignored during labeling; False if not.
        """
        return self.ignore_unknowns

    def get_missing_data_compare(self):
        """

        :return: the MissingDataCompare strategy in use by this labeler
        """
        return self.mdc

    def get_test_instance(self):
        """

        :return: the test instance being used to label other instances
        """
        return self.test_instance

    def is_ignored(self, index: int) -> bool:
        """
        Find if the attribute at the given index is ignored during labeling. The
        default behavior is to ignore the attributes with unknown values in the
        test instance if get_ignore_unknowns() is true.

        :param index: Index of the attribute being queried
        :return: True if the given attribute is ignored during labeling; False otherwise.
        """
        return index in self.ignore_set

    def label(self, data: Instance) -> Label:
        """
        Create a context label for the input instance by comparing it with the
        test instance.

        :param data: Instance to be labeled
        :return: the label for the context that the instance belongs to. The cardinality of the label will be the same as
        the test and data items. At any given index i, label.matches(i) will return True if
        that feature is the same in the test and data instances.
        :raises: ValueError if the test and data instances are not from the same data set.
        """
        # FIXME: implement
        # if not data.equal_headers(self.get_test_instance()):
        #     raise ValueError("Input instance is not compatible with the test instance")

        label = set()
        length = self.get_cardinality()

        index = 0
        for i in range(self.get_test_instance().num_attributes()):
            # skip ignored attributes and the class attribute
            if self.is_ignored(i) or i == self.get_test_instance().class_index:
                continue
            att = self.get_test_instance().attribute_name(i)
            # use mdc if were are comparing a missing attribute
            if self.get_test_instance().is_missing(i) or data.is_missing(i):
                if not self.get_missing_data_compare().matches(self.get_test_instance(), data, i):
                    # use length-1-index instead of index so that in binary the
                    # labels show left to right, first to last feature.
                    label.add(length - 1 - index)
            elif self.get_test_instance().value(att) != data.value(att):
                # same as above
                label.add(length - 1 - index)
            index += 1
        return Label(label, self.get_cardinality())

    def get_context_string(self, label: Label):
        """
        Returns a string representing the context. If the input test instance attributes are "A C D Z R",
	    and the label is 00101, then the return string will be "A C * Z *".
        """
        context_list = self.get_context_list(label, "*")
        return " ".join(map(str, context_list))

    def get_context_list(self, label: Label, mismatch_string: str) -> list[str]:
        """
        Returns a list representing the context. If the input test instance attributes are "A C D Z R",
        the label is 00101, and the mismatch_string is "*", then the return list
        will be "A", "C", "*", "Z", "*".
        """
        context_bit_string = str(label)
        result = []
        label_index = 0
        for i in range(self.test_instance.num_attributes()):
            # skip the class attribute and ignored attributes
            if i == self.test_instance.class_index or self.is_ignored(i):
                continue
            if context_bit_string[label_index] == "0":
                result.append(self.test_instance.string_value(i))
            else:
                result.append(mismatch_string)
            label_index += 1
        return result

    def get_instance_atts_string(self, instance: Instance, att_delimiter: str) -> str:
        """
        Returns a string containing the attributes of the input instance (minus the class
        attribute and ignored attributes).
        """
        atts = self.get_instance_atts_values_list(instance)
        return att_delimiter.join(atts)

    def get_instance_atts_values_list(self, instance: Instance) -> list[str]:
        """Returns a list containing the attributes of the input instance (minus the class
        attribute and ignored attributes)."""
        atts = []
        for i in range(instance.num_attributes()):
            if i == instance.class_index or self.is_ignored(i):
                continue
            atts.append(str(instance[i]))
        return atts

    def get_instance_atts_names_list(self, instance: Instance) -> list[str]:
        atts = []
        for i in range(instance.num_attributes()):
            if i == instance.class_index or self.is_ignored(i):
                continue
            atts.append(instance.attribute_name(i))
        return atts

    def get_lattice_top(self):
        """
        Creates and returns the label which belongs at the top of the boolean
        lattice formed by the subcontexts labeled by this labeler, i.e. the one for
	    which every feature is a match.

	    :return: A label with all matches
	    """
        return Label(set(), self.get_cardinality())

    def get_lattice_bottom(self):
        """
        Creates and returns the label which belongs at the bottom of the boolean
	    lattice formed by the subcontexts labeled by this labeler, i.e. the one for
	    which every feature is a mismatch.

        :return: A label with all mismatches
        """
        bottom = set(range(self.get_cardinality()))

        return Label(bottom, self.get_cardinality())

    def from_bits(self, label_bits: int):
        """For testing purposes, this method allows the client to directly specify the label using
	    the bits of an integer
	    """
        bits = set()
        index = 0
        while label_bits != 0:
            if label_bits % 2 != 0:
                bits.add(index)
            index += 1
            label_bits = label_bits >> 1
        return Label(bits, self.get_cardinality())

    def partition(self, label: Label, partition_index: int) -> Label:
        """
        In distributed processing, it is necessary to split labels into
        partitions. This method returns a partition for the given label. A full
        label is partitioned into pieces 0 through num_partitions(), so
        code to process labels in pieces should look like this:

        <pre>
        Label myLabel = myLabeler.label(myInstance);
        for(int i = 0; i &lt; myLabeler.numPartitions(); i++)
            process(myLabeler.partition(myLabel, i);
        </pre>

        :param partition_index:  index of the partition to return
        :return: a new label representing a portion of the attributes represented by the input label.
        :raises: ValueError if the partitionIndex is greater than num_partitions() or less than zero.
        :raises: ValueError if the input label is not compatible with this labeler.
        """
        if partition_index > self.num_partitions() or partition_index < 0:
            raise ValueError(f"Illegal partition index: {partition_index}")
        if label.get_cardinality() != self.get_cardinality():
            raise ValueError(
                f"Label cardinality is {label.get_cardinality()}, but labeler cardinality is {self.get_cardinality()}")
        if not isinstance(label, Label):
            raise ValueError(
                f"This labeler can only handle Labels; input label was an instance of {label.__class__.__name__}")

        # create and cache the masks if they have not be created yet
        return self.partitioners[partition_index].extract(label)

    def num_partitions(self) -> int:
        """

        :return: The number of label partitions available via partition
        """
        if self.get_cardinality() < PARTITION_SIZE:
            return 1
        return ceil(self.get_cardinality() / PARTITION_SIZE)

    def partitions(self) -> list['Partition']:
        """This provides a default partitioning implementation which is overridable
        by child classes.

        :return: An array of partitions indicating how labels can be split into partitions.
        """
        spans = [Partition(0, 0) for _ in range(self.num_partitions())]
        span_size = floor(self.get_cardinality() / self.num_partitions())
        # an extra bit will be given to remainder masks, since numMasks
        # probably does not divide cardinality
        remainder = self.get_cardinality() % self.num_partitions()
        index = 0

        for i in range(self.num_partitions()):
            if i < remainder:
                inc = span_size + 1
            else:
                inc = span_size
            spans[i] = Partition(index, inc)
            index += inc
        return spans


class Partition:
    """Simple class for storing index spans."""
    def __init__(self, s: int, l: int) -> None:
        self.start_index = s
        self.cardinality = l

    def get_start_index(self) -> int:
        """

        :return: The beginning of the span
        """
        return self.start_index

    def get_cardinality(self) -> int:
        """

        :return: The cardinality of the partition, or number of represented features.
        """
        return self.cardinality

    def __str__(self):
        return f"[{self.start_index},{self.cardinality}]"


class Partitioner:
    """ class for storing label partitions"""
    def __init__(self, s: Partition):
        self.start_index = s.get_start_index()
        self.cardinality = s.get_cardinality()

    def extract(self, label: Label) -> Label:
        new_label = set()
        # loop through the bits and set the unmatched ones
        for i in range(self.cardinality):
            if not label.matches(i + self.start_index):
                new_label.add(i)
        return Label(new_label, self.cardinality)

    def __str__(self):
        return f"{self.start_index},{self.cardinality}"

