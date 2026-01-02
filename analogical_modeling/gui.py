"""Graphical user interface for analogical modeling."""

import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from tkinter import ttk, filedialog

import pandas as pd

from analogical_modeling.am.gui.aml_wrapper import AMWrapper
from analogical_modeling.am.gui.gui_utils import CheckboxFrames, CountFrame
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
root.minsize(600, 600)
root.geometry("300x300+50+50")

notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

main_tab = ttk.Frame(notebook, padding=10)
notebook.add(main_tab, text="Configuration")

tk.Label(main_tab, text="Configuration", font=("", 15)).pack(expand=True, fill=tk.BOTH)

wrapper = AMWrapper()

create_analog = tk.BooleanVar()
create_gangs = tk.BooleanVar()
create_distr = tk.BooleanVar()


def run_button():
    # runs in separate thread
    try:
        wrapper.class_idx = cls_column.current()
        wrapper.ignored = [ignored.get(i) for i in ignored.curselection()]
        errors = wrapper.run_in_thread()
        if not errors:
            bar.pack(expand=True, fill=tk.X)
            cancel_button.pack(expand=True, fill=tk.X)
            start_button.pack_forget()
            out_name.configure(state="readonly")  # don't change name
            root.after(100, check_completion)
        else:
            messagebox.showerror("Missing parameters", errors)
    except Exception as e:
        raise e


def stop_aml():
    # stop thread
    bar["value"] = 0
    bar_label.pack_forget()
    wrapper.cancel()
    messagebox.showinfo("Stop AML", "Stopping AML")
    bar.pack_forget()
    cancel_button.pack_forget()
    start_button.pack(expand=True, fill=tk.X)
    out_name.configure(state=tk.NORMAL)  # name changeable


def check_completion():
    if wrapper.res:
        on_completion()
    elif wrapper.am.cancel_event:
        return
    else:
        while not wrapper.queue.empty():
            val, max_ = wrapper.queue.get()
            # print(max_, val)
            bar["maximum"] = max_
            bar["value"] = max(val, bar["value"])
            if val == max_:
                bar_label.pack(in_=bar)
        root.after(100, check_completion)


def make_table(parent, file_):
    res_frame = tk.Frame(parent)
    res_frame.pack(expand=True, fill=tk.BOTH)
    TableVisualization(res_frame, file_)


def vis_files(files):
    if not create_gangs.get():
        pass
    elif not hasattr(root, "gangs"):
        root.gangs = ttk.Frame(notebook)
        notebook.add(root.gangs, text="Gang Effects")
        make_table(root.gangs, files[0])
    else:
        # Update existing tab
        for widget in root.gangs.winfo_children():
            widget.destroy()
        make_table(root.gangs, files[0])

    if not create_analog.get():
        pass
    elif not hasattr(root, "analog"):
        root.analog = ttk.Frame(notebook)
        notebook.add(root.analog, text="Analogical Sets")
        make_table(root.analog, files[1])
    else:
        # Update existing tab
        for widget in root.analog.winfo_children():
            widget.destroy()
        make_table(root.analog, files[1])

    if not create_distr.get():
        pass
    elif not hasattr(root, "distr"):
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
        MatrixVisualization(root.conf_mat_tab, matrix, wrapper.out)
    else:
        # Update existing tab
        for widget in root.conf_mat_tab.winfo_children():
            widget.destroy()
        result_label = tk.Label(root.conf_mat_tab,
                                text=f"Accuracy: {acc * 100}%")
        result_label.pack()
        MatrixVisualization(root.conf_mat_tab, matrix)


def on_completion():
    bar["value"] = 0
    bar.pack_forget()
    bar_label.pack_forget()
    cancel_button.pack_forget()
    start_button.pack(expand=True, fill=tk.X)
    out_name.configure(state=tk.NORMAL)  # name changeable

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
    cls_column["values"] = cols
    cls_column.current(len(cols) - 1)
    weights_box["values"] = [""] + cols
    cls_frame.pack(side=tk.TOP, fill=tk.X, expand=True)
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
        wrapper.out = Path(wrapper.out_dir).resolve() / wrapper.out_name.get()
        out_label.config(
            text=f"Results will be saved to "
                 f"{Path(wrapper.out_dir).name}/{out_name.get()}_*")
    else:
        out_label.config(text="Results won't be saved automatically.")


def get_out_dir():
    tmp = filedialog.askdirectory(initialdir="./..")
    if not tmp:
        return

    wrapper.out_dir = tmp
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
lex_spec_frame.pack(fill=tk.BOTH, expand=True)
lex_frame = tk.Frame(lex_spec_frame)
lex_frame.pack(expand=True, fill=tk.X)
tk.Label(lex_frame, text="Lexicon file:").pack(side=tk.LEFT, expand=True,
                                               fill=tk.X)
lexicon_button = tk.Button(lex_frame, text="Select file", command=get_lexicon)
lexicon_button.pack(side=tk.RIGHT, expand=True, fill=tk.X)

# configurations once lexicon has been selected
frame = tk.Frame(lex_spec_frame)
frame.pack(side=tk.BOTTOM, expand=True, fill=tk.X)
cls_frame = tk.Frame(frame)
tk.Label(cls_frame, text="Class column:").pack(side=tk.LEFT, expand=True, fill=tk.X)
cls_column = ttk.Combobox(cls_frame,
                          textvariable=wrapper.class_idx,
                          state="readonly")
cls_column.pack(side=tk.LEFT, expand=True, fill=tk.X)

ignored_frame = tk.Frame(frame)
tk.Label(ignored_frame, text="Select columns to ignore:").pack(side=tk.LEFT,
                                                               expand=True,
                                                               fill=tk.X)
ignored = tk.Listbox(ignored_frame, selectmode=tk.MULTIPLE, height=4)
ignored.pack(side=tk.RIGHT, expand=True, fill=tk.X)
scrollbar = tk.Scrollbar(ignored_frame, orient=tk.VERTICAL)
scrollbar.pack(expand=False, fill=tk.Y, before=ignored, side=tk.RIGHT)
# link scrollbar and listbox
scrollbar.config(command=ignored.yview)
ignored.config(yscrollcommand=scrollbar.set)

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
tk.Spinbox(threshold_frame, increment=0.01, from_=0.0, to=1.0,
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
                                                       expand=True,
                                                       fill=tk.X)
out_name = tk.Entry(prefix_frame, textvariable=wrapper.out_name)
# TODO: maybe default value
# out_name.insert(0, "am_output")
out_name.pack(side=tk.RIGHT, expand=True, fill=tk.X)
out_name.bind("<KeyRelease>", update_name)
out_label = tk.Label(out_frame, text="Results won't be saved automatically.")
out_label.pack(side=tk.RIGHT, expand=True, fill=tk.X)

ttk.Separator(main_tab, orient="horizontal").pack(expand=True, fill=tk.BOTH)

df_frame = tk.Frame(main_tab)
df_frame.pack(expand=True)
tk.Label(df_frame, text="Create:").pack(side=tk.LEFT,)
gangs = tk.Checkbutton(df_frame, text="Gang effects", variable=create_gangs)
gangs.select()
gangs.pack(side=tk.LEFT)
analogs = tk.Checkbutton(df_frame, text="Analogical sets", variable=create_analog)
analogs.select()
analogs.pack(side=tk.LEFT)
distr = tk.Checkbutton(df_frame, text="Distributions", variable=create_distr)
distr.select()
distr.pack(side=tk.LEFT)

ttk.Separator(main_tab, orient="horizontal").pack(expand=True, fill=tk.BOTH)

tk.Label(main_tab, text="Additional Options", pady=10, font=("", 12)).pack(expand=True,
                                                            fill=tk.X)

# count strategy
CountFrame(main_tab, wrapper)

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
CheckboxFrames(rest_frame, wrapper)

# run/cancel
run_frame = tk.Frame(main_tab)
run_frame.pack(expand=True, fill=tk.X)
start_button = tk.Button(run_frame, text="Run algorithm", command=run_button)
start_button.pack(side=tk.TOP, expand=True, fill=tk.X)
cancel_button = tk.Button(run_frame, text="Cancel", command=stop_aml)

bar = ttk.Progressbar(run_frame, orient=tk.HORIZONTAL, mode="determinate")
bar_label = tk.Label(run_frame, text="Creating output files...")  # TODO: no background

# FIXME: pops up at base position first
# center_window(root)
root.mainloop()
