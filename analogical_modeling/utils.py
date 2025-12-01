"""Utility classes for reading data.

remains from weka:
- Attributes = columns
- Instances = rows
"""

from pathlib import Path

import pandas as pd


class Instance(pd.Series):
    """Instance Representation"""

    # needed for serialization
    _metadata = ["class_index", "ignored", "real_data", "data_idx", "weight"]

    def __init__(self, data: pd.Series, class_column: str,
                 ignore_list: list[str], idx: int, weight: float):
        """

        :param data: Series containing values of the Instance
        :param class_column: name of column containing class value
        :param ignore_list: columns to ignore
        :param idx: index in the dataset
        """
        super().__init__(data)
        self.drop(labels=ignore_list, inplace=True)
        self.class_index = self.keys().get_loc(class_column)
        self.real_data = data
        self.data_idx = idx
        self.weight = weight

    def is_missing(self, idx: int) -> bool:
        """Check if value is missing

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

    def value(self, attr: str):
        """Return the value of the given attribute.

        :param attr: attribute name
        """
        return self.get(attr)

    def string_value(self, idx: int):
        """Return the value of an attributed specified by index.

        :param idx: index of the attribute
        """
        return self.iloc[idx]

    def class_value(self):
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
    """Dataset representation"""

    def __init__(self, atts: list | None = None, weights: str = ""):
        """

        :param atts: if atts is None, call from_csv() to populate the dataset
        :param weights: name of column with weights, if given
        """
        self.ignored: list[str] = []
        if atts is None:
            self.data = pd.DataFrame()
            self.class_index = None
            self.weights = []
            return
        self.data = pd.DataFrame(atts)

        # remove weights from dataset, as they are no features
        if weights:
            self.weights = self.data[weights].tolist()
            self.data.drop(columns=[weights], inplace=True)
        else:
            self.weights = [1] * self.data.shape[0]

        self.class_index = self.num_attributes() - 1

    def from_csv(self, source: str | Path, weights: str = "") -> 'Dataset':
        """Read dataset from csv file

        :param source: path to csv file
        :param weights: name of column with weights, if given
        """
        self.data = pd.read_csv(Path(__file__).parent / source)

        # remove weights from dataset, as they are no features
        if weights:
            self.weights = self.data[weights].tolist()
            self.data.drop(columns=[weights], inplace=True)
        else:
            self.weights = [1] * self.data.shape[0]

        # set class index only afterwards (possibly one column less than before)
        self.class_index = self.num_attributes() - 1

        return self

    def get_instance(self, idx) -> Instance:
        """Get an instance of the given index

        :param idx: index of the instance"""
        return self.data.iloc[idx]

    def num_attributes(self) -> int:
        """Return the number of attributes (whether ignored or not)."""
        return self.data.shape[1]

    def num_counted_attributes(self) -> int:
        """Return the number of attributes that are not ignored."""
        return self.data.shape[1] - len(self.ignored)

    def set_class_index(self, idx: int) -> None:
        """Set the class index.

        :param idx: index of the class
        """
        if idx > self.num_attributes():
            raise ValueError(f"Index out of range: There are only "
                             f"{self.num_attributes()} attributes.")
        self.class_index = idx

    def filter_threshold(self, threshold: float) -> None:
        """Drop all instances with a weight below the given threshold."""
        temp = pd.DataFrame(self.weights)
        if threshold != 0:
            self.data.drop(temp[temp[0] < threshold].index, inplace=True)
            self.weights = list(filter(lambda w: w >= threshold, self.weights))
        else:
            self.data.drop(temp[temp[0] <= threshold].index, inplace=True)
            self.weights = list(filter(lambda w: w > threshold, self.weights))
        self.data.reset_index(drop=True, inplace=True)

    def delete_with_missing_class(self) -> None:
        """Delete instances without a class"""
        self.data.dropna(subset=self.data.columns[self.class_index],
                         inplace=True)

    def get_classes(self) -> set:
        """Return all class values"""
        return set(self.data.iloc[:, self.class_index])

    def num_classes(self) -> int:
        """Return the number of classes."""
        return len(set(self.data.iloc[:, self.class_index]))

    def class_column_name(self) -> str:
        """Return the name of the class column."""
        return self.data.columns[self.class_index]

    def set_ignored(self, ignore: list[str]) -> None:
        """Set ignored columns.

        :param ignore: columns to ignore
        """
        self.ignored = ignore

    def __getitem__(self, idx) -> Instance:
        return Instance(self.data.iloc[idx], self.class_column_name(),
                        self.ignored, self.data.index[idx],  # keep index
                        self.weights[idx])

    def __iter__(self):
        for idx, el in self.data.iterrows():
            yield Instance(el, self.class_column_name(), self.ignored, idx,
                           self.weights[idx])

    def __len__(self):
        return self.data.shape[0]

    def add(self, row: Instance) -> None:
        """Add an instance to the dataset.

        :param row: instance to add
        """
        self.data = pd.concat([self.data, row.to_frame().T]).reset_index(
            drop=True)
