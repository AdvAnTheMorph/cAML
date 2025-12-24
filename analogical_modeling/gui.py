"""Graphical user interface for analogical modeling."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk, filedialog

import pandas as pd

import analogical_modeling.am.gui.gui_utils as gui_utils
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
# root.configure()
root.minsize(600, 550)
root.geometry("300x300+50+50")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

main_tab = ttk.Frame(notebook)
notebook.add(main_tab, text="Configuration")

tk.Label(main_tab, text="Configuration").pack(expand=True, fill=tk.BOTH)

wrapper = gui_utils.AMWrapper()


def make_error_msg(errors):
    msg = ""
    if errors & gui_utils.MISSING_LEXICON:
        msg += "Lexicon file not provided.\n"
    if errors & gui_utils.INVALID_LEXICON:
        msg += "Lexicon file does not exist.\n"
    if errors & gui_utils.INVALID_TEST:
        msg += "Test file given, but does not exist.\n"
    if errors & gui_utils.MISSING_OUT:
        msg += "Output not specified.\n"
    return msg


def run_button():
    # runs in separate thread
    try:
        wrapper.ignored = [ignored.get(i) for i in ignored.curselection()]
        errors = wrapper.run_in_thread()
        if not errors:
            cancel_button.pack(expand=True, fill=tk.X)
            start_button.pack_forget()
            root.after(100, check_completion)
        else:
            messagebox.showerror("Missing parameters", make_error_msg(errors))
    except Exception as e:
        raise e


def stop_aml():
    # stop thread
    wrapper.cancel()
    messagebox.showinfo("Stop AML", "Stopping AML")
    cancel_button.pack_forget()
    start_button.pack(expand=True, fill=tk.X)


def check_completion():
    if wrapper.res:
        on_completion()
    else:
        root.after(100, check_completion)


def make_table(parent, file_):
    res_frame = tk.Frame(parent)
    res_frame.pack(expand=True, fill=tk.BOTH)
    TableVisualization(res_frame, file_)


def vis_files(files):
    if not hasattr(root, "gangs"):
        root.gangs = ttk.Frame(notebook)
        notebook.add(root.gangs, text="Gangs")
        make_table(root.gangs, files[0])
    else:
        # Update existing tab
        for widget in root.gangs.winfo_children():
            widget.destroy()
        make_table(root.gangs, files[0])
    if not hasattr(root, "analog"):
        root.analog = ttk.Frame(notebook)
        notebook.add(root.analog, text="Analogical Sets")
        make_table(root.analog, files[1])
    else:
        # Update existing tab
        for widget in root.analog.winfo_children():
            widget.destroy()
        make_table(root.analog, files[1])
    if not hasattr(root, "distr"):
        root.distr = ttk.Frame(notebook)
        notebook.add(root.distr, text="Distribution")
        make_table(root.distr, files[2])
    else:
        # Update existing tab
        for widget in root.distr.winfo_children():
            widget.destroy()
        make_table(root.distr, files[2])


def vis_matrix(matrix, acc):
    if not hasattr(root, "conf_mat_tab"):
        root.conf_mat_tab = ttk.Frame(notebook)
        notebook.add(root.conf_mat_tab, text="Confusion Matrix")
        result_label = tk.Label(root.conf_mat_tab,
                                text=f"Accuracy: {acc * 100}%")
        result_label.pack()
        MatrixVisualization(root.conf_mat_tab, matrix)
    else:
        # Update existing tab
        for widget in root.conf_mat_tab.winfo_children():
            widget.destroy()
        result_label = tk.Label(root.conf_mat_tab,
                                text=f"Accuracy: {acc * 100}%")
        result_label.pack()
        MatrixVisualization(root.conf_mat_tab, matrix)


def on_completion():
    cancel_button.pack_forget()
    start_button.pack(expand=True, fill=tk.X)
    acc, matrix, files = wrapper.res

    if matrix is not None:
        vis_matrix(matrix, acc)
    vis_files(files)


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
    ignored.delete(0, tk.END)  # remove old elements
    for col in cols:
        ignored.insert(tk.END, col)
        weights_box["values"] = [""] + cols
    ignored_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
    weights_frame.pack(side=tk.TOP, expand=True, fill=tk.X)


def val_and_vis(_arg=None):
    if not weights_box.get():  # = no weights
        threshold_frame.pack_forget()
        return

    # validate and set
    temp = pd.read_csv(wrapper.lexicon)
    value = weights_box.get()
    if pd.api.types.is_numeric_dtype(temp[value]):
        wrapper.weights = value
        threshold_frame.pack(side=tk.BOTTOM, fill=tk.X, expand=True)
    else:
        threshold_frame.pack_forget()
        messagebox.showerror(f"Invalid weights column '{value}'",
                             "The selected column does not contain "
                             "numeric values.")
        weights_box.current(0)


def get_testset():
    wrapper.testset = get_file(test_button) or ""
    if wrapper.testset:
        del_test_button.pack(side=tk.RIGHT, after=test_button)


def clear_test():
    wrapper.testset = ""
    del_test_button.pack_forget()
    test_button.configure(text="Select file")


def update_name(_arg=None):
    if wrapper.out_name.get():
        print(wrapper.out_dir, wrapper.out_name.get())
        wrapper.out = Path(wrapper.out_dir or ".") / wrapper.out_name.get()
        out_label.config(
            text=f"Results will be saved to "
                 f"{Path(wrapper.out_dir).name or '.'}/{out_name.get()}_*")
    else:
        out_label.config(text="")


def get_out_dir():
    wrapper.out_dir = filedialog.askdirectory(initialdir="./..", )
    update_name()
    if wrapper.out_dir:
        out_button.configure(text=f"Selected: */{Path(wrapper.out_dir).name}/")


def validate_numeric(val):
    if val == "":  # Allow empty string (deletion)
        return True
    try:
        return float(val) >= 0.0
    except ValueError:
        return False


# Lexicon
lex_spec_frame = tk.Frame(main_tab)
lex_spec_frame.pack(fill='both', expand=True)
lex_frame = tk.Frame(lex_spec_frame)
lex_frame.pack(expand=True, fill=tk.X)
tk.Label(lex_frame, text="Lexicon file:").pack(side=tk.LEFT, expand=True,
                                               fill=tk.X)
lexicon_button = tk.Button(lex_frame, text="Select file", command=get_lexicon)
lexicon_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)

# configurations once lexicon has been selected
frame = tk.Frame(lex_spec_frame)
frame.pack(side=tk.BOTTOM, expand=True, fill=tk.X)
ignored_frame = tk.Frame(frame)
tk.Label(ignored_frame, text="Select columns to ignore:").pack(side=tk.LEFT,
                                                               expand=True,
                                                               fill=tk.X)
ignored = tk.Listbox(ignored_frame, selectmode=tk.MULTIPLE, height=4)
ignored.pack(side=tk.RIGHT, expand=True, fill=tk.X)
# scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
# scrollbar.config(command=ignored.yview)
# scrollbar.grid()
weights_frame = tk.Frame(frame)
tk.Label(weights_frame, text="Select weights column (if any):").pack(
    side=tk.LEFT, expand=True, fill=tk.X)
weights_box = ttk.Combobox(weights_frame, values=[""], state="readonly")
weights_box.bind("<<ComboboxSelected>>", val_and_vis)
weights_box.current(0)
weights_box.pack(side=tk.RIGHT, expand=True, fill=tk.X)

threshold_frame = tk.Frame(frame)
tk.Label(threshold_frame, text="Ignore instances with weights below:").pack(
    side=tk.LEFT, expand=True, fill=tk.X)
tk.Spinbox(threshold_frame, increment=0.1, from_=0.0, to=100.0,
           textvariable=wrapper.threshold,
           validate='key',
           validatecommand=(frame.register(validate_numeric), '%P')).pack(
    side=tk.RIGHT, expand=True, fill=tk.X)

# Test set
test_frame = tk.Frame(main_tab)
test_frame.pack(expand=True, fill=tk.X)
tk.Label(test_frame, text="Test file (optional):").pack(side=tk.LEFT,
                                                        expand=True, fill=tk.X)
test_button = tk.Button(test_frame, text="Select file", command=get_testset)
test_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)
del_test_button = tk.Button(test_frame, text="Clear file", command=clear_test)

# Output
out_frame = tk.Frame(main_tab)
out_frame.pack(expand=True, fill=tk.X)
dir_frame = tk.Frame(out_frame)
dir_frame.pack(expand=True, fill=tk.X)
tk.Label(dir_frame, text="Output directory:").pack(side=tk.LEFT, expand=True,
                                                   fill=tk.X)
out_button = tk.Button(dir_frame, text="Select directory", command=get_out_dir)
out_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)
prefix_frame = tk.Frame(out_frame)
prefix_frame.pack(expand=True, fill=tk.X)
tk.Label(prefix_frame, text="Prefix for output:").pack(side=tk.LEFT,
                                                       expand=True, fill=tk.X)
out_name = tk.Entry(prefix_frame, textvariable=wrapper.out_name)
out_name.pack(side=tk.RIGHT, expand=True, fill=tk.X)
out_name.bind("<KeyRelease>", update_name)
out_label = tk.Label(out_frame)
out_label.pack(side=tk.RIGHT, expand=True, fill=tk.X)

ttk.Separator(main_tab, orient="horizontal").pack(expand=True, fill=tk.BOTH)

tk.Label(main_tab, text="Additional Options", pady=10).pack(expand=True,
                                                            fill=tk.X)

# count strategy
count_frame = tk.Frame(main_tab)
count_frame.pack(expand=True, fill=tk.X)
tk.Label(count_frame, text="Count strategy:").pack(side=tk.LEFT, expand=True,
                                                   fill=tk.X)
tk.Radiobutton(count_frame, text="quadratic count", value=0,
               variable=wrapper.linear).pack(side=tk.LEFT, expand=True,
                                             fill=tk.X)
tk.Radiobutton(count_frame, text="linear count", value=1,
               variable=wrapper.linear).pack(side=tk.LEFT, expand=True,
                                             fill=tk.X)

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
mdc_selection.pack(side=tk.LEFT, expand=True, fill=tk.X)

# rest
rest_frame = tk.Frame(main_tab)
rest_frame.pack(expand=True, fill=tk.X)
a_frame = tk.Frame(rest_frame)
a_frame.pack(expand=True, fill=tk.X)
tk.Checkbutton(a_frame, text="Drop duplicated instances",
               variable=wrapper.drop_duplicates).pack(side=tk.LEFT, expand=True,
                                                      fill=tk.X)
tk.Checkbutton(a_frame, text="Keep test exemplar in training set", onvalue=0,
               offvalue=1).pack(side=tk.LEFT, expand=True, fill=tk.X)
b_frame = tk.Frame(rest_frame)
b_frame.pack(expand=True, fill=tk.X)
tk.Checkbutton(b_frame, text="Ignore attributes with unknown values",
               variable=wrapper.ignore_unknowns).pack(side=tk.LEFT, expand=True,
                                                      fill=tk.X)
tk.Checkbutton(b_frame, text="Debug mode", variable=wrapper.debug).pack(
    side=tk.LEFT, expand=True, fill=tk.X)

# run/cancel
run_frame = tk.Frame(main_tab)
run_frame.pack(expand=True, fill=tk.X)
start_button = tk.Button(run_frame, text="Run algorithm", command=run_button)
start_button.pack(side=tk.TOP, expand=True, fill=tk.X)
cancel_button = tk.Button(run_frame, text="Cancel", command=stop_aml)

root.mainloop()
