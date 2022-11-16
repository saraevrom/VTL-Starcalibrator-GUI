import tkinter as tk
from tkinter import ttk
from plotter import GridPlotter
from .player_controls import PlayerControls
import os
import numpy as np
from datetime import datetime

class MatPlayer(tk.Toplevel):
    def __init__(self, master):
        super(MatPlayer, self).__init__(master)
        self.title("Воспроизведение")
        self.file = None
        self.plotter = GridPlotter(self)
        self.plotter.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.player_controls = PlayerControls(self, self.on_frame_draw)
        self.player_controls.pack(side=tk.BOTTOM, expand=True, fill=tk.X)
        self.get_mat_file()
        self.divider = None
        self.displacement = None
        if os.path.isfile("flat_fielding.npy"):
            with open("flat_fielding.npy", "rb") as fp:
                self.divider = np.load(fp)
                self.displacement = np.load(fp)

    def on_frame_draw(self, frame_num):
        if self.file:
            frame = self.file["data0"][frame_num]
            ut0 = self.file["UT0"][frame_num]
            time_str = datetime.utcfromtimestamp(ut0).strftime('%Y-%m-%d %H:%M:%S')
            if self.divider is not None:
                frame = (frame - self.displacement) / self.divider
                frame = np.nan_to_num(frame, nan=0)
                frame = frame * (self.divider != 0)
            self.plotter.buffer_matrix = frame
            self.plotter.update_matrix_plot(True)
            self.plotter.axes.set_title(time_str)
            self.plotter.draw()

    def get_mat_file(self):
        if hasattr(self.master, "file"):
            self.file = self.master.file
            if self.file:
                self.player_controls.set_limit(len(self.file["UT0"]))
