"""Utility functions for Graphical User Interface"""

from pathlib import Path
import threading

import tkinter as tk

from analogical_modeling.aml import AnalogicalModeling


class FileValidator:
    """Validates files"""
    def __init__(self, required: bool=True, write: bool=False):
        self.required = required
        self.write = write

    def __set__(self, instance, value: str):
        if not value:
            print("No file provided")
            if not self.required:  # FIXME: deletes without updating widget
                instance._x = ""
        elif not self.write and not Path(value).exists():
            print("File doesn't exist")
        elif not self.write and not Path(value).is_file():
            print("Invalid file provided (not a file)")
        else:
            instance._x = value

    def __get__(self, instance, instance_type=None):
        return instance._x


class AMWrapper:
    """Wrapper for Analogical Modelling with GUI"""
    lexicon = FileValidator(True)
    testset = FileValidator(False)
    out = FileValidator(True, True)

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

    def validate_threshold(self, *args):
        try:
            value = float(self.threshold.get())
            if value < 0:
                self.threshold.set(0.0)  # reset
        except (ValueError, tk.TclError):
            self.threshold.set(0.0)  # reset

    def validate(self):  # FIXME: takes several tries to save lexicon
        if not self.lexicon or not Path(self.lexicon).exists():
            print("No lexicon provided")
            return False
        if self.testset and not Path(self.testset).exists():
            print("Testset doesn't exist")
            return False
        if not self.out:
            print("No output path provided")
            return False
        print(self.out)
        return True

    def cancel(self):
        self.am.cancel_event = True

        # make sure process ends
        if self.thread.is_alive():
            self.thread.join()

    def run_in_thread(self):
        self.res = self.am.run_classifier(self.lexicon,
                                          Path(self.out).with_suffix(".csv"),
                                          self.testset,
                                          self.weights)

    def run(self):
        """Run AM"""
        self.am.set_linear_count(self.linear.get())
        self.am.set_remove_test_exemplar(self.keep_test.get())
        self.am.set_ignore_unknowns(self.ignore_unknowns.get())
        self.am.set_missing_data_compare(self.mdc.get())
        self.am.set_drop_duplicates(self.drop_duplicates.get())
        self.am.set_ignore_columns(self.ignored)
        self.am.threshold = self.threshold.get()

        print(self.am.get_options())

        if self.validate():
            # reset both
            self.res = None
            self.am.cancel_event = False

            # run in separate thread
            self.thread = threading.Thread(target=self.run_in_thread)
            self.thread.start()
            return True
        return False
