import gc
from tkinter import ttk
import tkinter as tk

import tqdm
import numba as nb
from .dual_highlighting_plotter import DualHighlightingplotter
from vtl_common.common_GUI import SettingMenu
from .settings_build import build_settings
from .signal_plotter import SignalPlotter
import numpy as np
from .flat_fielding_methods import ALGO_MAP
import matplotlib.pyplot as plt
from vtl_common.localization import get_locale
# import tkinter.filedialog as filedialog
from vtl_common.workspace_manager import Workspace

from ..tool_base import ToolBase
from .models import FlatFieldingModel, Chain
import os.path as ospath


FF_WORKSPACE = Workspace("ff_calibration")


REPLACE = 0
APPEND = 1
AMEND = 2


@nb.njit(cache=True)
def collapse_array(data0, skip):
    frames, width, height = data0.shape()
    res_length = int(np.ceil(frames/skip))
    res_array = np.zeros((res_length,width,height))
    j = 0
    for i in range(0, len(data0), skip):
        layer = np.mean(data0[i:i + skip], axis=0)
        res_array[j] = layer
        j+=1
    return res_array

class FlatFielder(ToolBase):
    def __init__(self, master):
        self.file = None
        self.remembered_model = None
        self.apparent_data = None
        self.remembered_settings = dict()
        super(FlatFielder, self).__init__(master)
        self.title(get_locale("flatfielder.title"))
        self.coeff_plotter = DualHighlightingplotter(self)
        self.coeff_plotter.axes.set_title(get_locale("flatfielder.coefficients.title"))
        self.coeff_plotter.grid(row=1, column=0, sticky="nsew")
        self.coeff_plotter.on_pair_click_callback = self.on_dual_draw

        self.bg_plotter = DualHighlightingplotter(self)
        self.bg_plotter.axes.set_title(get_locale("flatfielder.baselevel.title"))
        self.bg_plotter.grid(row=1, column=1, sticky="nsew")
        self.bg_plotter.on_pair_click_callback = self.on_dual_draw

        settings_menu_parent = tk.Frame(self)
        settings_menu_parent.columnconfigure(0, weight=1)
        settings_menu_parent.rowconfigure(0, weight=1)

        self.settings_menu = SettingMenu(settings_menu_parent,True)
        settings_menu_parent.grid(row=0, column=1, sticky="nsew")
        build_settings(self.settings_menu)
        self.settings_menu.grid(row=0, column=0, sticky="nsew", columnspan=3)

        self.signal_plotter = SignalPlotter(self)
        self.signal_plotter.grid(row=0, column=0, sticky="nsew")

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.settings_dict = dict()
        self.settings_menu.commit_action = self.on_apply_settings


        self.samples_mean_setting = self.settings_menu.lookup_setting("samples_mean")
        self.t1_setting = self.settings_menu.lookup_setting("time_1")
        self.t2_setting = self.settings_menu.lookup_setting("time_2")

        self.sync_settings()
        self.get_mat_file()
        self.signal_plotter.draw()
        self.drawn_data = None
        self.model_change_mode = REPLACE

        btn = ttk.Button(settings_menu_parent, text=get_locale("flatfielder.btn.coeffs_calculate"), command=self.on_calculate)
        btn.grid(row=1, column=0, sticky="ew")
        btn = ttk.Button(settings_menu_parent, text=get_locale("flatfielder.btn.append"), command=self.on_append)
        btn.grid(row=1, column=1, sticky="ew")
        btn = ttk.Button(settings_menu_parent, text=get_locale("flatfielder.btn.amend"), command=self.on_amend)
        btn.grid(row=1, column=2, sticky="ew")
        btn = ttk.Button(settings_menu_parent, text=get_locale("flatfielder.btn.save"), command=self.on_save_press)
        btn.grid(row=2, column=0, sticky="ew", columnspan=3)
        #btn = ttk.Button(self, text=get_locale("flatfielder.btn.random_plot"), command=self.on_random_draw)
        #btn.grid(row=4, column=0, sticky="ew")
        self.on_apply_settings()

    def sync_settings(self):
        self.settings_menu.push_settings_dict(self.settings_dict)
        t1 = self.settings_dict["time_1"]
        t2 = self.settings_dict["time_2"]
        if t1 > t2:
            t1, t2 = t2, t1
            self.settings_dict["time_1"] = t1
            self.settings_dict["time_2"] = t2
            self.back_sync_settings(["time_1", "time_2"])

    def back_sync_settings(self, keys=None):
        self.settings_menu.pull_settings_dict(self.settings_dict, keys)

    def propagate_limits(self):
        maxlen = len(self.file["data0"]) // self.settings_dict["samples_mean"] - 1
        if self.file:
            self.t1_setting.set_limits(0, maxlen)
            self.t2_setting.set_limits(0, maxlen)
            t1 = self.settings_dict["time_1"]
            t2 = self.settings_dict["time_2"]
            self.signal_plotter.view_x(t1, t2)

    def on_apply_settings(self):
        self.sync_settings()
        self.signal_plotter.set_xrange(self.settings_dict["time_1"], self.settings_dict["time_2"])
        if self.file:
            self.propagate_limits()
            self.draw_plot()
        self.signal_plotter.draw()

    def on_amend(self):
        self.model_change_mode = AMEND
        self.on_calculate_common()

    def on_append(self):
        self.model_change_mode = APPEND
        self.on_calculate_common()

    def on_calculate(self):
        self.model_change_mode = REPLACE
        self.on_calculate_common()

    def on_calculate_common(self):
        if self.drawn_data is not None:
            # t1 = self.settings_dict["time_1"]
            # t2 = self.settings_dict["time_2"]
            #assert t2 > t1
            #requested_data = self.drawn_data[t1:t2]
            requested_data = self.drawn_data[:]
            if (self.model_change_mode == APPEND) and (self.remembered_model is not None):
                #apply data for next stage
                requested_data = self.remembered_model.apply(requested_data)
            elif self.model_change_mode == AMEND:
                if isinstance(self.remembered_model, Chain):
                    requested_data = self.remembered_model.apply_amending(requested_data)

            used_algo = self.settings_dict["used_algo"]
            if used_algo in ALGO_MAP.keys():
                algo, iden = ALGO_MAP[used_algo]
                model = algo(requested_data)
                if model is None:
                    return
            else:
                return

            if self.model_change_mode==REPLACE:
                self.remembered_model = model
            else:
                # Chaining models!
                # But do not turn FF into perceptron though
                if not isinstance(self.remembered_model, Chain):
                    tmpmodel = self.remembered_model
                    self.remembered_model = Chain()
                    if isinstance(tmpmodel, FlatFieldingModel):
                        self.remembered_model.append_model(tmpmodel)
                if self.model_change_mode == APPEND:
                    self.remembered_model.append_model(model)
                elif self.model_change_mode == AMEND:
                    self.remembered_model.amend_model(model)
                else:
                    return

            # del model # to prevent usage
            print("MODEL:", self.remembered_model)
            self.remembered_model.reset_broken()
            broke_signal = self.remembered_model.broken_query()
            print("BROKEN_DETECTION:", broke_signal)
            display1, param1 = self.remembered_model.display_parameter_1()
            self.coeff_plotter.axes.set_title(get_locale(display1))
            if param1 is not None:
                self.coeff_plotter.buffer_matrix = param1
            self.coeff_plotter.set_broken(broke_signal)
            self.coeff_plotter.update_matrix_plot(update_norm=True)
            self.coeff_plotter.draw()

            display2, param2 = self.remembered_model.display_parameter_2()
            self.bg_plotter.axes.set_title(get_locale(display2))
            if param2 is not None:
                self.bg_plotter.buffer_matrix = param2
            self.bg_plotter.set_broken(broke_signal)
            self.bg_plotter.update_matrix_plot(update_norm=True)
            self.bg_plotter.draw()
            self.remembered_settings.update(self.settings_dict)
            self.draw_plot()
            self.signal_plotter.draw()
            #np.save("flat_fielding.npy", draw_coeff_matrix)

    def on_save_press(self):
        if self.remembered_model is not None:
            t1 = self.remembered_settings["time_1"]
            t2 = self.remembered_settings["time_2"]
            used_algo = self.remembered_settings["used_algo"]
            av = self.remembered_settings["samples_mean"]
            algo, iden = ALGO_MAP[used_algo]
            fbase = self.get_loaded_filename()
            fbase = ospath.splitext(fbase)[0]

            if isinstance(self.remembered_model, Chain):
                initial_filename = f"flat_fielding_src-{fbase}___chain.json"
            else:
                initial_filename = f"flat_fielding_src-{fbase}___{av}_{t1}-{t2}_{iden}.json"
            filename = FF_WORKSPACE.asksaveasfilename(parent=self,
                                                      title=get_locale("flatfielder.filedialog.save_ff_settings.title"),
                                                      filetypes=[
                                                          (get_locale("app.filedialog_formats.ff_json"), "*.json")
                                                      ],
                                                      initialfile=initial_filename
                                                    )
            if filename:
                model = self.remembered_model
                dead1 = np.logical_not(self.coeff_plotter.alive_pixels_matrix)
                dead2 = np.logical_not(self.bg_plotter.alive_pixels_matrix)
                model.set_broken(np.logical_or(dead1,dead2))
                model.save(filename)
                #self.trigger_ff_model_reload()


    def on_loaded_file_success(self):
        self._last_skip = None
        self._collapsed_data = None
        elements = self.file["data0"].shape[0]
        CLAMP_SAMPLES = 8*3600
        if elements>CLAMP_SAMPLES:
            print("FF: too many samples!", elements)
            self.samples_mean_setting.set_value(elements//CLAMP_SAMPLES)

        self.on_apply_settings()
        #self.propagate_limits()
        #self.draw_plot()

    def draw_plot(self):
        data0 = self.file["data0"]
        skip = self.settings_dict["samples_mean"]
        t1 = self.settings_dict["time_1"]
        t2 = self.settings_dict["time_2"]
        if t1 > t2:
            t1, t2 = t2, t1


        def get_range():
            return range(t1*skip, t2*skip, skip)
            #return range(0, len(data0), skip)

        res_array = np.zeros(shape=(len(get_range()),data0.shape[1],data0.shape[2]))
        gc.collect()
        j = 0
        for i in tqdm.tqdm(get_range()):
            layer = np.mean(data0[i:i+skip], axis=0)
            res_array[j]=layer
            j+=1
        assert j==res_array.shape[0]
        #res_array = collapse_array(np.array(data0), skip) # Lord have mercy

        self.drawn_data = np.array(res_array)
        apparent_data = self.drawn_data
        if (self.remembered_model is not None) and self.settings_dict["use_model"]:
            apparent_data = self.remembered_model.apply_nobreak(apparent_data)
            broke = self.remembered_model.get_broken()
            apparent_data[:, broke] = 0
        self.apparent_data = apparent_data
        self.signal_plotter.plot_data(apparent_data,offset=t1)
        bottom = -10
        top = np.max(apparent_data)
        print("LIMITS:", bottom, top)
        self.signal_plotter.view_y(bottom, top)

        self.signal_plotter.set_yrange(0, top)

    def on_dual_draw(self,p1,p2):
        if self.apparent_data is None:
            return
        # t1 = self.settings_dict["time_1"]
        # t2 = self.settings_dict["time_2"]
        # if t1 > t2:
        #     t1, t2 = t2, t1
        # requested_data = self.apparent_data[t1:t2,:,:]
        requested_data = self.apparent_data[:,:,:]
        #outdata = np.concatenate([self.apparent_data[:t1,:,:], self.apparent_data[t2:,:,:]])
        assert (requested_data!=0).any()
        i1, j1 = p1
        i2, j2 = p2
        S_1 = requested_data[:, i1, j1]
        S_2 = requested_data[:, i2, j2]

        #S_1_o = outdata[:, i1, j1]
        #S_2_o = outdata[:, i2, j2]
        fig, ax = plt.subplots()
        ax.axis('equal')
        ax.set_xlabel(f"S[{i1}, {j1}]")
        ax.set_ylabel(f"S[{i2}, {j2}]")
        #ax.scatter(S_1_o, S_2_o)
        ax.scatter(S_1, S_2)
        maxval = np.max(np.concatenate([S_1, S_2]))
        ax.plot([0, maxval], [0, maxval])
        # xs_test = np.array([min(S_1), max(S_1)])
        # ys_test = draw_coeff_matrix[i2, j2] * (xs_test - draw_bg_matrix[i1, j1]) / draw_coeff_matrix[i1, j1] + \
        #           draw_bg_matrix[i2, j2]
        # ax.plot(xs_test, ys_test)
        fig.show()