import os
import tkinter as tk
from settings_frame import SettingMenu
from .vtl_settings_build import build_menu
from .starlist import Starlist
from .starplotter import StarGridPlotter
import tkinter.filedialog as filedialog
import numpy as np
import pandas as pd
from numpy.lib.stride_tricks import sliding_window_view

from astropy.time import Time
from astronomy import range_calculate, to_altaz
import json
from .random_roaming import RandomRoaming, maximize
from ..tool_mat_converter import MatConverter

import matplotlib.pyplot as plt
from parameters import MAIN_LATITUDE, MAIN_LONGITUDE
from localization import get_locale
from ..tool_base import ToolBase

class StarCalibrator(ToolBase):
    def __init__(self, master):
        super(StarCalibrator, self).__init__(master)
        self.title(get_locale("app.title"))

        leftpanel = tk.Frame(self)
        leftpanel.grid(row=0, column=0, sticky="nsew")

        load_settings_btn = tk.Button(leftpanel, text=get_locale("app.menu.file.load_settings"),
                                      command=self.on_settings_load)
        load_settings_btn.grid(row=0, column=0, sticky="ew")
        save_settings_btn = tk.Button(leftpanel, text=get_locale("app.menu.file.save_settings"),
                                      command=self.on_settings_save)
        save_settings_btn.grid(row=1, column=0, sticky="ew")
        leftpanel.columnconfigure(0,weight=1)

        self.star_menu = Starlist(leftpanel)
        self.star_menu.grid(row=2, column=0, sticky="nsew")
        self.star_menu.star_callback = self.on_star_selection_change

        #leftpanel.rowconfigure(0, weight=1)
        #leftpanel.rowconfigure(1, weight=1)
        leftpanel.rowconfigure(2, weight=1)

        self.plot = StarGridPlotter(self)
        self.plot.on_right_click_callback = self.popup_draw_signal
        self.plot.grid(row=0, column=1, sticky="nsew")
        self.broken = []

        self.settings = SettingMenu(self)
        build_menu(self.settings)
        self.settings.grid(row=0, column=2, sticky="nsew")
        self.settings.commit_action = self.on_settings_change
        self.settings.add_tracer("Mag_threshold", self.read_stars)
        self.settings.add_tracer("star_samples", self.on_star_sample_change)
        self.settings.add_tracer("time_1", self.read_stars)
        self.settings.add_tracer("time_2", self.read_stars)

        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.file = None
        self.data_cache = None
        self.settings_dict = dict()

        self.t1_setting = self.settings.lookup_setting("time_1")
        self.t2_setting = self.settings.lookup_setting("time_2")
        self.roamer = RandomRoaming(self.get_parameters,self.set_parameters, self.calculate_score, self.get_deltas)
        self.get_mat_file()


    def settings_pull(self):
        self.settings.push_settings_dict(self.settings_dict)

    def settings_push(self, keys=None):
        self.settings.pull_settings_dict(self.settings_dict, keys)

    def cut_frames(self):
        t1 = self.settings_dict["time_1"]
        t2 = self.settings_dict["time_2"]
        if t1 > t2:
            t1, t2 = t2, t1
            self.settings_dict["time_1"] = t1
            self.settings_dict["time_2"] = t2
            self.settings_push(["time_1", "time_2"])

        return t1, t2

    def get_era_range(self):
        t1, t2 = self.cut_frames()
        win = 0
        if self.settings_dict["display_use_filter"]:
            if not self.settings_dict["global_filter"]:
                win = self.settings_dict["filter_window"]

        assert t1 + win // 2 <= t2 - win // 2
        step = (t2 - t1 - win) // self.settings_dict["star_samples"]
        framespace = np.arange(t1 + win // 2, t2 - win // 2, step)
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
            t1, t2 = self.cut_frames()
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

            # print("SCORE_raw:", self.calculate_score(*self.get_parameters()))

    def refresh_broken_pixels(self):
        model = self.get_ff_model()
        if model:
            broke = model.broken_query()
            self.plot.set_broken(broke)
            self.broken = broke.T

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
        return self.flat_field_opt(subframes)

    def flat_field_opt(self, data_array):
        if not self.settings_dict["flatfielding"]:
            return data_array
        flat_field_model = self.get_ff_model()
        if flat_field_model is None:
            return data_array
        # print("BROKEN:", broke)
        retdata = flat_field_model.apply(data_array)
        return retdata

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
            self.refresh_broken_pixels()
            self.plot.draw()

    def read_stars(self):
        if self.file:
            # f1, f2 = 0, len(self.file["data0"])-1
            f1, f2 = self.cut_frames()
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
            if self.settings_dict["optimizer_descent"]:
                params = self.get_parameters()
                new_params, success = maximize(self.calculate_score, params,
                                               method=self.settings_dict["optimizer_descent_mode"])
                if success:
                    self.set_parameters(*new_params)
            else:
                self.roamer.sync_params()
                for i in range(self.settings_dict["optimizer_steps"]):
                    print(f"Step {i}/{self.settings_dict['optimizer_steps']}")
                    self.roamer.step()

            dec, ra0, psi, f = self.get_parameters()
            lat = MAIN_LATITUDE*np.pi/180
            lon = MAIN_LONGITUDE*np.pi/180
            alt, az = to_altaz(dec, ra0, lat, lon)
            print(f"        ALT  (°): {alt * 180 / np.pi}")
            print(f"        AZ  (°): {az * 180 / np.pi}")
        self.data_cache = None

    def on_star_sample_change(self):
        self.plot.delete_lines()
        self.refresh_fg()

    def on_settings_load(self):
        filename = filedialog.askopenfilename(title=get_locale("app.filedialog.load_settings.title"),
                                              filetypes=[(get_locale("app.filedialog_formats.settings_json"), "*.json")],
                                              parent=self)
        if filename and os.path.isfile(filename):
            with open(filename, "r") as f:
                self.settings_dict = json.load(f)
                self.settings_push()

    def on_settings_save(self):
        filename = filedialog.asksaveasfilename(title=get_locale("app.filedialog.save_settings.title"),
                                                filetypes=[(get_locale("app.filedialog_formats.settings_json"), "*.json")],
                                                parent=self)
        if filename:
            with open(filename, "w") as f:
                json.dump(self.settings_dict, f)

    def on_star_selection_change(self):
        self.refresh_fg()
        self.plot.update_matrix_plot(True)
        self.plot.draw()


    def popup_draw_signal(self,i,j):
        if self.file:
            t1, t2 = self.cut_frames()
            signal = self.file["data0"][t1:t2, i, j]
            if self.settings_dict["display_use_filter"]:
                if self.settings_dict["global_filter"]:
                    signal -= np.median(signal, axis=0)
                else:
                    win = self.settings_dict["filter_window"]
                    slide = sliding_window_view(signal, win, axis=0)
                    bg = slide.mean(axis=-1)
                    signal = slide[:, win // 2]
                    assert signal.shape == bg.shape
                    signal = signal - bg
                    t1 += win//2
                    t2 = t1+signal.shape[0]
            flat_field_model = self.get_ff_model()
            if flat_field_model is not None:
                signal = flat_field_model.apply_single(signal, i, j)
            fig, ax = plt.subplots()
            xs = np.arange(t1, t2)
            ax.plot(xs, signal)
            ax.set_title(f"[{i}, {j}]")
            fig.show()


    def on_loaded_file_success(self):
            self.t1_setting.set_limits(0, len(self.file["data0"])-1)
            self.t2_setting.set_limits(0, len(self.file["data0"])-1)
            self.refresh()
            self.read_stars()


    def calculate_score(self, dec, ra0, psi, f):
        final_calc_func = np.sum
        if self.settings_dict["optimizer_use_min"]:
            final_calc_func = np.min
        if self.file:
            eras, framespace = self.get_era_range()
            pixels = self.star_menu.get_pixels(eras, dec, ra0, psi, f)
            if len(pixels) > 0:
                t, i, j = pixels.T
                if self.broken is not None:
                    i_broken_ids, j_broken_ids = self.broken
                    i_break_test = np.isin(i, i_broken_ids)
                    j_break_test = np.isin(j, j_broken_ids)
                    ok_indices = np.logical_not(np.logical_and(i_break_test, j_break_test))
                    t, i, j = pixels[ok_indices].T

                frame_indices = framespace[t]
                # reind = np.arange(len(frame_indices))
                # asorted = np.argsort(frame_indices)

                if self.data_cache is None:
                    self.data_cache = np.array(np.array(self.file["data0"]))
                frames = self.data_cache[frame_indices, i, j]
                return final_calc_func(frames)
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