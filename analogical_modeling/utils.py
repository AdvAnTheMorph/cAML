"""Utility functions for reading data.


remains from weka:
- Attributes = columns
- Instances = rows
"""

from pathlib import Path

import pandas as pd


class Instance(pd.Series):
    def __init__(self, data: pd.Series, class_index: int):
        super().__init__(data)
        self._class_index = class_index

    def class_index(self):
        return self._class_index

    def is_missing(self, idx: int) -> bool:
        # TODO: until now, missing = "?", what about missing = None
        # return self.isna().iloc[idx]
        return self.isna().iloc[idx] or self.iloc[idx] == "?"

    def num_attributes(self) -> int:
        return self.shape[0]

    def attribute_name(self, idx: int):
        return self.index[idx]

    def value(self, val: str):
        return self.get(val)

    def string_value(self, idx: int):
        return self.iloc[idx]

    def class_value(self):
        return self.iloc[self.class_index()]

    def __str__(self):
        return f"{','.join(map(str, self.array))}"  #,\u007b{self.num_attributes()}\u007d"

    def __hash__(self):
        return int(pd.util.hash_pandas_object(self, index=False).sum())

    def __eq__(self, other):
        if isinstance(other, Instance):
            return self.values.all() == other.values.all()
        return super().__eq__(other)


class Dataset:
    def __init__(self, atts: list|None = None):
        if atts is None:
            self.data = None
            self.class_index = None
            return
        self.data = pd.DataFrame(atts)
        self.class_index = self.num_attributes() - 1

    def from_csv(self, source: str|Path):
        self.data = pd.read_csv(Path(__file__).parent / source)
        self.class_index = self.data.columns.get_loc("class")
        return self

    def get_instance(self, idx):
        return self.data.iloc[idx]

    def num_attributes(self) -> int:
        return self.data.shape[1]

    def set_class_index(self, idx: int):
        if idx > self.num_attributes():
            raise ValueError(f"Index out of range: There are only {self.num_attributes()} attributes.")
        self.class_index = idx

    def delete_with_missing_class(self):
        return self.data.dropna(subset=self.data.columns[self.class_index])

    def num_classes(self):
        return len(set(self.data.iloc[:, self.class_index]))

    def __getitem__(self, idx) -> Instance:
        return Instance(self.data.iloc[idx], self.class_index)

    def __iter__(self):
        for _, el in self.data.iterrows():
            yield Instance(el, self.class_index)

    def __len__(self):
        return self.data.shape[0]

    def add(self, row: Instance):
        self.data = pd.concat([self.data, row]).reset_index(drop=True)



if __name__ == "__main__":
    file_ = "data/finnverb.csv"
    # file_ = "data/ch3example.csv"
    # file_ = "data/soybean.csv"
    data = Dataset().from_csv(file_)
    # print(file_)
    # print(file_.shape)
    # print(file_.columns)
    # print(type(data[3]))
    # print(data[3])
    # print(data[3].class_index())
    # print(data.data)
    # print(data[3])
    # print(data[3].num_attributes())
    # print(data[3].iloc[5])
    # print(data[3].is_missing(5))
    # print(data[3].attribute_name(5))
    # data.data.drop(data.data.columns[[0, 1]], axis=1, inplace=True)
    # print(data.data)
    # print(data[3].get("5"))
    # print(hash(data[3]))
    print(data.data)
    data.set_class_index(3)
    print(data.data)
    print(data.delete_with_missing_class())

    # print(pd.read_csv("data/soybean.csv"))
