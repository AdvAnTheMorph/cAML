"""Utils for visualizing AML output using tkinter and pandastable"""

import tkinter as tk
from tkinter import filedialog

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pandastable import Table


class CSVSavingTable(Table):
    def __init__(self, parent=None, **kwargs):
        Table.__init__(self, parent, **kwargs)

    def saveAs(self, filename=None):
        """Save dataframe to file"""

        if filename is None:
            filename = filedialog.asksaveasfilename(parent=self.master,
                                                    initialdir = self.currentdir,
                                                    filetypes=[("csv","*.csv"),
                                                               ("All files","*.*")])
        if filename:
            super().saveAs(filename)

class TableVisualization:
    """Visualize tables in tkinter"""
    def __init__(self, root, df):
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        self.table = CSVSavingTable(self.frame, dataframe=df, showtoolbar=True,
                                    showstatusbar=True)
        self.table.show()


class MatrixVisualization:
    """Visualize confusion matrix in tkinter"""
    def __init__(self, root, matrix, save=None):
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

        fig, ax = plt.subplots()
        matrix.plot(ax=ax)
        canvas = FigureCanvasTkAgg(fig, master=self.frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side='left', fill='both', expand=True)

        if save:
            fig.savefig(save.with_name(save.stem + "_matrix.png"))
