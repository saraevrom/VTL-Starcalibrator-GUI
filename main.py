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
from random_roaming import RandomRoaming
from mat_converter import MatConverter

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

        self.toolsmenu = tk.Menu(self.topmenu, tearoff=0)
        self.toolsmenu.add_command(label="Преобразовать mat файлы", command=self.on_converter_open)

        self.topmenu.add_cascade(label="Файл", menu=self.filemenu)
        self.topmenu.add_cascade(label="Инструменты", menu=self.toolsmenu)
        self.config(menu=self.topmenu)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.file = None
        self.settings_dict = dict()

        self.t1_setting = self.settings.lookup_setting("time_1")
        self.t2_setting = self.settings.lookup_setting("time_2")
        self.roamer = RandomRoaming(self.get_parameters,self.set_parameters,self.calculate_score, self.get_deltas)


    def settings_pull(self):
        self.settings.push_settings_dict(self.settings_dict)

    def settings_push(self, keys=None):
        self.settings.pull_settings_dict(self.settings_dict, keys)

    def cut_frames(self):
        t1 = self.settings_dict["time_1"]
        t2 = self.settings_dict["time_2"]
        if t1 > t2:
            t1, t2 = t2, t1

        return t1, t2

    def get_era_range(self):
        t1, t2 = self.cut_frames()
        win = 0
        if self.settings_dict["display_use_filter"]:
            if not self.settings_dict["global_filter"]:
                win = self.settings_dict["filter_window"]

        assert t1 + win // 2 <= t2 - win // 2
        framespace = np.linspace(t1 + win // 2, t2 - win // 2, self.settings_dict["star_samples"]).astype(int)
        times = Time(self.file["UT0"][framespace], format="unix")
        # era1 = Time(self.file["UT0"][t1 + win // 2], format="unix", scale="utc").earth_rotation_angle(0).radian
        # era2 = Time(self.file["UT0"][t2 - win // 2], format="unix", scale="utc").earth_rotation_angle(0).radian
        # if era1 > era2:
        #     era2 += np.pi * 2
        # eras = np.linspace(era1,era2,self.settings_dict["star_samples"])
        return times.earth_rotation_angle(0).radian, framespace

    def refresh_fg(self):
        if self.file:
            stars = self.star_menu.get_selection_full()
            t1,t2 = self.cut_frames()
            win = 0
            if not self.settings_dict["global_filter"]:
                win = self.settings_dict["filter_window"]
            eras, framespace = self.get_era_range()
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
            print("SCORE_raw:", self.calculate_score(*self.get_parameters()))

    def read_segment(self):
        f1, f2 = self.cut_frames()
        subframes: np.ndarray
        subframes = np.array(self.file["data0"][f1:f2])
        # Вычитаем фон
        if self.settings_dict["display_use_filter"]:
            if self.settings_dict["global_filter"]:
                subframes -= np.median(subframes, axis=0)
            else:
                win = self.settings_dict["filter_window"]
                slide = sliding_window_view(subframes, win, axis=0)
                bg = slide.mean(axis=3)
                subframes = slide[:, :, :, win // 2]
                assert subframes.shape == bg.shape
                subframes = subframes - bg
        return subframes


    def refresh_bg(self):
        if self.file:
            subframes = self.read_segment()
            frame = None
            if self.settings_dict["display_use_max"]:
                frame = subframes.max(axis=0)
            else:
                subframes = (subframes > self.settings_dict["display_threshold"]).astype(np.float64)
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
        if self.settings_dict["optimizer_run"]:
            self.roamer.sync_params()
            for i in range(self.settings_dict["optimizer_steps"]):
                print(f"Step {i}/{self.settings_dict['optimizer_steps']}")
                self.roamer.step()

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

    def calculate_score(self, dec, ra0, psi, f):
        if self.file:
            eras, framespace = self.get_era_range()
            pixels = self.star_menu.get_pixels(eras, dec, ra0, psi, f)
            if len(pixels)>0:
                t, i, j = pixels.T
                frames = np.array(self.file["data0"])[framespace[t], i, j]
                return np.sum(frames)
        return 0

    def get_parameters(self):
        dec = self.settings_dict["dec0"] * np.pi/180
        ra0 = self.settings_dict["ra0"] * np.pi/180
        psi = self.settings_dict["psi"] * np.pi/180
        f = self.settings_dict["f"]
        return dec, ra0, psi, f

    def get_deltas(self):
        dec = self.settings_dict["d_dec0"] * np.pi/180
        ra0 = self.settings_dict["d_ra0"] * np.pi/180
        psi = self.settings_dict["d_psi"] * np.pi/180
        f = self.settings_dict["d_f"]
        return dec, ra0, psi, f

    def set_parameters(self, dec, ra0, psi, f):
        self.settings_dict["dec0"] = dec * 180/np.pi
        self.settings_dict["ra0"] = ra0 * 180/np.pi
        self.settings_dict["psi"] = psi * 180/np.pi
        self.settings_dict["f"] = f
        self.settings_push(["dec0", "ra0", "psi", "f"])

    def on_converter_open(self):
        MatConverter(self)


if __name__ == "__main__":
    root = App()
    root.mainloop()
