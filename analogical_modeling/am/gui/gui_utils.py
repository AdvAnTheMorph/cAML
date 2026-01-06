"""Utility classes for AML GUI"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Iterable, Optional

import pandas as pd

pack_config = {"side": tk.LEFT, "expand": True}#, "fill": tk.X}


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
        tk.Label(self.frame, text="Class column:").pack(side=tk.LEFT,
                                                       expand=True,
                                                       fill=tk.X)
        self.box = ttk.Combobox(self.frame,
                                  textvariable=wrapper.class_idx,
                                  state="readonly")
        self.box.pack(side=tk.LEFT, expand=True, fill=tk.X)

    def fill(self, vals):
        """Refill combobox with values and set current to last one"""
        self.box["values"] = vals
        self.box.current(len(vals) - 1)

    def get(self, idx: Optional[int]=None):
        """Get index of selected element or element with given index"""
        if idx:
            return self.box["values"][idx]
        return self.box.current()

class IgnoreFrame(VisOnCommandFrame):
    def __init__(self, parent: tk.Frame):
        super().__init__(parent, {"side": tk.TOP, "fill": tk.X, "expand": True})
        tk.Label(self.frame, text="Select columns to ignore:").pack(
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
        tk.Label(self.frame, text="Select weights column (if any):").pack(
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
                                 "numeric values.")
            self.box.current(0)

    def fill(self, vals: list) -> None:
        """Fill Combobox with new values"""
        self.box["values"] = [""] + vals


class ThresholdFrame(VisOnCommandFrame):
    def __init__(self, parent: tk.Frame, wrapper):
        super().__init__(parent, {"side": tk.BOTTOM, "fill": tk.X, "expand": True})

        tk.Label(self.frame,
                 text="Ignore instances with weights below:").pack(
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


class CountFrame:
    """Frame to determine count strategy"""
    def __init__(self, parent, wrapper):
        self.frame = tk.Frame(parent)
        self.frame.pack(expand=True)

        tk.Label(self.frame,
                 text="Count strategy:",
                 padx=15).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Radiobutton(self.frame,
                       text="quadratic count",
                       variable=wrapper.linear,
                       value=0).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Radiobutton(self.frame,
                       text="linear count",
                       variable=wrapper.linear,
                       value=1).pack(side=tk.LEFT, expand=True, fill=tk.X)


class CheckboxFrames:
    """Frames for additional options"""
    def __init__(self, parent, wrapper):
        self.parent = parent

        first = tk.Frame(self.parent)
        first.pack(expand=True, fill=tk.BOTH)
        tk.Checkbutton(first,
                       text="Drop duplicated instances",
                       variable=wrapper.drop_duplicates,
                       anchor="e").grid(padx=20)
                       # pack(anchor="e", padx=30, **pack_config)
        tk.Checkbutton(first,
                       text="Keep test exemplar in training set",
                       onvalue=0,
                       offvalue=1,
                       anchor="w").grid(row=0, column=1, padx=80)
                       # pack(anchor="w", padx=40, **pack_config)

        second = tk.Frame(parent)
        second.pack(expand=True, fill=tk.BOTH)
        tk.Checkbutton(second,
                       text="Ignore attributes with unknown values",
                       variable=wrapper.ignore_unknowns,
                       anchor="e").grid(padx=20)
                       # pack(padx=5, **pack_config)
        tk.Checkbutton(second,
                       text="Debug mode",
                       variable=wrapper.debug,
                       anchor="w").grid(row=0, column=1)
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
                             text="Creating output files...")  # TODO: no background

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

    def stop(self):
        # stop thread
        self.wrapper.cancel()
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

    def enable_all(self, frame):
        """Re-enable all buttons"""
        for child in frame.winfo_children():
            if isinstance(child, tk.Frame):
                self.enable_all(child)
            child.unbind("<Button>")

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
        else:
            self.update_probressbar()
            self.app.root.after(100, self.check_completion)
