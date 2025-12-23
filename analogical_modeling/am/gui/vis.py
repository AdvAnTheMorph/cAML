"""Utils for visualizing AML output using tkinter and pandastable"""

import tkinter as tk
from pandastable import Table
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class TableVisualization:
    def __init__(self, root, df):
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        self.table = Table(self.frame, dataframe=df, showtoolbar=True,
                          showstatusbar=True)
        self.table.show()


class MatrixVisualization:
    def __init__(self, root, matrix):
        self.frame = tk.Frame(root)
        self.frame.pack(padx=10, pady=10)

        fig, ax = plt.subplots()
        matrix.plot(ax=ax)
        canvas = FigureCanvasTkAgg(fig, master=self.frame)
        canvas.draw()
        canvas.get_tk_widget().pack(side='left', fill='both', expand=True)
