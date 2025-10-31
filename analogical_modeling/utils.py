"""Utility classes for reading data.

remains from weka:
- Attributes = columns
- Instances = rows
"""

from pathlib import Path

import pandas as pd


class Instance(pd.Series):
    _metadata = ["class_index", "ignored", "real_data", "data_idx"]

    def __init__(self, data: pd.Series, class_column: str, ignore_list: list[str], idx: int):
        super().__init__(data)
        self.drop(labels=ignore_list, inplace=True)
        self.class_index = self.keys().get_loc(class_column)
        self.real_data = data
        self.data_idx = idx

    def is_missing(self, idx: int) -> bool:
        # return self.isna().iloc[idx]
        return self.iloc[idx] == "="

    def num_attributes(self) -> int:
        """Return the number of considered attributes."""
        return self.shape[0]

    def num_all_attributes(self) -> int:
        """Return the number of attributes, including ignored ones."""
        return self.real_data.shape[0]

    def attribute_name(self, idx: int):
        return self.index[idx]

    def value(self, val: str):
        return self.get(val)

    def string_value(self, idx: int):
        return self.iloc[idx]

    def class_value(self):
        return self.iloc[self.class_index]

    def __str__(self):
        return f"{','.join(map(str, self.array))}"  #,\u007b{self.num_attributes()}\u007d"

    def __hash__(self):
        return int(pd.util.hash_pandas_object(self, index=False).sum())+hash(37*self.data_idx)

    def __eq__(self, other):
        if isinstance(other, Instance):
            return self.values.all() == other.values.all()
        return super().__eq__(other)


class Dataset:
    def __init__(self, atts: list|None = None):
        self.ignored = []
        if atts is None:
            self.data = None
            self.class_index = None
            return
        self.data = pd.DataFrame(atts)
        self.class_index = self.num_attributes() - 1

    def from_csv(self, source: str|Path):
        self.data = pd.read_csv(Path(__file__).parent / source)
        self.class_index = self.num_attributes() - 1
        return self

    def get_instance(self, idx):
        return self.data.iloc[idx]

    def num_attributes(self) -> int:
        return self.data.shape[1]

    def num_counted_attributes(self) -> int:
        return self.data.shape[1] - len(self.ignored)

    def set_class_index(self, idx: int):
        if idx > self.num_attributes():
            raise ValueError(f"Index out of range: There are only {self.num_attributes()} attributes.")
        self.class_index = idx

    def delete_with_missing_class(self):
        return self.data.dropna(subset=self.data.columns[self.class_index])

    def get_classes(self):
        return set(self.data.iloc[:, self.class_index])

    def num_classes(self):
        return len(set(self.data.iloc[:, self.class_index]))

    def class_column_name(self):
        return self.data.columns[self.class_index]

    def set_ignored(self, ignore: list[str]):
        self.ignored = ignore

    def __getitem__(self, idx) -> Instance:
        return Instance(self.data.iloc[idx], self.class_column_name(), self.ignored, idx)

    def __iter__(self):
        for idx, el in self.data.iterrows():
            yield Instance(el, self.class_column_name(), self.ignored, idx)

    def __len__(self):
        return self.data.shape[0]

    def add(self, row: Instance):
        self.data = pd.concat([self.data, row.to_frame().T]).reset_index(drop=True)
