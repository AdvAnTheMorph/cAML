"""Utility classes for reading data.

remains from weka:
- Attributes = columns
- Instances = rows
"""
import math
import warnings
from os import PathLike
from pathlib import Path
from typing import Any, Optional

import pandas as pd


class InvalidColumnError(Exception):
    """Exception if a column configuration is invalid."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class EmptyLexiconError(Exception):
    """Exception if a lexicon is empty."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class TooFewAttributesError(Exception):
    """Exception if less than 2 attributes (class + 1 other)"""
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class Instance(pd.Series):
    """Instance Representation"""

    # needed for serialization
    _metadata = ["class_index", "ignored", "real_data", "data_idx", "weight"]

    def __init__(self, data: pd.Series, class_column: str,
                 ignore_list: list[str], idx: int, weight: float, silent=False):
        """

        :param data: Series containing values of the Instance
        :param class_column: name of column containing class value
        :param ignore_list: columns to ignore
        :param idx: index in the dataset
        :raise InvalidColumnError: if not silent and ignored columns not in data
        """
        super().__init__(data)
        if silent:
            self.drop(labels=ignore_list, inplace=True, errors="ignore")
        else:
            try:
                self.drop(labels=ignore_list, inplace=True)
            except KeyError as e:  # raise error to prevent silent typos
                raise InvalidColumnError(
                    f"Not all ignored columns ({ignore_list}) in data (valid "
                    f"columns are {list(self.keys())}).") from e
        self.class_index = self.keys().get_loc(class_column)
        self.real_data = data
        self.data_idx = idx
        self.weight = weight

    def is_missing(self, idx: int) -> bool:
        """Check if value is missing.

        Missing values are represented by an equals sign (=).

        :param idx: index of value
        """
        # return self.isna().iloc[idx]
        return self.iloc[idx] == "="

    def num_attributes(self) -> int:
        """Return the number of considered attributes."""
        return self.shape[0]

    def num_all_attributes(self) -> int:
        """Return the number of attributes, including ignored ones."""
        return self.real_data.shape[0]

    def attribute_name(self, idx: int) -> str:
        """Return the name of the attribute at a given index.

        :param idx: index of the attribute
        """
        return self.index[idx]

    def value(self, attr: str) -> Any:
        """Return the value of the given attribute.

        :param attr: attribute name
        """
        return self.get(attr)

    def string_value(self, idx: int):
        """Return the value of an attributed specified by index.

        :param idx: index of the attribute
        """
        return self.iloc[idx]

    def class_value(self) -> Any:
        """Return the value of the class attribute."""
        return self.iloc[self.class_index]

    def __str__(self) -> str:
        return f"{','.join(map(str, self.array))},\u007b{self.weight}\u007d"

    def __hash__(self) -> int:
        return int(pd.util.hash_pandas_object(self, index=False).sum()) + hash(
            37 * self.data_idx)

    def __eq__(self, other) -> bool:
        if isinstance(other, Instance):
            return self.values.all() == other.values.all()
        return super().__eq__(other)


class Dataset:
    """Dataset representation."""

    def __init__(self, atts: list | pd.DataFrame | None = None,
                 weights: str = ""):
        """

        :param atts: if atts is None, call :func:`from_csv` to populate the
            dataset
        :param weights: name of column with weights, if given
        :raise EmptyLexiconError: if lexicon empty
        """
        self.ignored: list[str] = []
        self.silent = False  # require ignored columns to be there
        if atts is None:
            self.data = pd.DataFrame()
            self._class_index = None
            self.weights = []
            return
        self.data = pd.DataFrame(atts).replace(math.nan, None)
        if len(self.data) == 0:
            warnings.warn("The lexicon does not contain any Instances.")

        self.weights = self.set_weights_by_column(weights)
        self.class_index = self.num_attributes() - 1

    def from_file(self, source: PathLike, weights: str = "",
                  sheet: Optional[str] = None) -> 'Dataset':
        """Read dataset from csv file.

        :param source: path to csv or Excel file
        :param weights: name of column with weights, if given
        :param sheet: sheet name for Excel files
        :raise EmptyLexiconError: if lexicon empty
        """
        match Path(source).suffix:  # match/case for easier extension
            case ".xlsx":
                fun = lambda x: pd.read_excel(x, sheet_name=sheet)
            case _:
                fun = pd.read_csv

        self.data = fun(Path(__file__).parent / source).replace(math.nan, None)
        if len(self.data) == 0:
            warnings.warn("The lexicon does not contain any Instances.")

        self.weights = self.set_weights_by_column(weights)

        # set class index only afterwards (possibly one column less than before)
        self.class_index = self.num_attributes() - 1

        return self

    def set_weights_by_column(self, name: str) -> list:
        """Set instance weights.

        The weights column is then dropped from the dataset.

        :param name: name of column with weights, if given
        :raise InvalidColumnError: if weights column not in data or weights
            not numeric or weights negative
        """
        # remove weights from dataset, as they are no features
        if name:
            # make sure that column numerical
            try:
                col = self.data[name]
                if pd.api.types.is_numeric_dtype(col):
                    if min(col) < 0:
                        raise InvalidColumnError(
                            "Weights must not be negative.")
                    weights = col.tolist()
                    self.data.drop(columns=[name], inplace=True)
                else:
                    raise InvalidColumnError(
                        f"Weights column '{name}' does not contain numeric "
                        f"data.")
            except KeyError as e:
                raise InvalidColumnError(
                    f"Weights column '{name}' not found in dataset.") from e
        else:
            weights = [1] * self.data.shape[0]
        return weights

    def get_instance(self, idx) -> Instance:
        """Get an instance of the given index.

        :param idx: index of the instance
        """
        return self.data.iloc[idx]

    def num_attributes(self) -> int:
        """Return the number of attributes (whether ignored or not)."""
        return self.data.shape[1]

    def num_counted_attributes(self) -> int:
        """Return the number of attributes that are not ignored."""
        return self.data.shape[1] - len(self.ignored)

    @property
    def class_index(self) -> int:
        """Get class index."""
        return self._class_index

    @class_index.setter
    def class_index(self, idx: int) -> None:
        """Set the class index.

        :param idx: index of the class
        :raise TypeError: if index is not an integer
        :raise TooFewAttributesError: if fewer than 2 attributes
        :raise ValueError: if index higher than number of attributes
        """
        if not isinstance(idx, int):
            raise TypeError(f"Index must be an integer, not {type(idx)}.")
        if self.num_attributes() < 2:
            warnings.warn("There should be at least 1 attribute beside the class.")
        if idx > self.num_attributes():
            raise ValueError(f"Class index out of range: There are only "
                             f"{self.num_attributes()} attributes.")
        self._class_index = idx

    def filter_threshold(self, threshold: float,
                         inclusive: bool = False) -> None:
        """Drop all instances with a weight below the given threshold.

        :param threshold: drop everything below this threshold
        :param inclusive: whether to include the threshold
        :raise EmptyLexiconError: if lexicon would be empty after filtering
        """
        temp = pd.DataFrame(self.weights)
        if inclusive:
            new_data = self.data.drop(temp[temp[0] <= threshold].index)
            weights = list(filter(lambda w: w > threshold, self.weights))
        else:
            new_data = self.data.drop(temp[temp[0] < threshold].index)
            weights = list(filter(lambda w: w >= threshold, self.weights))
        if len(new_data) == 0:
            raise EmptyLexiconError("No instances remaining.")

        # update only if safe to do so
        self.data = new_data
        self.weights = weights
        self.data.reset_index(drop=True, inplace=True)

    def delete_with_missing_class(self) -> None:
        """Delete instances without a class."""
        self.data.dropna(subset=self.data.columns[self.class_index],
                         inplace=True)

    def get_classes(self) -> set:
        """Return all class values."""
        return set(self.data.iloc[:, self.class_index])

    def num_classes(self) -> int:
        """Return the number of classes."""
        return len(set(self.data.iloc[:, self.class_index]))

    def class_column_name(self) -> str:
        """Return the name of the class column."""
        return self.data.columns[self.class_index]

    def add_class_column(self, name: str) -> None:
        """Add class column to data."""
        self.data[name] = [None] * self.data.shape[0]

    def set_ignored(self, ignore: list[str], silent=False) -> None:
        """Set ignored columns.

        :param ignore: columns to ignore
        :param silent: if True, ignore if columns not in data
        :raise InvalidColumnError: if not silent and columns not in data
        :raise InvalidColumnError: if class column in ignored columns
        :raise TooFewAttributesError: if less than two considered attributes
            remaining
        """
        self.silent = silent

        if not silent and list(
                filter(lambda x: x not in self.data.columns, ignore)):
            raise InvalidColumnError(
                f"Not all ignored columns ({ignore}) in data (valid "
                f"columns are {list(self.data.columns)}).")
        # class column ignored
        if self.class_column_name() in ignore:
            raise InvalidColumnError(f"Class column {self.class_column_name()} "
                                     f"can't be ignored.")

        # else: filter out superfluous attributes
        if len(set(ignore)) > len(self.data.columns) - 2:
            raise TooFewAttributesError(
                "There must be at least 1 considered attribute beside the class.")
        self.ignored = list(filter(lambda x: x in self.data.columns, set(ignore)))

    def __getitem__(self, idx) -> Instance:
        return Instance(self.data.iloc[idx], self.class_column_name(),
                        self.ignored, self.data.index[idx],  # keep index
                        self.weights[idx], self.silent)

    def __iter__(self):
        for idx, el in self.data.iterrows():
            yield Instance(el, self.class_column_name(), self.ignored, idx,
                           self.weights[idx], self.silent)

    def __len__(self):
        return self.data.shape[0]

    def add(self, row: Instance) -> None:
        """Add an instance to the dataset.

        :param row: instance to add
        """
        self.data = pd.concat([self.data, row.to_frame().T]).reset_index(
            drop=True)
