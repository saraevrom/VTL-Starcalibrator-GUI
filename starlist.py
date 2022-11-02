import tkinter

from settings_frame import ScrollableFrame
import pandas as pd
import re


def name_a_star(row):
    data = []
    if "name_IAU" in row.keys():
        data.append(row["name_IAU"])
    if "BayerFlamsteed" in row.keys():
        data.append(row["BayerFlamsteed"])
    if "Hip" in row.keys():
        data.append(f"HIP {int(row['Hip'])}")
    if "HR" in row.keys():
        data.append(f"HR {int(row['HR'])}")
    if data:
        if len(data) > 1:
            return f"{data[0]} ({', '.join(data[1:])})"
        else:
            return data[0]
    else:
        return f"UNKNOWN (StarID {row['StarID']})"


class Starlist(ScrollableFrame):
    def __init__(self, master, *args, **kwargs):
        super(Starlist, self).__init__(master, *args, **kwargs)
        self.stars = []

    def add_star(self, index, row):
        name = name_a_star(row)
        mag = row["Mag"]
        new_var = tkinter.IntVar(self)
        new_entry = tkinter.Checkbutton(self.view_port,text=f"{mag} {name}", variable=new_var)
        new_entry.grid(row=len(self.stars),column=0,sticky="ew")
        self.stars.append((index,new_entry,new_var))

    def clear_stars(self):
        for index, star in self.stars:
            star.destroy()
        self.stars.clear()

    def get_selection(self):
        return [star[0] for star in self.stars if star[2].get()]

    def add_stars(self, stars_df: pd.DataFrame):
        ordered_stars = stars_df.sort_values(by="Mag")
        for index, row in ordered_stars.iterrows():
            self.add_star(index,row)
