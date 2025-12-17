"""Graphical user interface for analogical modeling."""

import sys

import pandas as pd
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog

from analogical_modeling.aml import AnalogicalModeling

root = tk.Tk()


root.title('Analogical Modeling')
#root.configure()
root.minsize(500, 500)
root.maxsize(1000, 1000)
root.geometry("300x300+50+50")

tk.Label(root, text="Configuration").grid()


lexicon = ""
testset = ""
out_dir = Path(".")
out_name = tk.StringVar()
weights = tk.StringVar()
threshold = tk.DoubleVar()
drop_duplicates = tk.BooleanVar()
linear = tk.BooleanVar()
keep_test = tk.BooleanVar()
ignore_unknowns = tk.BooleanVar()
debug = tk.BooleanVar()
mdc = tk.StringVar()

def run():
    # validation
    if not isinstance(lexicon, Path):
        sys.exit("Please specify a lexicon.")
    if not lexicon.exists():
        sys.exit(f"File {lexicon} not found.")
    if testset and not Path(testset).exists():
        sys.exit(f"Test file given, but {testset} not found.")

    # if args.debug:
    #     logger.setLevel(logging.DEBUG)

    am = AnalogicalModeling()
    am.set_linear_count(linear.get())
    am.set_remove_test_exemplar(keep_test.get())
    am.set_ignore_unknowns(ignore_unknowns.get())
    am.set_missing_data_compare(mdc.get())
    am.set_drop_duplicates(drop_duplicates.get())
    am.set_ignore_columns([ignored.get(i) for i in ignored.curselection()])
    am.threshold = threshold.get()
    output = Path(out_dir) / out_name.get()
    try:
        print(am.get_options())
        print(lexicon)
        print(testset)
        print(weights.get())
        print(threshold.get())
        print(output)
        am.run_classifier(lexicon, output.with_suffix(".csv"),
                          testset, weights.get())
    except Exception as e:
        # logger.exception(e)
        raise e

def get_file(button, title):
    filename = Path(filedialog.askopenfilename(initialdir="./..",
                                          title="Select a File",
                                          filetypes=(("CSV files",
                                                      "*.csv"),
                                                     ("all files",
                                                      "*.*"))))

    # Change label contents
    button.configure(text=filename.name)
    return filename

def get_lexicon():
    global lexicon
    lexicon = get_file(lexicon_button, "Lexicon")

    if Path(lexicon).exists():
        # TODO: validation -> Error message
        cols = list(pd.read_csv(lexicon).columns)
        for col in cols:
            ignored.insert(tk.END, col)
            weights_box["values"] = [""]+cols
        ignored.grid()
        weights_box.grid()


def get_testset():
    global testset
    testset = get_file(test_button, "Test")


def update_name(arg=None):
    if out_name.get():
        name = Path(out_dir) / out_name.get()
        out_label.config(text=f"Results will be saved to {name.name}_*")
    else:
        out_label.config(text="")


def get_out_dir():
    global out_dir
    out_dir = filedialog.askdirectory(initialdir="./..",)
    update_name()

tk.Label(root, text="Lexicon file:").grid(column=0, row=1)
lexicon_button = tk.Button(root, text="Select file", command=get_lexicon)
lexicon_button.grid(column=1, row=1)

tk.Label(root, text="Test file (optional):").grid(column=0, row=2)
test_button = tk.Button(root, text="Select file", command=get_testset)
test_button.grid(column=1, row=2)

tk.Label(root, text="Output directory:").grid(column=0, row=3)
out_button = tk.Button(root, text="Select directory", command=get_out_dir)
out_button.grid(column=1, row=3)
tk.Label(root, text="Prefix for output:").grid(column=0, row=4)
out_name = tk.Entry(root, textvariable=out_name)
out_name.grid(column=1, row=4)
out_name.bind("<KeyRelease>", update_name)  # TODO: only if key released in Entry
out_label = tk.Label(root)
out_label.grid(column=0, row=5)

frame = tk.Frame(root)
frame.grid()
ignored = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=4)
# scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
# scrollbar.config(command=ignored.yview)
# scrollbar.grid()
weights_box = ttk.Combobox(frame, values=[""], textvariable=weights)
weights_box.current(0)

tk.Spinbox(root, increment=0.1, from_=0.0, to=100.0, textvariable=threshold).grid()

tk.Label(root, text="Additional Options").grid()
tk.Checkbutton(root, text="drop duplicated instances", variable=drop_duplicates).grid()
tk.Radiobutton(root, text="quadratic count", value=0, variable=linear).grid()
tk.Radiobutton(root, text="linear count", value=1, variable=linear).grid(column=1, row=5)
tk.Checkbutton(root, text="keep test exemplar in training set", onvalue=0, offvalue=1).grid()
tk.Checkbutton(root, text="ignore attributes with unknown values", variable=ignore_unknowns).grid()
tk.Checkbutton(root, text="debug mode", variable=debug).grid()

mdc_selection = ttk.Combobox(root, values=["match", "mismatch", "variable"], textvariable=mdc)
mdc_selection.current(2)
mdc_selection.grid()

tk.Button(root, text="Run algorithm", command=run).grid()

root.mainloop()
