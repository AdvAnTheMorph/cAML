"""weka.classifiers.lazy.AM"""

import random
from pathlib import Path
from threading import Lock
from typing import TypeVar

from unittest.mock import Mock


from analogical_modeling import utils
from analogical_modeling.am import am_utils
from analogical_modeling.am.data.subcontext import Subcontext
from analogical_modeling.am.data.supracontext import Supracontext
from analogical_modeling.am.label.label import Label
from analogical_modeling.am.data.classified_supra import ClassifiedSupra
# from analogical_modeling.analogical_modeling import AnalogicalModeling
from analogical_modeling.utils import Instance, Dataset

# TODO: remove
AnalogicalModeling = TypeVar("AnalogicalModeling")

# The name of the chapter 3 training data file
CHAPTER_3_DATA = "ch3example.csv"
# The name of the finnverb data file. 10 attributes, 189 instances
FINNVERB = "finnverb.csv"
# A paired-down finnverb for minimal testing.
FINNVERB_MIN = "finn_min_gangs.csv"
# 35 attributes, 683 instances
SOYBEAN = "soybean.csv"
# 69 attributes, 226 instances
AUDIOLOGY = "audiology.csv"
# 13 attributes, 4,969 instances
SPANISH_STRESS = "spanish_stress.csv"


def get_dataset(file_in_data_folder: str) -> utils.Dataset:
    """
    Read a dataset from disk and return the Instances object. It is assumed
    that the file is in the project data folder, and that the class attribute
    is the last one.

    :param file_in_data_folder: Name of csv file located in the project data folder
    :return: The dataset contained in the given file.
    :raises Exception: if there is a problem loading the dataset
    """
    source = Path("data") / file_in_data_folder
    # instances = source.get_data_set()
    # instances.set_class_index(instances.num_attributes() -1)
    # return instances
    data = utils.Dataset()
    data.from_csv(source)
    return data


def get_instance_from_file(file_in_data_folder: str, index: int) -> utils.Instance:
    """
    Read a dataset from disk and return the Instance object at the specified
    index. It is assumed that the file is in the project data folder, and
    that the class attribute is the last one.

    :param file_in_data_folder: Name of csv file in located in the project data folder
    :param index: Index of instance to return
    :return: The instance at the specified index of the dataset contained in the file
    :raises Exception: if there is a problem loading the instance
    """
    instances = get_dataset(file_in_data_folder)
    # instances.set_class_index(instances.num_attributes() - 1)
    return instances[index]


def six_cardinality_data():
    # atts = []
	# 	atts.add(new Attribute("a", List.of("a", "z", "w")));  # column z,w with name a
	# 	atts.add(new Attribute("b", List.of("b", "x", "y")));
	# 	atts.add(new Attribute("c", List.of("c", "w", "v")));
	# 	atts.add(new Attribute("d", List.of("d", "u", "t")));
	# 	atts.add(new Attribute("e", List.of("e", "s", "r")));
	# 	atts.add(new Attribute("class", List.of("e", "r")));
    #     Instances dataset = new Instances("TestInstances", atts, 0);
    #     dataset.setClassIndex(dataset.numAttributes() - 1);

    # data = [[0, 1, 2, 1, 1, 1], [0, 1, 2, 1, 1, 0], [2, 1, 1, 2, 1, 1], [0, 1, 2, 0, 2, 0],
    #         [2, 1, 2, 0, 2, 1], [1, 0, 1, 0, 0, 0], [0, 1, 1, 1, float("NaN"), 1],
    #         [0, 1, 0, 1, float("NaN"), 0], [0, 1, 2, float("NaN"), 1, 1]]
    data = [list("axvusr"), list("axvuse"), list("wxwtsr"), list("axvdre"),
            list("wxvdrr"), list("zbwdee"), ["a", "x", "w", "u", float("NaN"), "r"],
            ["a", "x", "c", "u", float("NaN"), "e"], ["a", "x", "v", float("NaN"), "s", "r"]]
    #     for (double[] datum : data) {
    #         Instance instance = new DenseInstance(6, datum);
    #         dataset.add(instance);
    #     }
    dataset = utils.Dataset(data)
    dataset.set_class_index(dataset.num_attributes() - 1)
    return dataset


def mock_instance(num_attributes: int):
    inst = Mock()
    # add one attribute for the class, so that numAttributes matches the resulting label size exactly
    inst.num_attributes.return_value = num_attributes + 1
    return inst


def get_reduced_dataset(file_in_data_folder: str, ignore_atts: list[int]) -> utils.Dataset:
    """Read a dataset from the given file and remove the specified attributes, then return it.

    :param file_in_data_folder: name of file in the project data folder
    :param ignore_atts:  A list of indices specifying which attributes should be removed.
    :return: The altered dataset
    """

    data = get_dataset(file_in_data_folder)

    data.data.drop(data.data.columns[ignore_atts], axis=1, inplace=True)
    data.set_class_index(data.num_attributes() -1)
    return data


def get_deterministic_random_provider():
    """ Supply deterministic PRNG output for testing algorithms that use randomness (JJLattice, etc.)

    :return: A random provider with deterministic output
    """
    random_seeder = [0]
    lock = Lock()

    def random_provider():
        with lock:
            seed = random_seeder[0]
            random_seeder[0] += 1
            return random.Random(seed)
    return random_provider


def supra_deep_equals(supra1: Supracontext, supra2: Supracontext):
    return supra1.get_count() == supra2.get_count() and supra1.get_data() == supra2.get_data()


def contains_supra(actual_supras: set, expected):
    for supra in actual_supras:
        if supra_deep_equals(supra, expected):
            return True
    return False


def leave_out_index(am: AnalogicalModeling, data: Dataset, index: int):
    # copy so that removing an instance doesn't affect the original
    train = Dataset(data)
    test = train.data.drop(index=index)
    am.build_classifier(train)
    am.distribution_for_instance(test)

    return am.get_results()

def leave_one_out(am: AnalogicalModeling, data: Dataset):
    correct = 0
    for i in range(data.data.size[0]):
        am_set = leave_out_index(am, data, i)
        if data[i].class_value() in am_set.get_predicted_classer():
            correct += 1
    return correct


def bits_to_bitset(bits: int) -> set[int]:
    bitset = set()
    index = 0
    while bits != 0:
        if bits % 2 != 0:
            bitset.add(index)
        index += 1
        bits = bits >> 1
    return bitset


def get_supra_from_string(supra_string: str, data):
    """Create the ClassifiedSupra object specified by the input string.

    This method is somewhat slow, so use it only in testing, and only with
    small datasets if possible.

    :param supra_string: A string representing the supracontext to be created.
                         This should be in the same form as that produced by
                         str(ClassifiedSupra).
    :param data: The dataset containing the instances specified in the Supracontext string. For example:
                 <code>[1x(01010|&amp;nondeterministic&amp;|H,A,V,A,0,B/H,A,V,I,0,A)]</code> .
    :return: classified supra created according to string specification
    """
    # get the count, between '[' and the first 'x'
    loc = supra_string.index("x")
    count = int(supra_string[1:loc])
    if count < 0:
        raise ValueError("Count must be greater than 0")
    loc += 1  # skip x

    # parse subcontexts, which are each contained in parentheses
    subs = set()
    subs_string = supra_string[loc:supra_string.index("]")]
    for substring in subs_string.split("),("):
        # remove extra parentheses
        substring = substring.replace(")", "").replace("(", "")
        # split into label, outcome, and instances
        sub_components = substring.split("|")
        if len(sub_components) != 3:
            raise ValueError(f"Incomplete subcontext specified {substring}")
        # parse label
        label = Label(bits_to_bitset(int(sub_components[0], 2)), len(sub_components[0]))
        sub = Subcontext(label, "foo")

        # parse outcome
        if sub_components[1] == am_utils.NONDETERMINISTIC_STRING:
            outcome = am_utils.NONDETERMINISTIC
        else:
            outcome = sub_components[1]
            if outcome == -1:
                raise ValueError(f"Unknown outcome given: {sub_components[1]}")

        # parse instances; use this set to keep track of previous instances,
        # in case there are several with the same string representation
        seen_instances = set()
        for instance_string in sub_components[2].split("/"):
            # we can't just create a new Instance from the given
            # attributes;
            # since there is no Instance.equals() method, the only way to
            # achieve Supra equality is by having the exact same Instance
            # instances, i.e. grep the set for the matching object :(
            # # TODO: pd.Series.equals() exists
            added = False
            # inst = Instance(instance_string.split(","), len(instance_string.split(","))-1)
            # if inst in data:
            #     sub.add(inst)
            #     added = True
            #     seen_instances.add(inst)
            for instance in data:
                if str(instance) == instance_string:
                    if instance in seen_instances:
                        continue
                    sub.add(instance)
                    added = True
                    seen_instances.add(instance)
                    break
            if not added:
                raise ValueError(f"{instance_string} does not specify any instance in the given dataset")
        if sub.get_outcome() != outcome:
            raise ValueError(f"Specified instances give an outcome of {sub.get_outcome()}, not {outcome}")
        subs.add(sub)
    return ClassifiedSupra(subs, count)


def test_supra_from_string():
    """Test that the get_supra_from_string utility function above works as desired."""
    # data = get_reduced_dataset(FINNVERB_MIN, [5, 6, 7, 8, 9])
    # sub1 = Subcontext(Label(0b10110, 5), "foo")
    # sub1.add(data[3])  # P,U,0,?,0,A
    #
    # sub2 = Subcontext(Label(0b10000, 5), "foo")
    # sub2.add(data[2])  # K,U,V,U,0,A
    #
    # sub3 = Subcontext(Label(0b10010, 5), "foo")
    # sub3.add(data[1])  # U,U,V,I,0,A

    # expected_supra = ClassifiedSupra({sub1, sub2, sub3}, 1)
    # supra_string = "[1x(10110|A|P,U,0,?,0,A),(10000|A|K,U,V,U,0,A),(10010|A|U,U,V,I,0,A)]"
    # actual_supra = get_supra_from_string(supra_string, data)
    # assert supra_deep_equals(expected_supra, actual_supra)
    # assert supra_deep_equals(get_supra_from_string(str(expected_supra), data), actual_supra)
    #
    # supra_string = "[1x(01010|&nondeterministic&|H,A,V,A,0,B/H,A,V,I,0,A)]"
    # actual_supra = get_supra_from_string(supra_string, data)
    # sub4 = Subcontext(Label(0b01010, 5), "foo")
    # sub4.add(data[4])  # H,A,V,I,0,A
    # sub4.add(data[5])  # H,A,V,A,0,B
    # expected_supra = ClassifiedSupra({sub4}, 1)
    #
    # assert supra_deep_equals(expected_supra, actual_supra)
    # assert supra_deep_equals(get_supra_from_string(str(expected_supra), data), actual_supra)

    data = get_reduced_dataset(FINNVERB, [5, 6, 7, 8, 9])
    sub5 = Subcontext(Label({0}, 5), "foo")
    sub5.add(data[1])  # A,A,0,?,S,B
    sub5.add(data[2])  # also A,A,0,?,S,B  # FIXME: fails probably due to set() -> can be added only once, since equal
    expected_supra = ClassifiedSupra({sub5}, 6)
    supra_string = "[6x(00001|B|A,A,0,?,S,B/A,A,0,?,S,B)]"
    actual_supra = get_supra_from_string(supra_string, data)
    assert actual_supra == expected_supra
    assert supra_deep_equals(expected_supra, actual_supra)
    assert supra_deep_equals(get_supra_from_string(str(expected_supra), data), actual_supra)

#         // TODO: test error conditions

