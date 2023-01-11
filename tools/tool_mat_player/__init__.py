import tkinter as tk
from plotter import GridPlotter
from .player_controls import PlayerControls
import os
import numpy as np
from datetime import datetime
from ..tool_base import ToolBase
from localization import get_locale
from tk_forms import TkDictForm
from ..tool_flatfielder import FlatFieldingModel

FORM_CONF = {
    "use_filter": {
        "type": "bool",
        "default":False,
        "display_name": get_locale("matplayer.form.use_filter")
    },
    "filter_window": {
        "type": "int",
        "default": 60,
        "display_name": get_locale("matplayer.form.filter_window")
    },
    "use_flatfielding": {
        "type": "bool",
        "default": True,
        "display_name": get_locale("matplayer.form.use_flatfielding")
    }
}

class MatPlayer(ToolBase):
    def __init__(self, master):
        super(MatPlayer, self).__init__(master)
        self.title(get_locale("matplayer.title"))
        self.file = None
        self.form = TkDictForm(self,FORM_CONF)
        self.form.pack(side=tk.RIGHT, fill=tk.Y)
        self.plotter = GridPlotter(self)
        self.plotter.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.player_controls = PlayerControls(self, self.on_frame_draw, self.click_callback)
        self.player_controls.pack(side=tk.BOTTOM, fill=tk.X)
        self.get_mat_file()
        self.form_data = self.form.get_values()

    def on_frame_draw(self, frame_num):
        if self.file:
            #frame_start = time.time()
            #print("Frame START")
            frame = self.frames[frame_num]
            #frame = self.file["data0"][frame_num]
            ut0 = self.ut0_s[frame_num]
            #ut0 = self.file["UT0"][frame_num]
            time_str = datetime.utcfromtimestamp(ut0).strftime('%Y-%m-%d %H:%M:%S')
            ffmodel = self.get_ff_model()
            if self.form_data["use_filter"]:
                window = self.form_data["filter_window"]
                #print("PING!", window)
                slide_bg = np.median(self.file["data0"][frame_num:frame_num+window],axis=0)
                if (ffmodel is not None) and self.form_data["use_flatfielding"]:
                    frame = ffmodel.apply(self.file["data0"][frame_num]) - ffmodel.apply(slide_bg)
            elif (ffmodel is not None) and self.form_data["use_flatfielding"]:
                frame = ffmodel.apply(frame)
            self.plotter.buffer_matrix = frame
            self.plotter.update_matrix_plot(True)
            self.plotter.axes.set_title(time_str)
            #print("Frame calculated:", time.time()-frame_start)
            self.plotter.draw()
            #print("Frame END:", time.time()-frame_start)

    def click_callback(self):
        self.form_data = self.form.get_values()

    def on_loaded_file_success(self):
        self.player_controls.set_limit(len(self.file["UT0"]))
        self.frames = np.array(self.file["data0"])
        self.ut0_s = np.array(self.file["UT0"])
        ffmodel = self.get_ff_model()
        if ffmodel:
            self.plotter.set_broken(ffmodel.broken_query())