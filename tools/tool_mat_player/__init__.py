import tkinter as tk
from localized_GUI.plotter import GridPlotter
from .player_controls import PlayerControls
import numpy as np
from datetime import datetime
from ..tool_base import ToolBase
from localization import get_locale
from common_GUI import TkDictForm
from parameters import DATETIME_FORMAT
from preprocessing.denoising import moving_average_subtract
import matplotlib.pyplot as plt

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
        self.plotter.on_right_click_callback = self.on_pixel_rmb
        self.player_controls = PlayerControls(self, self.on_frame_draw, self.click_callback)
        self.player_controls.pack(side=tk.BOTTOM, fill=tk.X)
        self.get_mat_file()
        self.form_data = self.form.get_values()
        self.fig, self.ax = None, None

    def on_frame_draw(self, frame_num):
        if self.file:
            #frame_start = time.time()
            #print("Frame START")
            frame = self.frames[frame_num]
            #frame = self.file["data0"][frame_num]
            ut0 = self.ut0_s[frame_num]
            #ut0 = self.file["UT0"][frame_num]
            time_str = datetime.utcfromtimestamp(ut0).strftime(DATETIME_FORMAT)
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
        self.player_controls.set_limit(len(self.file["UT0"]) - 1)
        self.frames = np.array(self.file["data0"])
        self.ut0_s = np.array(self.file["UT0"])
        self.player_controls.time_link(self.ut0_s)
        #self.plotter.draw()
        self.poke()

    def poke(self):
        self.player_controls.draw_frame()

    def on_ff_reload(self):
        ffmodel = self.get_ff_model()
        self.plotter.set_broken(ffmodel.broken_query())
        self.plotter.draw()
        self.poke()


    def handle_mpl_close(self, mpl_event):
        if self.fig is None:
            return
        if mpl_event.canvas.figure == self.fig:
            print("Closed last figure. Figure resetting.")
            self.fig = None
            self.ax = None
    def on_pixel_rmb(self, i, j):
        if self.file:
            print("DRAW", i, j)
            start, end = self.player_controls.get_selected_range()
            print("FROM", start, "TO", end)
            xs = self.ut0_s[start: end+1]
            ys = self.frames[start: end+1, i, j]
            if self.form_data["use_filter"]:
                ys = moving_average_subtract(ys, self.form_data["filter_window"])
            if self.fig is None:
                self.fig, self.ax = plt.subplots()
                self.fig.canvas.mpl_connect('close_event', self.handle_mpl_close)
            self.ax.plot(xs, ys, label=f"[{i+1},{j+1}]")
            self.ax.legend()
            self.fig.show()