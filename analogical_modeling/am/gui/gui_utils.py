"""Utility functions for Graphical User Interface"""

import threading
import tkinter as tk
from pathlib import Path

from analogical_modeling.aml import AnalogicalModeling


MISSING_LEXICON = 0x0001
INVALID_LEXICON = 0x0002
INVALID_TEST = 0x0004
MISSING_OUT = 0x0008


class AMWrapper:
    """Wrapper for Analogical Modelling with GUI"""

    def __init__(self):
        self.am = AnalogicalModeling()
        self.lexicon = ""
        self.testset = ""
        self.out = ""
        self.out_dir = Path("../..")
        self.out_name = tk.StringVar()
        self.weights = ""
        self.threshold = tk.DoubleVar()
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

    def validate_threshold(self, *_args):
        """Make sure that threshold non-negative float"""
        try:
            value = float(self.threshold.get())
            if value < 0:
                self.threshold.set(0.0)  # reset
        except (ValueError, tk.TclError):
            self.threshold.set(0.0)  # reset

    def validate(self) -> int:
        """Check that all required parameters are valid"""
        problems = 0x0000
        if not self.lexicon:
            print("No lexicon provided")
            problems |= MISSING_LEXICON
        elif not Path(self.lexicon).exists():
            problems |= INVALID_LEXICON
        if self.testset and not Path(self.testset).exists():
            print("Testset doesn't exist")
            problems |= INVALID_TEST
        if not self.out:
            print("No output path provided")
            problems |= MISSING_OUT
        return problems

    def cancel(self):
        """Stop AML"""
        self.am.cancel_event = True

        # make sure process ends
        if self.thread.is_alive():
            self.thread.join()

    def run(self) -> None:
        """Run AML"""
        self.res = self.am.run_classifier(self.lexicon,
                                          Path(self.out).with_suffix(".csv"),
                                          self.testset,
                                          self.weights)

    def run_in_thread(self) -> int:
        """Run AML in separate thread"""
        self.am.set_linear_count(self.linear.get())
        self.am.set_remove_test_exemplar(self.keep_test.get())
        self.am.set_ignore_unknowns(self.ignore_unknowns.get())
        self.am.set_missing_data_compare(self.mdc.get())
        self.am.set_drop_duplicates(self.drop_duplicates.get())
        self.am.set_ignore_columns(self.ignored)
        self.am.threshold = self.threshold.get()

        print(self.am.get_options())

        errors = self.validate()
        if not errors:
            # reset both
            self.res = None
            self.am.cancel_event = False

            # run in separate thread
            self.thread = threading.Thread(target=self.run)
            self.thread.start()
            return 0
        return errors
