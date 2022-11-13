import tkinter as tk
from tkinter import ttk
from plotter import GridPlotter
from .player_controls import PlayerControls
import os
import numpy as np


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
        if os.path.isfile("flat_fielding.npy"):
            self.divider = np.load("flat_fielding.npy")

    def on_frame_draw(self, frame_num):
        if self.file:
            frame = self.file["data0"][frame_num]
            if self.divider is not None:
                frame = frame / self.divider
                frame = np.nan_to_num(frame, nan=0)
                frame = frame * (self.divider != 0)
            self.plotter.buffer_matrix = frame
            self.plotter.update_matrix_plot(True)
            self.plotter.draw()

    def get_mat_file(self):
        if hasattr(self.master, "file"):
            self.file = self.master.file
            if self.file:
                self.player_controls.set_limit(len(self.file["UT0"]))
