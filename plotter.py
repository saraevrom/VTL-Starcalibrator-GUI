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
from astronomy import find_index
import colorsys
matplotlib.use("TkAgg")
from parameters import *
from localization import get_locale
import time

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
        #self.figure.canvas.draw()
        #self.figure.canvas.flush_events()
        self.mpl_canvas.draw()


class GridPlotter(Plotter):
    def __init__(self, master, norm=None, *args, **kwargs):
        super(GridPlotter, self).__init__(master, *args, **kwargs)
        self.use_autoscale_var = tk.IntVar(self)
        self.use_autoscale_var.set(1)
        self.min_norm_entry = tk.StringVar(self)
        self.max_norm_entry = tk.StringVar(self)
        self.on_right_click_callback = None
        self.on_right_click_callback_outofbounds = None

        self.colorbar = None
        span = HALF_PIXELS*PIXEL_SIZE+HALF_GAP_SIZE
        self.axes.set_xlim(-span, span)
        self.axes.set_ylim(-span, span)
        self.axes.set_box_aspect(1)

        self.buffer_matrix = np.zeros((16, 16))
        self.alive_pixels_matrix = np.ones([2*HALF_PIXELS, 2*HALF_PIXELS]).astype(bool)
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
        self.figure.canvas.mpl_connect("button_press_event", self.on_plot_click)

        norm_panel = tk.Frame(self)
        norm_panel.pack(side=tk.BOTTOM, fill=tk.X)
        for i in range(4):
            norm_panel.columnconfigure(i, weight=1)
        autoscale_check = tk.Checkbutton(norm_panel, text=get_locale("app.widgets.gridplotter.use_autoscale"),
                                         variable=self.use_autoscale_var)
        autoscale_check.grid(row=0, column=0, columnspan=4, sticky="ew")
        tk.Label(norm_panel, text=get_locale("app.widgets.gridplotter.scale")).grid(row=1, column=0, sticky="ew")
        tk.Label(norm_panel, text=get_locale("???")).grid(row=1, column=2, sticky="ew")
        tk.Entry(norm_panel, textvariable=self.min_norm_entry).grid(row=1, column=1, sticky="ew")
        tk.Entry(norm_panel, textvariable=self.max_norm_entry).grid(row=1, column=3, sticky="ew")

    def update_norm(self, low_fallback=None, high_fallback=None):
        if low_fallback is None:
            if self.norm is None:
                return
            low_fallback = self.norm.vmin

        if high_fallback is None:
            if self.norm is None:
                return
            high_fallback = self.norm.vmax
        if low_fallback > high_fallback:
            high_fallback = low_fallback + 1e-6

        if self.use_autoscale_var.get():
            low = low_fallback
            high = high_fallback
            self.max_norm_entry.set(str(high_fallback))
            self.min_norm_entry.set(str(low_fallback))
        else:
            try:
                low = float(self.min_norm_entry.get())
            except ValueError:
                self.min_norm_entry.set(str(low_fallback))
                low = low_fallback
            try:
                high = float(self.max_norm_entry.get())
            except ValueError:
                self.max_norm_entry.set(str(high_fallback))
                high = high_fallback

        if low > high:
            low, high = high, low

        if self.norm is None:
            self.norm = Normalize(low, high)
        else:
            # M agic: pyplot requires to assign twice
            self.norm.vmin = low
            self.norm.vmin = low
            self.norm.vmax = high
            self.norm.vmax = high

    def update_matrix_plot(self, update_norm=False):
        # start_time = time.time()
        # print("Draw START")
        if update_norm or (self.norm is None):
            alive_data = self.buffer_matrix[self.alive_pixels_matrix]
            low_auto = np.min(alive_data)
            high_auto = np.max(alive_data)
            self.update_norm(low_auto, high_auto)

            if self.colorbar is None:
                self.colorbar = self.figure.colorbar(plt.cm.ScalarMappable(norm=self.norm, cmap=PLOT_COLORMAP))
        # print("Normalized:", time.time()-start_time)
        for j in range(2*HALF_PIXELS):
            for i in range(2*HALF_PIXELS):
                if self.alive_pixels_matrix[i,j]:
                    self.patches[j][i].set_color(PLOT_COLORMAP(self.norm(self.buffer_matrix[i, j])))
                else:
                    self.patches[j][i].set_color(PLOT_BROKEN_COLOR)
        # print("Draw end:", time.time()-start_time)

    def set_broken(self, broken):
        self.alive_pixels_matrix = np.ones([2*HALF_PIXELS, 2*HALF_PIXELS]).astype(bool)
        for i, j in broken:
            self.alive_pixels_matrix[i, j] = False

    def toggle_broken(self, i, j):
        self.alive_pixels_matrix[i, j] = not self.alive_pixels_matrix[i, j]

    def on_plot_click(self, event):
        if (event.xdata is not None) and (event.ydata is not None):
            i = find_index(event.xdata)
            j = find_index(event.ydata)
            if i >= 0 and j >= 0:
                if event.button == 1:  #LMB
                    self.toggle_broken(i, j)
                    self.update_matrix_plot(True)
                    self.draw()
                elif event.button == 3:  #RMB
                    if self.on_right_click_callback:
                        self.on_right_click_callback(i, j)
            elif event.button == 3:
                if self.on_right_click_callback_outofbounds:
                    self.on_right_click_callback_outofbounds()

        # self.on_right_click_callback

class StarGridPlotter(GridPlotter):
    def __init__(self, master, norm=None, *args, **kwargs):
        super(StarGridPlotter, self).__init__(master, norm, *args, **kwargs)
        self.lines = dict()

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
        super(StarGridPlotter, self).draw()