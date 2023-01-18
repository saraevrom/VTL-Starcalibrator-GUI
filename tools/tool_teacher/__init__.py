from ..tool_base import ToolBase
from .filepool import FilePool
import h5py
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from localization import get_locale, format_locale

class ToolTeacher(ToolBase):
    def __init__(self, master):
        super().__init__(master)
        self.bg_pool = FilePool(self, "teacher.pool_bg.title", "*.mat *.hdf")
        self.bg_pool.grid(row=0, column=0, sticky="nsew")
        self.fg_pool = FilePool(self, "teacher.pool_fg.title", "*.mat *.hdf")
        self.fg_pool.grid(row=0, column=1, sticky="nsew")
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.status_display = ScrolledText(self)
        self.status_display.grid(row=0, column=2)
        self.check_passed = False

        teachbtn = tk.Button(self, text=get_locale("teacher.button.start"), command=self.on_teach)
        teachbtn.grid(row=1, column=0, columnspan=2, sticky="nsew")


    def on_teach(self):
        self.check_files()
        if self.check_passed:
            pass

    def println_status(self, message, tabs=0):
        if tabs == 0:
            self.status_display.insert(tk.INSERT, message + "\n")
        else:
            self.status_display.insert(tk.INSERT, "\t"*tabs + message + "\n")

    def check_files(self):
        self.status_display.delete('1.0', tk.END)
        bg_check = self.bg_pool.check_hdf5_fields(["data0", "marked_intervals"])
        fg_check = self.fg_pool.check_hdf5_fields(["EventsIJ"])
        self.println_status(get_locale("teacher.status.msg_bg"))
        self.check_passed = True
        if not self.bg_pool.files_list:
            self.println_status(get_locale("teacher.status.msg_empty"), 1)
            self.check_passed = False
        elif bg_check:
            self.check_passed = False
            for cause in bg_check:
                self.println_status(format_locale("teacher.status.msg_missing", **cause), 1)
        else:
            self.println_status(get_locale("teacher.status.msg_ok"), 1)

        self.println_status(get_locale("teacher.status.msg_fg"))
        if not self.fg_pool.files_list:
            self.println_status(get_locale("teacher.status.msg_empty"), 1)
            self.check_passed = False
        elif fg_check:
            self.check_passed = False
            for cause in fg_check:
                self.println_status(format_locale("teacher.status.msg_missing", **cause), 1)
        else:
            self.println_status(get_locale("teacher.status.msg_ok"), 1)
