"""weka.classifiers.lazy.AM"""

# FIXME: how to get weka java things?
# import weka.core.SelectedTag;
# import weka.core.Tag;

from enum import Enum
from dataclasses import dataclass
from typing import Protocol


# FIXME: might come from somewhere else
@dataclass
class Tag:
    id_: int
    description: str


@dataclass
class SelectedTag:
    selected_tag: Tag

    def get_selected_tag(self):
        return self.selected_tag


# In Weka, configuration with a specific set of possible values is implemented using {@link Tag}. These
# utilities make it possible to use an enum as the set of tags for a given config parameter.
#
class Enum2TagUtils:
    """Enums whose values are to be used as tags should implement this."""

    def get_tags(self, enum_class):
        """

        :param enum_class: The enum whose members are used as tags
        :return: Array of tags to be used for Weka configuration
        """
        return [Tag(el.value[0], el.get_description()) for el in enum_class]

    def get_element(self, enum_class, tag: SelectedTag):
        """

        :param enum_class: The enum whose members are used as tags
        :param tag: specifying which enum element to return. The id of this tag
        must match the desired element's ordinal() value.
        :return: The selected element of this enum
        """
        id_ = tag.get_selected_tag().id_
        for el in enum_class:
            if el.value[0] == id_:
                return el
        raise ValueError("There is no element with the specified value")

    def get_element_by_option(self, enum_class, option): # FIXME: name = get_element
        """

        :param enum_class: The enum whose members are used as tags
        :param option: The option specified by the user; it must match
        {@link TagInfo#getOptionString() getOptionString} for one enum member
        :return: The enum member specified by the option string
        """
        for el in enum_class:
            if el.get_option_string() == option:
                return el
        raise ValueError("There is no element with the specified option string")


class TagInfo(Protocol):
    def get_description(self) -> str:
        """

        :return: The user-facing tag description (used for the `readable` parameter
        """
        pass

    def get_option_string(self) -> str:
        """

        :return: the option string to be used to indicate the enum member
        """
        pass
