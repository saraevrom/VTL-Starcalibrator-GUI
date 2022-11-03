#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import ttk
from plotter import Plotter
from settings_frame import SettingMenu
from vtl_settings_build import build_menu
from starlist import Starlist
import tkinter.filedialog as filedialog
import h5py
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from astropy.time import Time
from astronomy import range_calculate
import json

class App(tk.Tk):
    def __init__(self):
        super(App, self).__init__()
        self.title("Определение ориентации")
        self.star_menu = Starlist(self)
        self.star_menu.grid(row=0, column=0, sticky="nsew")
        self.star_menu.star_callback = self.on_star_selection_change

        self.plot = Plotter(self)
        self.plot.grid(row=0, column=1, sticky="nsew")

        self.settings = SettingMenu(self)
        build_menu(self.settings)
        self.settings.grid(row=0, column=2, sticky="nsew")
        self.settings.commit_action = self.on_settings_change
        self.settings.add_tracer("Mag_threshold", self.read_stars)
        self.settings.add_tracer("star_samples", self.on_star_sample_change)

        self.topmenu = tk.Menu(self)

        self.filemenu = tk.Menu(self.topmenu, tearoff=0)
        self.filemenu.add_command(label="Oткрыть mat файл", command=self.open_mat_file)
        self.filemenu.add_command(label="Загрузить настройки", command=self.on_settings_load)
        self.filemenu.add_command(label="Сохранить настройки", command=self.on_settings_save)

        self.topmenu.add_cascade(label="Файл", menu=self.filemenu)
        self.config(menu=self.topmenu)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.file = None
        self.settings_dict = dict()

        self.t1_setting = self.settings.lookup_setting("time_1")
        self.t2_setting = self.settings.lookup_setting("time_2")


    def settings_pull(self):
        self.settings.push_settings_dict(self.settings_dict)

    def settings_push(self):
        self.settings.pull_settings_dict(self.settings_dict)

    def cut_frames(self):
        t1 = self.settings_dict["time_1"]
        t2 = self.settings_dict["time_2"]
        if t1 > t2:
            t1, t2 = t2, t1

        return t1, t2


    def refresh_fg(self):
        if self.file:
            stars = self.star_menu.get_selection_full()
            t1,t2 = self.cut_frames()
            win = 0
            if not self.settings_dict["global_filter"]:
                win = self.settings_dict["filter_window"]
            era1 = Time(self.file["UT0"][t1+win//2], format="unix", scale="utc").earth_rotation_angle(0).radian
            era2 = Time(self.file["UT0"][t2-win//2], format="unix", scale="utc").earth_rotation_angle(0).radian
            if era1>era2:
                era2+= np.pi*2
            eras = np.linspace(era1,era2,self.settings_dict["star_samples"])
            for star, visibility in stars:
                if visibility:
                    xs,ys,visibles = star.get_local_coords(eras, self.settings_dict["dec0"]*np.pi/180,
                                                           self.settings_dict["ra0"]*np.pi/180,
                                                           self.settings_dict["psi"]*np.pi/180,
                                                           self.settings_dict["f"])
                    if (visibles > 0).all():
                        self.plot.set_line(star.identifier, xs, ys, star.name)
                else:
                    self.plot.remove_line(star.identifier)



    def refresh_bg(self):
        if self.file:
            f1, f2 = self.cut_frames()
            subframes: np.ndarray
            subframes = np.array(self.file["data0"][f1:f2])
            # Вычитаем фон
            if self.settings_dict["global_filter"]:
                subframes -= np.median(subframes, axis=0)
            else:
                win = self.settings_dict["filter_window"]
                slide = sliding_window_view(subframes, win, axis=0)
                bg = slide.mean(axis=3)
                subframes = slide[:, :, :, win//2]
                assert subframes.shape == bg.shape
                subframes = subframes - bg
            # Обрезаем порог
            subframes = (subframes > self.settings_dict["display_threshold"]).astype(np.float64)
            #Формируем кадр
            frame = subframes.sum(axis=0)
            self.plot.buffer_matrix = frame
            self.plot.update_matrix_plot(True)
            self.plot.draw()

    def read_stars(self):
        if self.file:
            f1, f2 = 0, len(self.file["data0"])-1
            ut1 = Time(self.file["UT0"][f1], format="unix",scale="utc")
            ut2 = Time(self.file["UT0"][f2], format="unix",scale="utc")
            hygfull = pd.read_csv("hygfull_mod.csv", sep=",")
            hygfull = hygfull[hygfull["Mag"] < self.settings_dict["Mag_threshold"]]
            ra_low, ra_high, dec_low, dec_high = range_calculate(self.settings_dict, ut1, ut2)
            ra_low *= 12 / np.pi
            ra_high *= 12 / np.pi
            dec_low *= 180 / np.pi
            dec_high *= 180 / np.pi

            print(ra_low, ra_high, dec_low, dec_high)
            if ra_low<=ra_high:
                hygfull = hygfull[np.logical_and(hygfull["RA"] >= ra_low, hygfull["RA"] <= ra_high)]
            else:
                hygfull = hygfull[np.logical_or(hygfull["RA"] >= ra_low, hygfull["RA"] <= ra_high)]
            hygfull = hygfull[np.logical_and(hygfull["Dec"] >= dec_low, hygfull["Dec"] <= dec_high)]
            self.star_menu.clear_stars()
            self.star_menu.add_stars(hygfull)
            self.plot.delete_lines()
            self.refresh_fg()

    def refresh(self):
        self.settings_pull()
        self.refresh_fg()
        self.refresh_bg()

    def on_settings_change(self):
        self.refresh()

    def on_star_sample_change(self):
        self.plot.delete_lines()
        self.refresh_fg()

    def on_settings_load(self):
        filename = filedialog.askopenfilename(title="Загрузка настроек",
                                              filetypes=[("JSON файл с настройками", "*.json")])
        if filename and os.path.isfile(filename):
            with open(filename, "r") as f:
                self.settings_dict = json.load(f)
                self.settings_push()

    def on_settings_save(self):
        filename = filedialog.asksaveasfilename(title="Сохранение настроек",
                                                filetypes=[("JSON файл с настройками", "*.json")])
        if filename:
            with open(filename, "w") as f:
                json.dump(self.settings_dict, f)

    def on_star_selection_change(self):
        self.refresh_fg()
        self.plot.update_matrix_plot(True)
        self.plot.draw()

    def open_mat_file(self):
        filename = filedialog.askopenfilename(title="Открыть mat файл",
                                              filetypes=[("Обработанные mat файлы", "*.mat *.hdf")])
        if filename and os.path.isfile(filename):
            new_file = h5py.File(filename, "r")
            if self.file:
                self.file.close()
            self.file = new_file
            self.t1_setting.set_limits(0, len(self.file["data0"])-1)
            self.t2_setting.set_limits(0, len(self.file["data0"])-1)
            self.refresh()
            self.read_stars()


if __name__ == "__main__":
    root = App()
    root.mainloop()
