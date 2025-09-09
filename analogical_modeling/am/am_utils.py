"""weka.classifiers.lazy.AM"""
# * **************************************************************************
# * Copyright 2021 Nathan Glenn                                              *
# * Licensed under the Apache License, Version 2.0 (the "License");          *
# * you may not use this file except in compliance with the License.         *
# * You may obtain a copy of the License at                                  *
# *                                                                          *
# * http://www.apache.org/licenses/LICENSE-2.0                               *
# *                                                                          *
# * Unless required by applicable law or agreed to in writing, software      *
# * distributed under the License is distributed on an "AS IS" BASIS,        *
# * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. *
# * See the License for the specific language governing permissions and      *
# * limitations under the License.                                           *
# ****************************************************************************

from os import linesep
from decimal import Decimal, getcontext, ROUND_HALF_EVEN
from copy import deepcopy

# import com.jakewharton.picnic.CellStyle;
# import com.jakewharton.picnic.TextAlignment;


# This class holds constants and methods used in the AM classifier.
# @author nathan.glenn


# An unknown class value.
UNKNOWN = float("nan")

# A non-deterministic outcome, meaning that there is more than one
# possibility.
NONDETERMINISTIC = -1
NONDETERMINISTIC_STRING = "&nondeterministic&"

# A heterogeneous outcome, which means we don't bother with it.
HETEROGENEOUS = -2

LINE_SEPARATOR = linesep


class AMUtils:
    # Picnic library table style used for printing gangs and analogical sets
    # FIXME: translate to python
    # public static final CellStyle REPORT_TABLE_STYLE = new CellStyle.Builder()
    # .setPaddingLeft(1).
    # setPaddingRight(1).
    # setBorderLeft(true).
    # setBorderRight(true).
    # setAlignment(TextAlignment.MiddleRight).build();

    def format_pointer_percentage(self, pointers: int, total_pointers: float, num_decimals: int, add_percent_prefix: bool):
        """

        :param pointers: the number of pointers for the current context
        :param total_pointers: the number of pointers for all contexts
        :param num_decimals: the number of digits to output after the decimal point
        :param add_percent_prefix: true if a percent sign (%) should be prefixed
        :return: a formatted percentage indicating the size of the analogical effect of pointers
        """
        getcontext().prec = num_decimals + 2
        getcontext().rounding = ROUND_HALF_EVEN
        ratio = Decimal(pointers) / Decimal(total_pointers)
        return self.format_percentage(ratio, num_decimals, add_percent_prefix)

    @staticmethod
    def format_percentage(val: Decimal, num_decimals: int, add_percent_prefix: bool):
        """

        :param val: value to be formatted
        :param num_decimals: the number of digits to output after the decimal point
        :param add_percent_prefix: true if a percent sign (%) should be prefixed
        :return: val formatted as a percentage with three decimal places
        """
        percentage = float(val.scaleb(2))
        prefix = "%%" if add_percent_prefix else ""
        return f"{prefix}{percentage:.{num_decimals}f}"


class CsvDoc:
    def __init__(self, headers: list[str], entries: list[list[str]]):
        self.headers = headers
        self.entries = entries


class CsvBuilder:
    """
    Simplify CSV printing by allowing specifying rows as Maps and converting
    automatically to lists of column values in the build method
    """

    def __init__(self):
        self.header: list[str] = []
        self.entries: list[dict[str, str]] = []
        self.default_values: dict[str, str] = {}

    def add_entry(self, entry: dict[str, str]):
        safe_copy = deepcopy(entry)
        self.entries.append(safe_copy)
        for key in entry.keys():
            if key not in self.header:
                self.header.append(key)

    def build(self, sort_rows: bool):
        # List<String> sortedHeader = header.stream().sorted().collect(Collectors.toList());
        sorted_header: list[str] = []
        rows: list[list[str]] = []
        for entry in self.entries:
            row: list[str] = [entry.get(h, self.default_values.get(h, "")) for h in sorted_header]
            rows.append(row)
            if sort_rows:
                rows.sort()
        return CsvDoc(sorted_header, rows)

    def set_default(self, column_name: str, value: str):
        self.default_values[column_name] = value
