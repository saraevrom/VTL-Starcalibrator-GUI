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
        self.mat_file = None

    def add_star(self, row):
        name = name_a_star(row)
        mag = row["Mag"]
        new_var = tkinter.IntVar(self)
        new_entry = tkinter.Checkbutton(self.view_port, text=f"{mag} {name}", variable=new_var)
        new_entry.grid(row=len(self.stars), column=0, sticky="ew")
        self.stars.append((Star.from_row(row), new_entry, new_var))

    def clear_stars(self):
        for star in self.stars:
            star[1].destroy()
        self.stars.clear()

    def get_selection(self):
        return [star[0] for star in self.stars if star[2].get()]

    def add_stars(self, stars_df: pd.DataFrame):
        ordered_stars = stars_df.sort_values(by="Mag")
        for index, row in ordered_stars.iterrows():
            self.add_star(row)

    def update_mat_file(self,f):
        self.mat_file = f
