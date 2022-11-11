
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
        self.propagate_limits()
        self.signal_plotter.draw()
        if self.file:
            skip = self.settings_dict["samples_mean"]
            data0 = self.file["data0"]
            res_array = None
            for i in range(0, len(self.file), skip):
                layer = np.mean(data0[i:i+skip], axis=0)
                if res_array is not None:
                    res_array = np.vstack([res_array, layer])
                else:
                    res_array = layer
            self.draw_array = res_array

    def get_mat_file(self):
        self.sync_settings()
        if hasattr(self.master, "file"):
            self.file = self.master.file
            self.propagate_limits()