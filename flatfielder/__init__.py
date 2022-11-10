
import tkinter as tk
from tkinter import ttk
from plotter import GridPlotter
from settings_frame import SettingMenu
import os
import tkinter.filedialog as filedialog
import h5py
from .settings_build import build_settings
from .signal_plotter import SignalPlotter

class FlatFielder(tk.Toplevel):
    def __init__(self, master):
        super(FlatFielder, self).__init__(master)
        self.title("Выравнивание пикселей")
        self.plotter = GridPlotter(self)
        self.file = None
        self.get_mat_file()
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

    def get_mat_file(self):
        if hasattr(self.master, "file"):
            self.file = self.master.file
        else:
            return None
