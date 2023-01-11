from ..tool_base import ToolBase
from .bg_picking_editor import BgPickingEditor
from .create_settings import build_menu
import gc
from settings_frame import SettingMenu
from parameters import HALF_PIXELS
import numpy as np
import os
from ..tool_flatfielder import FlatFieldingModel
from numpy.lib.stride_tricks import sliding_window_view
import numba as nb


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
        #self.setting_frame = SettingMenu(self)
        self.columnconfigure(0, weight=1)
        #self.rowconfigure(0, weight=1)
        #self.rowconfigure(1, weight=1)
        #self.setting_frame.grid(row=0, column=1, sticky="nsew")
        #build_menu(self.setting_frame)

        self.interval_editor = BgPickingEditor(self)
        self.interval_editor.pack(fill="both", expand=True)

        #self.plotter.grid(row=0, column=0, sticky="nsew", rowspan=2)

    def on_loaded_file_success(self):
        gc.collect()
        # self.interval_editor.clear()
        #
        # model = None
        # if os.path.isfile("flat_fielding.json"):
        #     model = FlatFieldingModel.load("flat_fielding.json")
        # self.interval_editor.display_data(self.file, model)
        # self.interval_editor.draw()
