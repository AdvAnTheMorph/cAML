"""Utility classes for AML GUI"""

import tkinter as tk


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

