"""Utility classes for AML GUI"""

import tkinter as tk
from tkinter import ttk, messagebox


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
