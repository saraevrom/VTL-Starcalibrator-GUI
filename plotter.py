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
import colorsys
matplotlib.use("TkAgg")

PIXEL_SIZE = 2.85
HALF_GAP_SIZE = 2.0
HALF_PIXELS = 8
CMAP = plt.cm.viridis

LOWER_EDGES = np.arange(HALF_PIXELS)*PIXEL_SIZE+HALF_GAP_SIZE
LOWER_EDGES = np.concatenate([-np.flip(LOWER_EDGES)-PIXEL_SIZE, LOWER_EDGES])
print(LOWER_EDGES)


def star_id_to_rgb(i):
    hue = (2/3+np.pi/12*i) % 1
    r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
    r = min(int(r*255), 255)
    g = min(int(g * 255), 255)
    b = min(int(b * 255), 255)

    print(r,g,b)
    return '#%02x%02x%02x' % (r,g,b)

class Plotter(ttk.Frame):
    def __init__(self, master, *args, **kwargs):
        super(Plotter, self).__init__(master, *args, **kwargs)
        self.figure: Figure
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.axes: Axes
        self.axes = self.figure.add_subplot(1, 1, 1)

        self.mpl_canvas = FigureCanvasTkAgg(self.figure, self)
        self.mpl_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.toolbar = NavigationToolbar2Tk(self.mpl_canvas, self)
        self.toolbar.update()

    def draw(self):
        self.figure.canvas.draw()
        self.figure.canvas.flush_events()
        self.mpl_canvas.draw()

class GridPlotter(Plotter):
    def __init__(self, master, norm=None, *args, **kwargs):
        super(GridPlotter, self).__init__(master, *args, **kwargs)

        span = HALF_PIXELS*PIXEL_SIZE+HALF_GAP_SIZE
        self.axes.set_xlim(-span, span)
        self.axes.set_ylim(-span, span)
        self.axes.set_box_aspect(1)

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

    def set_line(self, key, xs, ys, label=""):
        if key in self.lines.keys():
            line = self.lines[key]
            line.set_xdata(xs)
            line.set_ydata(ys)
        else:
            line, = self.axes.plot(xs, ys, "-o", label=label, color= star_id_to_rgb(key))
            self.lines[key] = line


    def remove_line(self, key):
        if key in self.lines.keys():
            self.lines[key].remove()
            del self.lines[key]

    def delete_lines(self):
        for key in self.lines.keys():
            self.lines[key].remove()
        self.lines.clear()
        self.axes.set_prop_cycle(None)

    def draw(self):
        self.axes.legend()
        super(GridPlotter, self).draw()