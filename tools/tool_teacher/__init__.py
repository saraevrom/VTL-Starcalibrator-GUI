from ..tool_base import ToolBase
from .filepool import RandomIntervalAccess, RandomFileAccess, FilePool
import h5py
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from localization import get_locale, format_locale
from trigger_ai import create_trigger_model
import gc
import numpy.random as rng
import numpy as np

class ToolTeacher(ToolBase):
    def __init__(self, master):
        super().__init__(master)
        self.bg_pool = RandomIntervalAccess(self, "teacher.pool_bg.title")
        self.bg_pool.grid(row=0, column=0, sticky="nsew")
        self.fg_pool = RandomFileAccess(self, "teacher.pool_fg.title")
        self.fg_pool.grid(row=0, column=1, sticky="nsew")
        self.interference_pool = RandomFileAccess(self, "teacher.pool_interference.title", allow_clear=True)
        self.interference_pool.grid(row=0, column=2, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.status_display = ScrolledText(self)
        self.status_display.grid(row=0, column=3)
        self.check_passed = False
        self.workon_model = None

        teachbtn = tk.Button(self, text=get_locale("teacher.button.start"), command=self.on_teach)
        teachbtn.grid(row=1, column=0, columnspan=3, sticky="nsew")


    def ensure_model(self):
        if self.workon_model is None:
            self.workon_model = create_trigger_model(128)

    def on_teach(self):
        self.check_files()
        if self.check_passed:
            self.ensure_model()
            gc.collect()
            generator = self.data_generator(100)
            genlist = list(generator)

    def println_status(self, message, tabs=0):
        if tabs == 0:
            self.status_display.insert(tk.INSERT, message + "\n")
        else:
            self.status_display.insert(tk.INSERT, "\t"*tabs + message + "\n")

    def check_pool(self, msg_key, pool: FilePool,fields,allow_empty=False):
        self.println_status(get_locale(msg_key))
        if not (pool.files_list or allow_empty):
            self.check_passed = False
            self.println_status(get_locale("teacher.status.msg_empty"), 1)
        else:
            fails = pool.check_hdf5_fields(fields)
            if fails:
                self.check_passed = False
                for cause in fails:
                    self.println_status(format_locale("teacher.status.msg_missing", **cause), 1)
            else:
                self.println_status(get_locale("teacher.status.msg_ok"), 1)


    def data_generator(self,amount):
        for i in range(amount):
            bg = self.bg_pool.random_access()
            x_data = bg
            if self.fg_pool.files_list:
                if rng.random() < 0.5:
                    interference = self.fg_pool.random_access()
                    x_data = x_data+interference
            if rng.random() < 0.5:
                y_data = np.array([1, 0])
            else:
                y_data = np.array([0, 1])
                fg = self.fg_pool.random_access()
                x_data = x_data + fg

            yield x_data, y_data

    def check_files(self):
        self.status_display.delete('1.0', tk.END)
        self.check_passed = True
        self.check_pool("teacher.status.msg_bg", self.bg_pool, ["data0", "marked_intervals"])
        self.check_pool("teacher.status.msg_fg", self.fg_pool, ["EventsIJ"])
        self.check_pool("teacher.status.msg_it", self.interference_pool, ["EventsIJ"], True)

