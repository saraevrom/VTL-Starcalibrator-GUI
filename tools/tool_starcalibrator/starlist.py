import tkinter

from settings_frame import ScrollableFrame
import pandas as pd
import numpy as np
from astronomy import Star, name_a_star
from astropy.time import Time
from astronomy import range_calculate

class Starlist(ScrollableFrame):
    def __init__(self, master, *args, **kwargs):
        super(Starlist, self).__init__(master, *args, **kwargs)
        self.stars = []
        self.star_callback = None

    def on_selection_change(self, *args):
        if self.star_callback:
            self.star_callback()

    def add_star(self, row):
        name = name_a_star(row)
        mag = row["Mag"]
        new_var = tkinter.IntVar(self)
        new_var.trace("w", self.on_selection_change)
        new_entry = tkinter.Checkbutton(self.contents, text=f"{mag} {name}", variable=new_var)
        new_entry.grid(row=len(self.stars), column=0, sticky="w")
        self.stars.append((Star.from_row(row), new_entry, new_var))

    def clear_stars(self):
        for star in self.stars:
            star[1].destroy()
        self.stars.clear()

    def get_selection(self):
        return [star[0] for star in self.stars if star[2].get()]

    def get_pixels(self, era, dec, ra0, psi, f):
        stars = self.get_selection()
        t = np.arange(len(era))
        rows = None
        for star in stars:
            i, j = star.get_pixel(era, dec, ra0, psi, f)
            accessible = np.logical_and(i >= 0, j >= 0)
            new_arr = np.array([t[accessible], i[accessible], j[accessible]]).T
            if rows is None:
                rows = new_arr
            else:
                rows = np.vstack([rows, new_arr])
        if rows is None:
            rows = np.array([])
        res = np.unique(rows, axis=0)
        return res



    def get_selection_full(self):
        return [(star[0],bool(star[2].get())) for star in self.stars]

    def add_stars(self, stars_df: pd.DataFrame):
        ordered_stars = stars_df.sort_values(by="Mag")
        for index, row in ordered_stars.iterrows():
            self.add_star(row)

