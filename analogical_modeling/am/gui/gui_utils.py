"""Utility classes for AML GUI"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from typing import Iterable, Optional

import pandas as pd
from TkToolTip import ToolTip as Tip

LEN = 40
pack_config = {"side": tk.LEFT, "expand": True}  # , "fill": tk.X}


class ToolTip(Tip):
    """Helper class to get same configurations for all tooltips"""
    def __init__(self, widget, text):
        super().__init__(widget, text=text, delay=0.5, relief='raised',
                         show_duration=5)


class OutputSelection:
    def __init__(self, parent: tk.Frame):
        df_frame = tk.Frame(parent)
        df_frame.pack(expand=True)

        self.analog = tk.BooleanVar()
        self.gangs = tk.BooleanVar()
        self.distr = tk.BooleanVar()

        tk.Label(df_frame, text="Create:").pack(side=tk.LEFT)
        gangs = tk.Checkbutton(df_frame, text="Gang effects",
                               variable=self.gangs)
        gangs.select()
        gangs.pack(side=tk.LEFT)
        analogs = tk.Checkbutton(df_frame, text="Analogical sets",
                                 variable=self.analog)
        analogs.select()
        analogs.pack(side=tk.LEFT)
        distr = tk.Checkbutton(df_frame, text="Distributions",
                               variable=self.distr)
        distr.select()
        distr.pack(side=tk.LEFT)


class VisOnCommandFrame:
    def __init__(self, parent: tk.Frame, config: dict):
        self.frame = tk.Frame(parent)
        self.config = config

    def vis(self):
        self.frame.pack(**self.config)

    def invis(self):
        self.frame.pack_forget()


class ClsFrame(VisOnCommandFrame):
    def __init__(self, parent: tk.Frame, wrapper):
        super().__init__(parent, {"side": tk.TOP, "fill": tk.X, "expand": True})
        tk.Label(self.frame,
                 text=f"{'Class column:':{LEN}s}\t").pack(side=tk.LEFT,
                                                          expand=True,
                                                          fill=tk.X)
        self.box = ttk.Combobox(self.frame,
                                textvariable=wrapper.class_idx,
                                state="readonly", values=[""])
        self.box.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def fill(self, vals):
        """Refill combobox with values and set current to last one"""
        self.box["values"] = vals
        self.box.current(len(vals) - 1)

    def get(self, idx: Optional[int] = None):
        """Get index of selected element or element with given index"""
        if idx:
            return self.box["values"][idx]
        return self.box.current()


class IgnoreFrame(VisOnCommandFrame):


    def __init__(self, parent: tk.Frame):
        super().__init__(parent, {"side": tk.TOP, "fill": tk.X, "expand": True})
        tk.Label(self.frame,
                 text=f"{'Select columns to ignore:':{LEN}s}\t").pack(
            side=tk.LEFT,
            expand=True,
            fill=tk.X)
        self.box = tk.Listbox(self.frame, selectmode=tk.MULTIPLE, height=4)
        self.box.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        scrollbar = tk.Scrollbar(self.frame, orient=tk.VERTICAL)
        scrollbar.pack(expand=False, fill=tk.Y, before=self.box, side=tk.RIGHT)
        # link scrollbar and listbox
        scrollbar.config(command=self.box.yview)
        self.box.config(yscrollcommand=scrollbar.set)

    def clear(self) -> None:
        """Remove all items from listbox"""
        self.box.delete(0, tk.END)

    def fill(self, items: Iterable) -> None:
        """Fill listbox with items"""
        for item in items:
            self.box.insert(tk.END, item)

    def list_selected(self) -> list:
        """List selected items in listbox"""
        return [self.box.get(i) for i in self.box.curselection()]


class WeightsFrame(VisOnCommandFrame):
    def __init__(self, parent: tk.Frame, wrapper):
        super().__init__(parent, {"side": tk.TOP, "fill": tk.X, "expand": True})
        self.wrapper = wrapper

        # weights_frame = tk.Frame(self.frame)
        tk.Label(self.frame,
                 text=f"{'Select weights column (if any):':{LEN}s}\t").pack(
            side=tk.LEFT, expand=True, fill=tk.X)

        self.box = ttk.Combobox(self.frame, values=[""], state="readonly")
        self.box.bind("<<ComboboxSelected>>", self.val_and_vis)
        self.box.current(0)
        self.box.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        self.threshold_frame = ThresholdFrame(parent, self.wrapper)

    def val_and_vis(self, _arg=None):
        """Validate weights column and visualize threshold selection"""
        value = self.box.get()
        if not value:  # = no weights
            self.threshold_frame.invis()
            self.wrapper.weights = value
            return

        # validate and set
        temp = pd.read_csv(self.wrapper.lexicon)
        if pd.api.types.is_numeric_dtype(temp[value]):
            self.wrapper.weights = value
            self.threshold_frame.vis()
        else:
            self.threshold_frame.invis()
            messagebox.showerror(f"Invalid weights column '{value}'",
                                 "The selected column does not contain "
                                 "numeric values")
            self.box.current(0)

    def fill(self, vals: list) -> None:
        """Fill Combobox with new values"""
        self.box["values"] = [""] + vals
        self.box.current(0)  # TODO: remove threshold if new file selected


class ThresholdFrame(VisOnCommandFrame):
    def __init__(self, parent: tk.Frame, wrapper):
        super().__init__(parent,
                         {"side": tk.BOTTOM, "fill": tk.X, "expand": True})

        tk.Label(self.frame,
                 text=f"{'Ignore instances with weights below:':{LEN}s}\t").pack(
            side=tk.LEFT, expand=True, fill=tk.X)
        tk.Spinbox(self.frame, increment=0.01, from_=0.0, to=1.0,
                   textvariable=wrapper.threshold,
                   validate='key',
                   validatecommand=(
                       self.frame.register(self.validate_numeric), '%P')).pack(
            side=tk.RIGHT, expand=True, fill=tk.X)

    @staticmethod
    def validate_numeric(val) -> bool:
        """Validate threshold as numeric, non-negative value"""
        if val == "":  # Allow empty string (deletion)
            return True
        try:
            return float(val) >= 0.0
        except ValueError:
            return False


class OutFrame:
    def __init__(self, parent: tk.Frame, wrapper):
        self.frame = tk.Frame(parent)
        self.frame.pack(expand=True, fill=tk.X)
        # tk.Label(self.frame, text="Output specification", font=("", 11),
        #          pady=8).pack(side=tk.TOP, expand=True, fill=tk.X)
        self.wrapper = wrapper

        dir_frame = tk.Frame(self.frame)
        dir_frame.pack(expand=True, fill=tk.X)
        tk.Label(dir_frame,
                 text=f"{'Output directory:':{LEN}s}\t").pack(side=tk.LEFT,
                                                              expand=True,
                                                              fill=tk.X)
        self.button = tk.Button(dir_frame, text="Select directory",
                                command=self.get_out_dir)
        self.button.pack(side=tk.RIGHT, expand=True, fill=tk.X)

        prefix_frame = tk.Frame(self.frame)
        prefix_frame.pack(expand=True, fill=tk.X)
        tk.Label(prefix_frame,
                 text=f"{'Prefix for output:':{LEN}s}\t").pack(side=tk.LEFT,
                                                               expand=True,
                                                               fill=tk.X)
        self.name = tk.Entry(prefix_frame, textvariable=wrapper.out_name)
        # TODO: maybe default value
        # out_name.insert(0, "am_output")
        self.name.pack(side=tk.RIGHT, expand=True, fill=tk.X)
        self.name.bind("<KeyRelease>", self.update_label_text)

        self.label = tk.Label(self.frame,
                              text="Results won't be saved automatically.",
                              fg="red")
        self.label.pack(side=tk.RIGHT, expand=True, fill=tk.X)

    def update_label_text(self, _arg=None):
        """Update text of label according to specified directory and name"""
        name = self.wrapper.out_name.get()
        if name:
            self.wrapper.out = Path(self.wrapper.out_dir).resolve() / name
            self.label.config(
                text=f"Results will be saved to "
                     f"{Path(self.wrapper.out_dir).name}/{name}_*",
                fg="black")
        else:
            self.label.config(text="Results won't be saved automatically.",
                              fg="red")

    def get_out_dir(self):
        """Let user select directory"""
        tmp = filedialog.askdirectory(initialdir="./..")
        if not tmp:
            return

        self.wrapper.out_dir = tmp
        self.update_label_text()
        self.button.configure(text=f"Selected: */{Path(tmp).name}/")


class CountFrame:
    """Frame to determine count strategy"""
    def __init__(self, parent, wrapper):
        self.frame = tk.Frame(parent)
        self.frame.pack(expand=True)

        tk.Label(self.frame,
                 text="Count strategy:",
                 padx=15).pack(side=tk.LEFT, expand=True, fill=tk.X)
        q = tk.Radiobutton(self.frame,
                           text="quadratic count",
                           variable=wrapper.linear,
                           value=0)
        q.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ToolTip(q,
                "Count pointers within homogeneous supracontexts quadratically")
        l = tk.Radiobutton(self.frame,
                           text="linear count",
                           variable=wrapper.linear,
                           value=1)
        l.pack(side=tk.LEFT, expand=True, fill=tk.X)
        ToolTip(l, "Count pointers within homogeneous supracontexts linearly")


class CheckboxFrames:
    """Frames for additional options"""
    def __init__(self, parent, wrapper):
        self.parent = parent

        first = tk.Frame(self.parent)
        first.pack(expand=True, fill=tk.BOTH)
        a = tk.Checkbutton(first,
                           text=f"{"Drop duplicated instances":{LEN}s}\t",
                           variable=wrapper.drop_duplicates,
                           anchor="e")
        a.grid()
        ToolTip(a, "Drop duplicated instances from lexicon")
        # pack(anchor="e", padx=30, **pack_config)
        b = tk.Checkbutton(first,
                           text=f"{'Keep test exemplar in lexicon':{LEN}s}",
                           onvalue=0,
                           offvalue=1,
                           anchor="w",
                           variable=wrapper.keep_test)
        b.grid(row=0, column=1)
        b.deselect()
        ToolTip(b,
                "Keep equal instances in the lexicon before attempting to "
                "classify an instance\n(only sensible if using a test set, "
                "as it will result in a direct lookup otherwise)")
        # pack(anchor="w", padx=40, **pack_config)

        second = tk.Frame(parent)
        second.pack(expand=True, fill=tk.BOTH)
        c = tk.Checkbutton(second,
                           text=f"{'Ignore attributes with unknown values':{LEN}s}\t",
                           variable=wrapper.ignore_unknowns,
                           anchor="e")
        c.grid()
        ToolTip(c, "Ignore unknown attributes (=) during classification")
        # pack(padx=5, **pack_config)
        d = tk.Checkbutton(second,
                           text=f"{'Debug mode':{LEN}s}",
                           variable=wrapper.debug,
                           anchor="w")
        d.grid(row=0, column=1)
        ToolTip(d, "Log debug messages")
        # pack(**pack_config)


class StartFrame:
    def __init__(self, app, parent, wrapper):
        self.app = app
        self.parent = parent
        self.wrapper = wrapper

        frame = tk.Frame(parent)
        frame.pack(expand=True, fill=tk.X)
        self.start_button = tk.Button(frame, text="Run algorithm",
                                      command=self.run)
        self.start_button.pack(side=tk.TOP, expand=True, fill=tk.X)
        self.cancel_button = tk.Button(frame, text="Cancel", command=self.stop)

        self.pbar = ttk.Progressbar(frame, orient=tk.HORIZONTAL,
                                    mode="determinate")
        self.bar_label = tk.Label(frame,
                                  text="Creating output files...")  # TODO:
        # no background

    def run(self):
        # runs in separate thread
        if self.app.run():
            self.disable_all_but_cancel(self.parent)
            self.pbar.pack(expand=True, fill=tk.X)
            self.cancel_button.pack(expand=True, fill=tk.X)
            self.start_button.pack_forget()
            self.app.root.after(100, self.check_completion)

    def on_end(self):
        """Reset everything to pre-run state"""
        # reset bar
        self.pbar["value"] = 0
        self.bar_label.pack_forget()
        self.pbar.pack_forget()
        # replace cancel with start
        self.cancel_button.pack_forget()
        self.start_button.pack(expand=True, fill=tk.X)
        # enable all widgets
        self.enable_all(self.parent)

    def stop(self, reason=None):
        # stop thread
        self.wrapper.cancel()
        if reason:
            messagebox.showwarning("Process cancelled", reason)
        else:
            messagebox.showinfo("Stop AML", "Stopping AML")

        self.on_end()

    def disable_all_but_cancel(self, frame):
        """Disable all but the cancel/start buttons"""
        for child in frame.winfo_children():
            if child in [self.cancel_button, self.start_button]:
                continue
            if isinstance(child, tk.Frame):
                self.disable_all_but_cancel(child)
            child.bind("<Button>", "break")
            child.bind("<Key>", "break")

    def enable_all(self, frame):
        """Re-enable all buttons"""
        for child in frame.winfo_children():
            if isinstance(child, tk.Frame):
                self.enable_all(child)
            child.unbind("<Button>")
            child.unbind("<Key>")

    def update_probressbar(self):
        """Update progressbar"""
        while not self.wrapper.queue.empty():
            val, max_ = self.wrapper.queue.get()
            self.pbar["maximum"] = max_
            self.pbar["value"] = max(val, self.pbar["value"])
            if val == max_:
                self.bar_label.pack(in_=self.pbar)

    def check_completion(self):
        """Check whether wrapped progress complete"""
        if self.wrapper.res:
            self.app.on_completion()
            self.on_end()
        elif self.wrapper.am.cancel_event:
            return
        elif self.wrapper.exit_reason:
            self.stop(self.wrapper.exit_reason)
        else:
            self.update_probressbar()
            self.app.root.after(100, self.check_completion)
