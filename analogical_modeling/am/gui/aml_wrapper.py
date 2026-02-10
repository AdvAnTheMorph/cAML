"""Wrapper for running AML with GUI"""

import logging
import threading
import tkinter as tk
from pathlib import Path
from queue import Queue

import pandas as pd

from analogical_modeling.aml import AnalogicalModeling, logger


class AMWrapper:
    """Wrapper for Analogical Modelling with GUI."""

    def __init__(self):
        self.am = AnalogicalModeling()
        self.lexicon = ""
        self.class_idx = -1
        self.testset = None
        self.out = ""
        self.out_dir = Path("../..").resolve()
        self.out_name = tk.StringVar()
        self.weights = ""
        self.threshold = tk.DoubleVar()
        self.inc_th = tk.BooleanVar()
        self.threshold.trace_add('write', self.validate_threshold)
        self.drop_duplicates = tk.BooleanVar()
        self.linear = tk.BooleanVar()
        self.keep_test = tk.BooleanVar()
        self.ignore_unknowns = tk.BooleanVar()
        self.debug = tk.BooleanVar()
        self.mdc = tk.StringVar()
        self.ignored = []

        self.thread = None
        self.res = None
        self.queue = Queue()

        self.exit_reason = None

    def adjust_data_to_class_idx(self) -> pd.DataFrame:
        """Permute lexicon such that class column comes last."""
        if Path(self.lexicon).suffix == ".xlsx":
            data = pd.read_excel(self.lexicon)
        else:
            data = pd.read_csv(self.lexicon)

        cols = data.columns.tolist()
        if self.class_idx == -1:
            self.class_idx = len(cols) - 1
        if self.class_idx != len(cols)-1:
            before, after = cols[:self.class_idx], cols[self.class_idx+1:]
            data = data.loc[:, before + after + [cols[self.class_idx]]]
        return data

    def validate_threshold(self, *_args) -> None:
        """Make sure that threshold non-negative float."""
        try:
            value = float(self.threshold.get())
            if value < 0:
                self.threshold.set(0.0)  # reset
        except (ValueError, tk.TclError):
            self.threshold.set(0.0)  # reset

    def validate(self) -> str:
        """Check that all required parameters are valid.

        :return: string containing all problem descriptions (or empty string)"""
        problems = ""
        if not self.lexicon:
            print("No lexicon provided")
            problems += "Lexicon file not provided.\n"
        elif not Path(self.lexicon).exists():
            problems += "Lexicon file does not exist.\n"
        if self.testset and not Path(self.testset).exists():
            print("Testset doesn't exist")
            problems += "Test file given, but does not exist.\n"
        return problems

        # TODO (not validation)
        # - error messages when running

    def cancel(self) -> None:
        """Stop AML"""
        self.am.cancel_event = True

        # make sure process ends
        if self.thread.is_alive():
            self.thread.join()

    def run(self) -> None:
        """Run AML"""
        try:
            lex = self.adjust_data_to_class_idx()
            self.res = self.am.run_classifier(lex,
                                              self.out or None,
                                              self.testset,
                                              self.weights)
        except Exception as e:
            self.exit_reason = e

    def run_in_thread(self) -> str:
        """Run AML in separate thread"""
        self.exit_reason = None

        self.am.set_linear_count(self.linear.get())
        self.am.set_remove_test_exemplar(self.keep_test.get())
        self.am.set_ignore_unknowns(self.ignore_unknowns.get())
        self.am.set_missing_data_compare(self.mdc.get())
        self.am.set_drop_duplicates(self.drop_duplicates.get())
        self.am.set_ignore_columns(self.ignored)
        self.am.threshold = (self.threshold.get(), self.inc_th.get())
        self.am.gui_queue = self.queue = Queue()

        if self.debug.get():
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        print(self.am.get_options())
        print(f"Saving to {self.out or '--'}")

        errors = self.validate()
        if not errors:
            # reset both
            self.res = None
            self.am.cancel_event = False

            # run in separate thread
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            return ""
        return errors
