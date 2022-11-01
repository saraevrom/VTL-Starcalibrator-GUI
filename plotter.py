import tkinter as tk
from tkinter import ttk
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from matplotlib.axes import Axes
import numpy as np
from matplotlib.patches import Rectangle
from matplotlib.pyplot import Normalize
matplotlib.use("TkAgg")

PIXEL_SIZE = 2.85
HALF_GAP_SIZE = 3.0
HALF_PIXELS = 8
CMAP = plt.cm.viridis

LOWER_EDGES = np.arange(HALF_PIXELS)*PIXEL_SIZE+HALF_GAP_SIZE
LOWER_EDGES = np.concatenate([-np.flip(LOWER_EDGES)-PIXEL_SIZE, LOWER_EDGES])
print(LOWER_EDGES)

class Plotter(ttk.Frame):
    def __init__(self, master, norm=None, *args, **kwargs):
        super(Plotter, self).__init__(master, *args, **kwargs)
        self.figure: Figure
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.axes: Axes
        self.axes = self.figure.add_subplot(1, 1, 1)
        span = HALF_PIXELS*PIXEL_SIZE+HALF_GAP_SIZE
        self.axes.set_xlim(-span, span)
        self.axes.set_ylim(-span, span)
        self.axes.set_box_aspect(1)

        self.mpl_canvas = FigureCanvasTkAgg(self.figure, self)
        self.mpl_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.mpl_canvas, self)
        self.toolbar.update()

        self.buffer_matrix = np.zeros((16, 16))
        self.patches = []
        for y in LOWER_EDGES:
            row = []
            for x in LOWER_EDGES:
                rect = Rectangle((x, y), PIXEL_SIZE, PIXEL_SIZE, color="blue")
                self.axes.add_patch(rect)
                row.append(rect)
            self.patches.append(row)
        self.norm = norm
        self.update_matrix_plot(True)
        self.axes.vlines(LOWER_EDGES, -span, -HALF_GAP_SIZE, colors="black")
        self.axes.vlines(LOWER_EDGES, span, HALF_GAP_SIZE, colors="black")
        self.axes.vlines([-HALF_GAP_SIZE, span], -span, -HALF_GAP_SIZE, colors="black")
        self.axes.vlines([-HALF_GAP_SIZE, span], span, HALF_GAP_SIZE, colors="black")
        self.axes.hlines(LOWER_EDGES, -span, -HALF_GAP_SIZE, colors="black")
        self.axes.hlines(LOWER_EDGES, span, HALF_GAP_SIZE, colors="black")
        self.axes.hlines([-HALF_GAP_SIZE, span], -span, -HALF_GAP_SIZE, colors="black")
        self.axes.hlines([-HALF_GAP_SIZE, span], span, HALF_GAP_SIZE, colors="black")
        self.lines = dict()

    def update_matrix_plot(self, update_norm=False):
        if update_norm or (self.norm is None):
            low = np.min(self.buffer_matrix)
            high = np.max(self.buffer_matrix)
            if low >= high:
                high += 1e-6
            self.norm = Normalize(low, high)
        for j in range(16):
            for i in range(16):
                self.patches[j][i].set_color(CMAP(self.norm(self.buffer_matrix[i,j])))

    def clear_lines(self):
        self.lines.clear()

    def set_line(self,key,xs,ys,label=""):
        if key in self.lines.keys():
            line = self.lines[key]
            line.set_xdata(xs)
            line.set_ydata(ys)
        else:
            line, = self.axes.plot(xs, ys, "-o", label=label)
            self.lines[key] = line


    def draw(self):
        self.axes.legend()
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        self.mpl_canvas.draw()