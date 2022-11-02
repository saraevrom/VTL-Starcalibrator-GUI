#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk
from plotter import Plotter
from settings_frame import SettingMenu
from vtl_settings_build import build_menu
from starlist import Starlist

class App(tk.Tk):
    def __init__(self):
        super(App, self).__init__()
        self.title("Определение ориентации")
        star_menu = Starlist(self)
        star_menu.grid(row=0, column=0, sticky="nsew")

        plot = Plotter(self)
        plot.grid(row=0, column=1, sticky="nsew")

        settings = SettingMenu(self)
        build_menu(settings)
        settings.grid(row=0, column=2, sticky="nsew")
        topmenu = tk.Menu(self)
        filemenu = tk.Menu(topmenu, tearoff=0)
        topmenu.add_cascade(label="Файл", menu=filemenu)
        self.config(menu=topmenu)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

if __name__ == "__main__":
    root = App()
    root.mainloop()
