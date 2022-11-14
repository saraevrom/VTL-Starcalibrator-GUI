
import tkinter as tk
from tkinter import ttk
from plotter import GridPlotter
from settings_frame import SettingMenu
import os
import tkinter.filedialog as filedialog
import h5py
from .settings_build import build_settings
from .signal_plotter import SignalPlotter
import numpy as np
from robustats import weighted_median
import matplotlib.pyplot as plt

def line_fit_robust(xs, ys):
    k = np.float(weighted_median(ys/xs, xs))
    return k

class FlatFielder(tk.Toplevel):
    def __init__(self, master):
        super(FlatFielder, self).__init__(master)
        self.title("Выравнивание пикселей")
        self.plotter = GridPlotter(self)
        self.file = None
        self.plotter.grid(row=0, column=0, sticky="nsew")
        self.settings_menu = SettingMenu(self)
        build_settings(self.settings_menu)
        self.settings_menu.grid(row=0, column=2, sticky="nsew")
        self.signal_plotter = SignalPlotter(self)
        self.signal_plotter.grid(row=0, column=1, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=2)
        self.rowconfigure(0, weight=1)
        self.settings_dict = dict()
        self.settings_menu.commit_action = self.on_apply_settings
        self.t1_setting = self.settings_menu.lookup_setting("time_1")
        self.t2_setting = self.settings_menu.lookup_setting("time_2")
        self.get_mat_file()
        self.drawn_data = None

        btn = ttk.Button(self, text="Расчёт коэффициентов", command=self.on_calculate)
        btn.grid(row=1, column=0, sticky="ew")
        self.on_apply_settings()

    def sync_settings(self):
        self.settings_menu.push_settings_dict(self.settings_dict)

    def propagate_limits(self):
        maxlen = len(self.file["data0"]) // self.settings_dict["samples_mean"] - 1
        if self.file:
            self.t1_setting.set_limits(0, maxlen)
            self.t2_setting.set_limits(0, maxlen)
            self.signal_plotter.view_x(0, maxlen)

    def on_apply_settings(self):
        self.sync_settings()
        self.signal_plotter.set_xrange(self.settings_dict["time_1"], self.settings_dict["time_2"])
        if self.file:
            self.propagate_limits()
            self.draw_plot()
        self.signal_plotter.draw()

    def on_calculate(self):
        if self.drawn_data is not None:
            t1 = self.settings_dict["time_1"]
            t2 = self.settings_dict["time_2"]
            if t1 > t2:
                t1, t2 = t2, t1
            requested_data = self.drawn_data[t1:t2]
            tim_len, x_len, y_len = requested_data.shape
            requested_data = requested_data.reshape((tim_len, x_len * y_len))
            #fig, ax = plt.subplots()
            #fig.show()
            #scattering = ax.scatter(requested_data[:,0],requested_data[:,1])
            coeff_matrix = np.zeros([x_len*y_len, x_len*y_len])
            for i in range(x_len*y_len):
                i_data = requested_data[:, i]
                for j in range(x_len*y_len):
                    j_data = requested_data[:, j]

                    k_ij = line_fit_robust(i_data, j_data)
                    if k_ij != 0:
                        coeff_matrix[i, j] = k_ij
            coeff_matrix = np.nan_to_num(coeff_matrix, nan=0)
            print(coeff_matrix.shape)
            bad_indices, = np.where((coeff_matrix == 0).sum(axis=0) >= x_len*y_len-1)
            good_indices, = np.where((coeff_matrix == 0).sum(axis=0) < x_len * y_len - 1)
            coeff_matrix[bad_indices] = np.zeros(x_len*y_len)

            pivot = good_indices[0]
            sample_row = coeff_matrix[pivot]
            print(len(sample_row))
            sample_median = np.median(sample_row[good_indices])
            sample_distances = np.abs(sample_row - sample_median)
            pivot = np.argmin(sample_distances)

            print("Chosen pivot:", pivot)

            coeff_matrix_reduced = coeff_matrix[good_indices]
            coeff_matrix_reduced = (coeff_matrix_reduced.T/coeff_matrix_reduced[:, pivot]).T

            #good_indices = np.where((coeff_matrix != 0).any(axis=0))
            #assert len(good_indices) > 0
            #correct_row = 0
            #correct_row = np.argmax(coeff_matrix) // coeff_matrix.shape[0]
            #coeff_array = coeff_matrix[correct_row]
            coeff_array = np.median(coeff_matrix_reduced, axis=0)
            draw_coeff_matrix = coeff_array.reshape(x_len, y_len)
            self.plotter.buffer_matrix = draw_coeff_matrix
            self.plotter.update_matrix_plot(update_norm=True)
            self.plotter.draw()
            np.save("flat_fielding.npy", draw_coeff_matrix)

    def get_mat_file(self):
        self.sync_settings()
        if hasattr(self.master, "file"):
            self.file = self.master.file
            if self.file:
                self.propagate_limits()
                self.draw_plot()
        self.signal_plotter.draw()

    def draw_plot(self):
        data0 = self.file["data0"]
        skip = self.settings_dict["samples_mean"]
        res_array = []
        for i in range(0, len(data0), skip):
            layer = np.mean(data0[i:i+skip], axis=0)
            res_array.append(layer)
        print(len(res_array))
        self.drawn_data = np.array(res_array)
        self.signal_plotter.plot_data(self.drawn_data)
        bottom = -10
        top = np.max(self.drawn_data)
        self.signal_plotter.view_y(bottom, top)
        self.signal_plotter.set_yrange(0, top)
