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

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

main_tab = ttk.Frame(notebook, padding=10)
notebook.add(main_tab, text="Configuration")

tk.Label(main_tab, text="Configuration", font=("", 15)).pack(expand=True,
                                                             fill=tk.BOTH)

wrapper = AMWrapper()


class GUI:
    def __init__(self, root):
        self.root = root

    def run(self):
        """Run AML through wrapper"""
        # runs in separate thread
        try:
            print(wrapper.weights)
            wrapper.class_idx = cls.get()
            wrapper.ignored = ignored.list_selected()

            if wrapper.class_idx in ignored.box.curselection():
                messagebox.showerror("Class column ignored",
                                     "The class column cannot be ignored.")
                return False
            if wrapper.weights in wrapper.ignored:
                messagebox.showerror("Weights column ignored",
                                     "The weights column cannot be ignored.")
                return False
            if wrapper.weights == cls.get(wrapper.class_idx):
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
            self.vis_matrix(matrix, acc)
        self.vis_files(files)

    @staticmethod
    def clear_frame(frame):
        """Remove all widgets from a frame"""
        for widget in frame.winfo_children():
            widget.destroy()

    def vis_matrix(self, matrix, acc):
        if not hasattr(root, "conf_mat_tab"):
            root.conf_mat_tab = ttk.Frame(notebook)
            notebook.add(root.conf_mat_tab, text="Confusion Matrix")
        else:
            # Update existing tab
            self.clear_frame(root.conf_mat_tab)
        result_label = tk.Label(root.conf_mat_tab,
                                text=f"Accuracy: {acc * 100}%")
        result_label.pack()
        MatrixVisualization(root.conf_mat_tab, matrix, wrapper.out)

    def make_table(self, parent, file_):
        res_frame = tk.Frame(parent)
        res_frame.pack(expand=True, fill=tk.BOTH)
        TableVisualization(res_frame, file_)

    def vis_files(self, files):
        """Visualize tables"""
        if outs.gangs.get():
            if not hasattr(root, "gangs"):
                root.gangs = ttk.Frame(notebook)
                notebook.add(root.gangs, text="Gang Effects")
            else:
                # Update existing tab
                self.clear_frame(root.gangs)
            self.make_table(root.gangs, files[0])

        if outs.analog.get():
            if not hasattr(root, "analog"):
                root.analog = ttk.Frame(notebook)
                notebook.add(root.analog, text="Analogical Sets")
            else:
                # Update existing tab
                self.clear_frame(root.analog)
            self.make_table(root.analog, files[1])

        if outs.distr.get():
            if not hasattr(root, "distr"):
                root.distr = ttk.Frame(notebook)
                notebook.add(root.distr, text="Distribution")
            else:
                # Update existing tab
                self.clear_frame(root.distr)
            self.make_table(root.distr, files[2])


gui = GUI(root)


def get_file(button):
    filename = filedialog.askopenfilename(initialdir="./..",
                                          title="Select a File",
                                          filetypes=(("CSV files",
                                                      "*.csv"),
                                                     ("all files",
                                                      "*.*")))
    if not filename:
        return None
    # Change label contents
    button.configure(text=f"Selected: {Path(filename).name}")
    return filename


def get_lexicon():
    wrapper.lexicon = get_file(lexicon_button)
    if not wrapper.lexicon or not Path(wrapper.lexicon).exists():
        return
    cols = list(pd.read_csv(wrapper.lexicon).columns)

    cls.fill(cols)
    cls.vis()

    ignored.clear()   # remove old elements
    ignored.fill(cols)  # refill
    ignored.vis()

    weights.fill(cols)
    weights.vis()
    weights.threshold_frame.invis()  # as no weight column selected


def get_testset():
    wrapper.testset = get_file(test_button) or ""
    if wrapper.testset:
        del_test_button.pack(side=tk.RIGHT, after=test_button)


def clear_test():
    wrapper.testset = ""
    del_test_button.pack_forget()
    test_button.configure(text="Select file")


# Lexicon
lex_spec_frame = tk.Frame(main_tab)
tk.Label(lex_spec_frame, text="Data", font=("", 12), pady=10).pack()
lex_spec_frame.pack(fill=tk.BOTH, expand=True)
lex_frame = tk.Frame(lex_spec_frame)
lex_frame.pack(expand=True, fill=tk.X)
tk.Label(lex_frame, text="Lexicon file:").pack(side=tk.LEFT, expand=True,
                                               fill=tk.X)
lexicon_button = tk.Button(lex_frame, text="Select file", command=get_lexicon)
lexicon_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)

# configurations once lexicon has been selected
conf_frame = tk.Frame(lex_spec_frame)
conf_frame.pack(side=tk.BOTTOM, expand=True, fill=tk.X)
cls = utils.ClsFrame(conf_frame, wrapper)
ignored = utils.IgnoreFrame(conf_frame)
weights = utils.WeightsFrame(conf_frame, wrapper)

# Test set
test_frame = tk.Frame(main_tab)
test_frame.pack(expand=True, fill=tk.X)
tk.Label(test_frame, text="Test file (optional):").pack(side=tk.LEFT,
                                                        expand=True, fill=tk.X)
test_button = tk.Button(test_frame, text="Select file", command=get_testset)
test_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)
del_test_button = tk.Button(test_frame, text="Clear file", command=clear_test)

# Output
utils.OutFrame(main_tab, wrapper)

ttk.Separator(main_tab, orient="horizontal").pack(expand=True, fill=tk.BOTH)

outs = utils.OutputSelection(main_tab)

ttk.Separator(main_tab, orient="horizontal").pack(expand=True, fill=tk.BOTH)

tk.Label(main_tab, text="Additional Options", pady=10, font=("", 12)).pack(
    expand=True,
    fill=tk.X)

# count strategy
count = utils.CountFrame(main_tab, wrapper)

# mdc
mdc_frame = tk.Frame(main_tab)
mdc_frame.pack(expand=True, fill=tk.X)
tk.Label(mdc_frame, text="Consider missing values as:").pack(side=tk.LEFT,
                                                             expand=True,
                                                             fill=tk.X)
mdc_selection = ttk.Combobox(mdc_frame,
                             values=["match", "mismatch", "variable"],
                             textvariable=wrapper.mdc, state="readonly")
mdc_selection.current(2)
mdc_selection.pack(side=tk.LEFT, expand=True)

# rest
rest_frame = tk.Frame(main_tab)
rest_frame.pack(expand=True, anchor=tk.CENTER)  # don't fill
utils.CheckboxFrames(rest_frame, wrapper)

run_stop = utils.StartFrame(gui, main_tab, wrapper)

# FIXME: pops up at base position first
# center_window(root)
root.mainloop()
