import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from plotter import Plotter
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.pyplot import Normalize
import colorsys
from matplotlib.collections import LineCollection


class SignalPlotter(Plotter):
    def __init__(self, master, *args, **kwargs):
        super(SignalPlotter, self).__init__(master, *args, **kwargs)
        self.axes.grid()
        self.left_line, = self.axes.plot([0, 0], [0, 1000], "-", color="black")
        self.right_line, = self.axes.plot([0, 0], [0, 1000], "-", color="black")
        self.left_cut = 0
        self.right_cut = 0

    def view_x(self, left, right):
        self.axes.set_xlim(left, right)

    def set_xrange(self, left, right):
        if left > right:
            left, right = right, left
        print(left, right)
        self.left_line.set_xdata([left, left])
        self.right_line.set_xdata([right, right])
        self.left_cut = left
        self.right_cut = right


    # def plot_data(self, file, skip):
    #     data0 = file["data0"]
    #     res_array = None
    #     for i in range(0, len(file), skip):
    #         layer = np.mean(data0[i:i+skip], axis=0)
    #         if res_array is not None:
    #             res_array = np.vstack([res_array, layer])
    #         else:
    #             res_array = layer
