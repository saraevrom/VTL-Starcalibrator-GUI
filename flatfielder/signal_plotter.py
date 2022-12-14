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
        self.plots = []

    def view_x(self, left, right):
        self.axes.set_xlim(left, right)

    def view_y(self, bottom, top):
        self.axes.set_ylim(bottom, top)

    def set_xrange(self, left, right):
        if left > right:
            left, right = right, left
        # print(left, right)
        self.left_line.set_xdata([left, left])
        self.right_line.set_xdata([right, right])
        self.left_cut = left
        self.right_cut = right

    def set_yrange(self, bottom, top):
        if bottom > top:
            bottom, top = top, bottom
        # print(bottom, top)
        self.left_line.set_ydata([bottom, top])
        self.right_line.set_ydata([bottom, top])

    def plot_data(self, drawing_data):
        xs = np.arange(0,len(drawing_data),1)
        for l in self.plots:
            l.remove()
        self.axes.set_prop_cycle(None)
        self.plots.clear()
        for i in range(16):
            for j in range(16):
                ys = drawing_data[:, i, j]
                line, = self.axes.plot(xs, ys)
                self.plots.append(line)
        print(drawing_data.shape)