"""Graphical user interface for analogical modeling."""

import os
import sys
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk, filedialog

import pandas as pd

am_path = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(am_path, '..'))
from analogical_modeling.am.gui.aml_wrapper import AMWrapper
import analogical_modeling.am.gui.gui_utils as utils
from analogical_modeling.am.gui.vis import TableVisualization, \
    MatrixVisualization

root = tk.Tk()

# def center_window(window):
#     window.update_idletasks()
#     width = window.winfo_width()
#     height = window.winfo_height()
#     screen_width = window.winfo_screenwidth()
#     screen_height = window.winfo_screenheight()
#     x = (screen_width - width) // 2
#     y = (screen_height - height) // 2
#     window.geometry(f"{width}x{height}+{x}+{y}")

root.title('Analogical Modeling')
root.minsize(600, 700)
root.geometry("800x700+50+50")

wrapper = AMWrapper()


class GUI:
    def __init__(self, root):
        self.root = root

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        main_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(main_tab, text="Configuration")

        self.conf = utils.MainConfigFrame(self, main_tab, wrapper)

        ttk.Separator(main_tab, orient="horizontal").pack(expand=True,
                                                          fill=tk.BOTH)

        self.outs = utils.OutputSelection(main_tab)

        ttk.Separator(main_tab, orient="horizontal").pack(expand=True,
                                                          fill=tk.BOTH)

        # additional options
        tk.Label(main_tab, text="Additional Options", pady=10,
                 font=("", 13)).pack(
            expand=True,
            fill=tk.X)
        options_frame = tk.Frame(main_tab, width=utils.FLEN)
        options_frame.pack(expand=True, fill=tk.Y)

        # count strategy
        self.count = utils.CountFrame(options_frame, wrapper)

        # mdc
        mdc_frame = tk.Frame(options_frame, width=utils.LEN * 2)
        mdc_frame.pack(expand=True, fill=tk.BOTH)
        tk.Label(mdc_frame,
                 justify=tk.LEFT,
                 anchor=tk.W,
                 text=f"{'Consider missing values as:':{utils.LEN}s}\t").pack(
            side=tk.LEFT,
            expand=True, fill=tk.X)
        mdc_selection = ttk.Combobox(mdc_frame,
                                     values=["match", "mismatch", "variable"],
                                     textvariable=wrapper.mdc, state="readonly")
        mdc_selection.current(2)
        mdc_selection.pack(side=tk.LEFT, expand=True, anchor=tk.W)
        utils.ToolTip(mdc_selection,
                      "The strategy to use when comparing missing attribute values "
                      "\nwith other values while filling subcontexts and supracontexts")

        # rest
        rest_frame = tk.Frame(options_frame)
        rest_frame.pack(expand=True, anchor=tk.CENTER)  # don't fill
        utils.CheckboxFrames(rest_frame, wrapper)

        self.run_stop = utils.StartFrame(self, main_tab, wrapper)

    def run(self):
        """Run AML through wrapper"""
        # runs in separate thread
        try:
            print(wrapper.weights)
            wrapper.class_idx = self.conf.cls.get()
            wrapper.ignored = self.conf.ignored.list_selected()

            if wrapper.class_idx in self.conf.ignored.box.curselection():
                messagebox.showerror("Class column ignored",
                                     "The class column cannot be ignored.")
                return False
            if wrapper.weights in wrapper.ignored:
                messagebox.showerror("Weights column ignored",
                                     "The weights column cannot be ignored.")
                return False
            if wrapper.weights == self.conf.cls.get(wrapper.class_idx):
                messagebox.showerror("Weights column is class column",
                                     "The weights column cannot be the class "
                                     "column.")
                return False

            errors = wrapper.run_in_thread()
            if not errors:
                return True
            messagebox.showerror("Missing parameters", errors)
            return False
        except Exception as e:
            raise e

    def on_completion(self):
        """Plot matrix and output files"""
        acc, matrix, files = wrapper.res
        if matrix is not None:
            try:
                self.vis_matrix(matrix, acc)
            except Exception as e:
                messagebox.showerror("An error occurred",
                                     f"The Matrix could not be displayed due "
                                     f"to \n{e}")
        try:
            self.vis_files(files)
        except Exception as e:
            messagebox.showerror("An error occurred",
                                 f"The output files could not be displayed "
                                 f"due to \n{e}")

    @staticmethod
    def clear_frame(frame):
        """Remove all widgets from a frame"""
        for widget in frame.winfo_children():
            widget.destroy()

    def vis_matrix(self, matrix, acc):
        if not hasattr(root, "conf_mat_tab"):
            root.conf_mat_tab = ttk.Frame(self.notebook)
            self.notebook.add(root.conf_mat_tab, text="Confusion Matrix")
        else:
            # Update existing tab
            self.clear_frame(root.conf_mat_tab)
        result_label = tk.Label(root.conf_mat_tab,
                                text=f"Accuracy: {round(acc * 100, 2)}%")
        result_label.pack()
        MatrixVisualization(root.conf_mat_tab, matrix, wrapper.out)

    def make_table(self, parent, file_):
        res_frame = tk.Frame(parent)
        res_frame.pack(expand=True, fill=tk.BOTH)
        TableVisualization(res_frame, file_)

    def vis_files(self, files):
        """Visualize tables"""
        if self.outs.gangs.get():
            if not hasattr(root, "gangs"):
                root.gangs = ttk.Frame(self.notebook)
                self.notebook.add(root.gangs, text="Gang Effects")
            else:
                # Update existing tab
                self.clear_frame(root.gangs)
            self.make_table(root.gangs, files[0])

        if self.outs.analog.get():
            if not hasattr(root, "analog"):
                root.analog = ttk.Frame(self.notebook)
                self.notebook.add(root.analog, text="Analogical Sets")
            else:
                # Update existing tab
                self.clear_frame(root.analog)
            self.make_table(root.analog, files[1])

        if self.outs.distr.get():
            if not hasattr(root, "distr"):
                root.distr = ttk.Frame(self.notebook)
                self.notebook.add(root.distr, text="Distribution")
            else:
                # Update existing tab
                self.clear_frame(root.distr)
            self.make_table(root.distr, files[2])


if __name__ == "__main__":
    # FIXME: pops up at base position first
    # center_window(root)
    GUI(root)
    root.mainloop()
