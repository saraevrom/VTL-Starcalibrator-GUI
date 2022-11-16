
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
from .flat_fielding_methods import median_corr_flatfield, isotropic_lsq_corr_flatfield
from .flat_fielding_methods import isotropic_lsq_corr_flatfield_parallel

def line_fit_robust(xs, ys):
    k = np.float(weighted_median(ys/xs, xs))
    return k

class LineFitter(object):
    def __init__(self,array):
        self.array = array

    def __call__(self, ij):
        i,j = ij
        i_data = self.array[:, i]
        j_data = self.array[:, j]
        if np.median(i_data)==0 or np.median(j_data)==0:
            return 0
        return line_fit_robust(i_data, j_data)

class FlatFielder(tk.Toplevel):
    def __init__(self, master):
        self.file = None
        self.remembered_coeffs = None
        self.remembered_bg = None
        self.remembered_working_pixels = None
        super(FlatFielder, self).__init__(master)
        self.title("Выравнивание пикселей")
        self.coeff_plotter = GridPlotter(self)
        self.coeff_plotter.axes.set_title("Коэффициенты")
        self.coeff_plotter.grid(row=0, column=0, sticky="nsew")

        self.bg_plotter = GridPlotter(self)
        self.bg_plotter.axes.set_title("Фон")
        self.bg_plotter.grid(row=1, column=0, sticky="nsew")
        self.settings_menu = SettingMenu(self)
        build_settings(self.settings_menu)
        self.settings_menu.grid(row=1, column=1, sticky="nsew")
        self.signal_plotter = SignalPlotter(self)
        self.signal_plotter.grid(row=0, column=1, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.settings_dict = dict()
        self.settings_menu.commit_action = self.on_apply_settings
        self.t1_setting = self.settings_menu.lookup_setting("time_1")
        self.t2_setting = self.settings_menu.lookup_setting("time_2")
        self.get_mat_file()
        self.drawn_data = None

        btn = ttk.Button(self, text="Расчёт коэффициентов", command=self.on_calculate)
        btn.grid(row=2, column=0, sticky="ew")
        btn = ttk.Button(self, text="Сохранить данные", command=self.on_save_press)
        btn.grid(row=3, column=0, sticky="ew")
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

            if self.settings_dict["use_alt_algo"]:
                draw_coeff_matrix, draw_bg_matrix = isotropic_lsq_corr_flatfield_parallel(requested_data, self.settings_dict)
            else:
                draw_coeff_matrix, draw_bg_matrix = median_corr_flatfield(requested_data, self.settings_dict)

            broke_signal = np.array(np.where(draw_coeff_matrix == 0)).T
            print("BROKEN_DETECTION:", broke_signal)
            self.coeff_plotter.buffer_matrix = draw_coeff_matrix
            self.coeff_plotter.set_broken(broke_signal)
            self.coeff_plotter.update_matrix_plot(update_norm=True)
            self.coeff_plotter.draw()

            self.bg_plotter.buffer_matrix = draw_bg_matrix
            self.bg_plotter.set_broken(broke_signal)
            self.bg_plotter.update_matrix_plot(update_norm=True)
            self.bg_plotter.draw()

            self.remembered_coeffs = draw_coeff_matrix
            self.remembered_bg = draw_bg_matrix
            self.remembered_working_pixels = self.coeff_plotter.alive_pixels_matrix
            self.draw_plot(draw_coeff_matrix, draw_bg_matrix)
            self.signal_plotter.draw()
            #np.save("flat_fielding.npy", draw_coeff_matrix)

    def on_save_press(self):
        if self.remembered_coeffs is not None:
            coeffs = self.remembered_coeffs
            coeffs = coeffs * self.remembered_working_pixels
            bg = self.remembered_bg
            bg = bg * self.remembered_working_pixels
            with open("flat_fielding.npy", "wb") as fp:
                np.save(fp, coeffs)
                np.save(fp, bg)

    def get_mat_file(self):
        self.sync_settings()
        if hasattr(self.master, "file"):
            self.file = self.master.file
            if self.file:
                self.propagate_limits()
                self.draw_plot()
        self.signal_plotter.draw()

    def draw_plot(self, coefficients = None, offsets = None):
        data0 = self.file["data0"]
        skip = self.settings_dict["samples_mean"]
        res_array = []
        for i in range(0, len(data0), skip):
            layer = np.mean(data0[i:i+skip], axis=0)
            res_array.append(layer)
        print(len(res_array))
        self.drawn_data = np.array(res_array)
        apparent_data = self.drawn_data
        if coefficients is not None:
            apparent_data = (apparent_data - offsets)/coefficients
            apparent_data = np.nan_to_num(apparent_data)
            apparent_data = apparent_data*(coefficients != 0)
        self.signal_plotter.plot_data(apparent_data)
        bottom = -10
        top = np.max(self.drawn_data)
        self.signal_plotter.view_y(bottom, top)
        self.signal_plotter.set_yrange(0, top)
