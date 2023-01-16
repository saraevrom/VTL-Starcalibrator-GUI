from ..tool_base import ToolBase
from .bg_picking_editor import BgPickingEditor
from .create_settings import build_menu
import gc
import numpy as np
import numba as nb
from ..tool_flatfielder import FlatFieldingModel
from common_GUI import GridPlotter, SettingMenu

import tkinter as tk

@nb.njit()
def putmask_max(arr1,arr2):
    dst = np.zeros(arr1.shape)
    for i in range(arr1.shape[0]):
        for j in range(arr1.shape[1]):
            if arr1[i,j] > arr2[i,j]:
                dst[i,j] = arr1[i,j]
            else:
                dst[i, j] = arr2[i, j]
    return dst


@nb.njit()
def decimate_max(src,window):
    length = src.shape[0]//window
    dst = np.zeros((length,src.shape[1],src.shape[2]))
    for i in range(length):
        i_start = i*window
        i_end = i_start+window
        dst[i] = src[i_start]
        for j in range(i_start+1,i_end):
            dst[i] = putmask_max(dst[i], src[j])
    return dst


class DatasetGenerator(ToolBase):
    def __init__(self, master):
        super().__init__(master)

        left_panel = tk.Frame(self)

        left_panel.pack(side="left", fill="both", expand=True)

        self.plotter = GridPlotter(left_panel)
        self.plotter.pack(side="top", fill="both", expand=True)

        self.interval_editor = BgPickingEditor(left_panel)
        self.interval_editor.pack(side="bottom", fill="x")

        right_panel = tk.Frame(self)
        right_panel.pack(side="right", fill="y")

        self.settings_menu = SettingMenu(right_panel, autocommit=True)
        self.settings_menu.pack(fill="both", expand=True)
        build_menu(self.settings_menu)
        self.cutoff_1_setting = self.settings_menu.lookup_setting("cutoff_start")
        self.cutoff_2_setting = self.settings_menu.lookup_setting("cutoff_end")
        self.settings_dict = dict()
        self.settings_menu.commit_action = self.on_settings_commit
        self.settings_menu.add_tracer("filter_window", self.on_ma_filter_change)
        #self.plotter.grid(row=0, column=0, sticky="nsew", rowspan=2)

    def on_loaded_file_success(self):
        gc.collect()
        self.settings_menu.push_settings_dict(self.settings_dict)
        self.reload_data()
        self.on_settings_commit()
        gc.collect()

    def reload_data(self):
        model = self.get_ff_model()
        self.interval_editor.reload_data(self.file, self.settings_dict, model)
        self.propagate_limits(self.file["data0"].shape[0])

    def on_ma_filter_change(self):
        print("MA filter changed")
        self.reload_data()

    def on_settings_commit(self):
        if self.file:
            self.settings_menu.push_settings_dict(self.settings_dict)

            print("Commit REDRAW")
            self.interval_editor.redraw(self.settings_dict)

    def propagate_limits(self, maxlen):
        self.cutoff_1_setting.set_limits(0, maxlen)
        self.cutoff_2_setting.set_limits(0, maxlen)

    def on_ff_reload(self):
        if self.file:
            self.on_loaded_file_success()