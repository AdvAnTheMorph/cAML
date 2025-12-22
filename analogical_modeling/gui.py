"""Graphical user interface for analogical modeling."""

import sys
# import multiprocessing as mp

import pandas as pd
import tkinter as tk
from tkinter import messagebox
from pathlib import Path
from tkinter import ttk, filedialog

from analogical_modeling.gui_utils import AMWrapper

root = tk.Tk()
stdout = sys.stdout  # original stdout # TODO: do I need that?

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
#root.configure()
root.minsize(600, 500)
# root.maxsize(1400, 1200)
root.geometry("300x300+50+50")

notebook = ttk.Notebook(root)
notebook.pack(fill='both', expand=True)

main_tab = ttk.Frame(notebook)
notebook.add(main_tab, text="Configuration")

tk.Label(main_tab, text="Configuration").grid(columnspan=2)


processes = []
# Toplevel for separate window container

wrapper = AMWrapper()

def run():
    try:
        wrapper.ignored = [ignored.get(i) for i in ignored.curselection()]
        wrapper.run()
    except Exception as e:
        # logger.exception(e)
        raise e
    # TODO:
    # - could return conf_matrix + output dirs
    # - then open all in files

    if not hasattr(root, "conf_mat_tab"):
        root.conf_mat_tab = ttk.Frame(notebook)
        notebook.add(root.conf_mat_tab, text="Results")
        result_label = tk.Label(root.conf_mat_tab, text="test")
        result_label.grid()
    else:
        # Update existing tab
        for widget in root.conf_mat_tab.winfo_children():
            widget.destroy()
        tk.Label(root.conf_mat_tab, text="test").grid()
    # tab = ttk.Notebook(root)
    # tab_2 = ttk.Frame(tab)
    # tab.add(tab_2, text="Confusion Matrix")
    # tab.grid()


def run_button():
    # tk.messagebox.showerror("title", "desc") / showinfo
    # TODO: more validation
    # validation
    # if not wrapper.lexicon:
    #     sys.exit("Please specify a lexicon.")
    # if not Path(wrapper.lexicon).exists():
    #     sys.exit(f"File {wrapper.lexicon} not found.")
    # if wrapper.testset and not Path(wrapper.testset).exists():
    #     sys.exit(f"Test file given, but {wrapper.testset} not found.")

    # if args.debug:
    #     logger.setLevel(logging.DEBUG)


    # FIXME:
    # run in separate process
    run()
    # process = mp.Process(target=run, args=(am,), daemon=True)
    # process.start()
    # processes.append(process)
    # start_button.grid_remove()
    # cancel_button.grid()


def stop_aml():
    for process in processes:
        process.terminate()
    cancel_button.grid_remove()
    start_button.grid()


# TODO: Must be removable
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
    # TODO: validation -> Error message
    cols = list(pd.read_csv(wrapper.lexicon).columns)
    ignored.delete(0, tk.END)  # remove old elements
    for col in cols:
        ignored.insert(tk.END, col)
        weights_box["values"] = [""]+cols
    ignored_label.grid(column=0, row=0)
    ignored.grid(column=1, row=0)
    weights_label.grid(column=0, row=1)
    weights_box.grid(column=1, row=1)

def val_and_vis(arg=None):
    if not weights_box.get():  # = no weights
        th_label.grid_remove()
        th_box.grid_remove()
        return

    # validate and set
    temp = pd.read_csv(wrapper.lexicon)
    value = weights_box.get()
    if pd.api.types.is_numeric_dtype(temp[value]):
        wrapper.weights = value
        th_label.grid(column=0, row=2)
        th_box.grid(column=1, row=2)
    else:
        th_label.grid_remove()
        th_box.grid_remove()
        messagebox.showerror(f"Invalid weights column '{value}'",
                             "The selected column does not contain numeric values.")
        weights_box.current(0)


def get_testset():
    wrapper.testset = get_file(test_button) or ""


def update_name(arg=None):
    if wrapper.out_name.get():
        wrapper.out = Path(wrapper.out_dir or ".") / wrapper.out_name.get()
        out_label.config(text=f"Results will be saved to {Path(wrapper.out_dir).name or '.'}/{out_name.get()}_*")
    else:
        out_label.config(text="")


def get_out_dir():
    wrapper.out_dir = filedialog.askdirectory(initialdir="./..",)
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

tk.Label(main_tab, text="Lexicon file:").grid(column=0, row=1)
lexicon_button = tk.Button(main_tab, text="Select file", command=get_lexicon)
lexicon_button.grid(column=1, row=1)

tk.Label(main_tab, text="Test file (optional):").grid(column=0, row=2)
test_button = tk.Button(main_tab, text="Select file", command=get_testset)
test_button.grid(column=1, row=2)

tk.Label(main_tab, text="Output directory:").grid(column=0, row=3)
out_button = tk.Button(main_tab, text="Select directory", command=get_out_dir)
out_button.grid(column=1, row=3)
tk.Label(main_tab, text="Prefix for output:").grid(column=0, row=4)
out_name = tk.Entry(main_tab, textvariable=wrapper.out_name)
out_name.grid(column=1, row=4)
out_name.bind("<KeyRelease>", update_name)
out_label = tk.Label(main_tab)
out_label.grid(column=0, row=5, columnspan=2)

# configurations once lexicon has been selected
frame = tk.Frame(main_tab)
frame.grid(column=0, row=6, columnspan=2)
ignored_label = tk.Label(frame, text="Select columns to ignore:")
ignored = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=4)
# scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL)
# scrollbar.config(command=ignored.yview)
# scrollbar.grid()
weights_label = tk.Label(frame, text="Select weights column (if any):")
weights_box = ttk.Combobox(frame, values=[""], state="readonly")
weights_box.bind("<<ComboboxSelected>>", val_and_vis)
weights_box.current(0)
weights_box.bind()
th_label = tk.Label(frame, text="Ignore instances with weights below:")
th_box = tk.Spinbox(frame, increment=0.1, from_=0.0, to=100.0, textvariable=wrapper.threshold,
    validate='key', validatecommand=(frame.register(validate_numeric), '%P'))

tk.Label(main_tab, text="Additional Options", pady=10).grid(column=0, row=7, columnspan=2)
tk.Label(main_tab, text="Count strategy:").grid(column=0, row=8)
tk.Radiobutton(main_tab, text="quadratic count", value=0, variable=wrapper.linear).grid(column=0, row=9)
tk.Radiobutton(main_tab, text="linear count", value=1, variable=wrapper.linear).grid(column=1, row=9)

tk.Label(main_tab, text="Consider missing values as:").grid(column=0, row=10)
mdc_selection = ttk.Combobox(main_tab, values=["match", "mismatch", "variable"], textvariable=wrapper.mdc, state="readonly")
mdc_selection.current(2)
mdc_selection.grid(column=1, row=10)

tk.Checkbutton(main_tab, text="Drop duplicated instances", variable=wrapper.drop_duplicates).grid(column=0, row=11)
tk.Checkbutton(main_tab, text="Keep test exemplar in training set", onvalue=0, offvalue=1).grid(column=1, row=11)
tk.Checkbutton(main_tab, text="Ignore attributes with unknown values", variable=wrapper.ignore_unknowns).grid(column=0, row=12)

tk.Checkbutton(main_tab, text="Debug mode", variable=wrapper.debug).grid(column=1, row=12)

start_button = tk.Button(main_tab, text="Run algorithm", command=run_button)
start_button.grid(row=13, columnspan=2)
cancel_button = tk.Button(main_tab, text="Cancel", command=stop_aml)
cancel_button.grid(row=13, columnspan=2)
cancel_button.grid_remove()


root.mainloop()


# # adding menu bar in root window
# # new item in menu bar labelled as 'New'
# # adding more items in the menu bar
# menu = Menu(root)
# item = Menu(menu)
# item.add_command(label='New')
# menu.add_cascade(label='File', menu=item)
# root.config(menu=menu)
