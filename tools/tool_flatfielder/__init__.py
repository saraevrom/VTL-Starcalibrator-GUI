from tkinter import ttk
from plotter import GridPlotter
from .dual_highlighting_plotter import DualHighlightingplotter
from settings_frame import SettingMenu
from .settings_build import build_settings
from .signal_plotter import SignalPlotter
import numpy as np
from robustats import weighted_median
from .flat_fielding_methods import ALGO_MAP
import numpy.random as rng
import matplotlib.pyplot as plt
from localization import get_locale

from ..tool_base import ToolBase
from .models import FlatFieldingModel

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

class FlatFielder(ToolBase):
    def __init__(self, master):
        self.file = None
        self.remembered_model = None
        self.apparent_data = None
        super(FlatFielder, self).__init__(master)
        self.title(get_locale("flatfielder.title"))
        self.coeff_plotter = DualHighlightingplotter(self)
        self.coeff_plotter.axes.set_title(get_locale("flatfielder.coefficients.title"))
        self.coeff_plotter.grid(row=0, column=0, sticky="nsew")
        self.coeff_plotter.on_pair_click_callback = self.on_dual_draw

        self.bg_plotter = DualHighlightingplotter(self)
        self.bg_plotter.axes.set_title(get_locale("flatfielder.baselevel.title"))
        self.bg_plotter.grid(row=1, column=0, sticky="nsew")
        self.bg_plotter.on_pair_click_callback = self.on_dual_draw
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

        self.sync_settings()
        self.get_mat_file()
        self.signal_plotter.draw()
        self.drawn_data = None

        btn = ttk.Button(self, text=get_locale("flatfielder.btn.coeffs_calculate"), command=self.on_calculate)
        btn.grid(row=2, column=0, sticky="ew")
        btn = ttk.Button(self, text=get_locale("flatfielder.btn.save"), command=self.on_save_press)
        btn.grid(row=3, column=0, sticky="ew")
        #btn = ttk.Button(self, text=get_locale("flatfielder.btn.random_plot"), command=self.on_random_draw)
        #btn.grid(row=4, column=0, sticky="ew")
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

            used_algo = self.settings_dict["used_algo"]
            if used_algo in ALGO_MAP.keys():
                model = ALGO_MAP[used_algo](requested_data)
            else:
                return

            broke_signal = model.broken_query()
            print("BROKEN_DETECTION:", broke_signal)
            display1, param1 = model.display_parameter_1()
            self.coeff_plotter.axes.set_title(get_locale(display1))
            if param1 is not None:
                self.coeff_plotter.buffer_matrix = param1
            self.coeff_plotter.set_broken(broke_signal)
            self.coeff_plotter.update_matrix_plot(update_norm=True)
            self.coeff_plotter.draw()

            display2, param2 = model.display_parameter_2()
            self.bg_plotter.axes.set_title(get_locale(display2))
            if param2 is not None:
                self.bg_plotter.buffer_matrix = param2
            self.bg_plotter.set_broken(broke_signal)
            self.bg_plotter.update_matrix_plot(update_norm=True)
            self.bg_plotter.draw()
            self.remembered_model = model
            self.draw_plot()
            self.signal_plotter.draw()
            #np.save("flat_fielding.npy", draw_coeff_matrix)

    def on_save_press(self):
        if self.remembered_model is not None:
            model = self.remembered_model
            dead1 = np.logical_not(self.coeff_plotter.alive_pixels_matrix)
            dead2 = np.logical_not(self.bg_plotter.alive_pixels_matrix)
            model.set_broken(np.logical_or(dead1,dead2))
            model.save("flat_fielding.json")
            self.trigger_ff_model_reload()


    def on_loaded_file_success(self):
        self.propagate_limits()
        self.draw_plot()

    def draw_plot(self):
        data0 = self.file["data0"]
        skip = self.settings_dict["samples_mean"]
        res_array = []
        for i in range(0, len(data0), skip):
            layer = np.mean(data0[i:i+skip], axis=0)
            res_array.append(layer)
        print(len(res_array))
        self.drawn_data = np.array(res_array)
        apparent_data = self.drawn_data
        if (self.remembered_model is not None) and self.settings_dict["use_model"]:
            apparent_data = self.remembered_model.apply(apparent_data)
            broke = self.remembered_model.get_broken()
            apparent_data[:, broke] = 0
        self.apparent_data = apparent_data
        self.signal_plotter.plot_data(apparent_data)
        bottom = -10
        top = np.max(self.drawn_data)
        self.signal_plotter.view_y(bottom, top)
        self.signal_plotter.set_yrange(0, top)

    def on_dual_draw(self,p1,p2):
        if self.apparent_data is None:
            return
        t1 = self.settings_dict["time_1"]
        t2 = self.settings_dict["time_2"]
        if t1 > t2:
            t1, t2 = t2, t1
        requested_data = self.apparent_data[t1:t2,:,:]
        print("REQ_SHAPE", requested_data.shape)
        assert (requested_data!=0).any()
        i1, j1 = p1
        i2, j2 = p2
        S_1 = requested_data[:, i1, j1]
        S_2 = requested_data[:, i2, j2]
        print("S1", S_1)
        print("req_data", requested_data[:, i1, j1])
        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlabel(f"S[{i1}, {j1}]")
        ax.set_ylabel(f"S[{i2}, {j2}]")
        ax.scatter(S_1, S_2)
        # xs_test = np.array([min(S_1), max(S_1)])
        # ys_test = draw_coeff_matrix[i2, j2] * (xs_test - draw_bg_matrix[i1, j1]) / draw_coeff_matrix[i1, j1] + \
        #           draw_bg_matrix[i2, j2]
        # ax.plot(xs_test, ys_test)
        fig.show()