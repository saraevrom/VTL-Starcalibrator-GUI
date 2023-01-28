from ..tool_base import ToolBase
from .filepool import RandomIntervalAccess, RandomFileAccess, FilePool
import h5py
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from localization import get_locale, format_locale
from trigger_ai import compile_model
import gc
import numpy.random as rng
import numpy as np
from common_GUI import SettingMenu
from .create_settings import build_menu
import tkinter.filedialog as filedialog
from tensorflow import keras

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
        self.status_display = ScrolledText(self,height=16)
        self.status_display.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.check_passed = False
        self.workon_model = None

        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=3, sticky="nsew")
        control_frame.rowconfigure(0, weight=1)

        self.settings_menu = SettingMenu(control_frame)
        self.settings_menu.commit_action = self.on_teach
        self.settings_menu.grid(row=0, column=0, sticky="nsew")
        build_menu(self.settings_menu)

        resetbtn = tk.Button(control_frame, text=get_locale("teacher.button.reset"), command=self.on_reset_model)
        resetbtn.grid(row=1, column=0, sticky="ew")

        savebtn = tk.Button(control_frame, text=get_locale("teacher.button.save"), command=self.on_save_model)
        savebtn.grid(row=2, column=0, sticky="ew")

        loadbtn = tk.Button(control_frame, text=get_locale("teacher.button.load"), command=self.on_load_model)
        loadbtn.grid(row=3, column=0, sticky="ew")

        teachbtn = tk.Button(control_frame, text=get_locale("teacher.button.start"), command=self.on_teach)
        teachbtn.grid(row=4, column=0, sticky="ew")


    def try_reset_model(self):
        new_model = compile_model(128, self)
        if new_model:
            self.workon_model = new_model

    def ensure_model(self):
        if self.workon_model is None:
            self.try_reset_model()
            return bool(self.workon_model)
        return False


    def on_save_model(self):
        if self.workon_model:
            filename = filedialog.asksaveasfilename(
                title=get_locale("app.filedialog.save_model.title"),
                filetypes=[(get_locale("app.filedialog_formats.model"), "*.h5")]
            )
            if filename:
                self.workon_model.save(filename)

    def on_load_model(self):
        filename = filedialog.askopenfilename(
            title=get_locale("app.filedialog.load_model.title"),
            filetypes=[(get_locale("app.filedialog_formats.model"), "*.h5")]
        )
        if filename:
            self.workon_model = keras.models.load_model(filename)

    def on_reset_model(self):
        self.try_reset_model()

    def on_teach(self):
        if self.ensure_model():
            self.check_files()
            if self.check_passed:
                gc.collect()
                generator = self.data_generator()
            #self.workon_model.com
            #self.workon_model.fit(generator)
        else:
            self.println_status(get_locale("teacher.status.msg_missing_model"))
        self.fg_pool.clear_cache()
        self.bg_pool.clear_cache()
        self.interference_pool.clear_cache()

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


    def data_generator(self, frame_size=128, amount=None):
        i = 0
        cycle_forever = amount is None
        while cycle_forever or i < amount:
            bg_start, (bg_start, bg_end) = self.bg_pool.random_access()
            if bg_end-bg_start < frame_size:
                continue
            sample_start = rng.randint(bg_start, bg_end-frame_size)
            bg = bg_start[sample_start:sample_start+frame_size]
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
            i += 1
            yield x_data, y_data

    def check_files(self):
        self.status_display.delete('1.0', tk.END)
        self.check_passed = True
        self.check_pool("teacher.status.msg_bg", self.bg_pool, ["data0", "marked_intervals"])
        self.check_pool("teacher.status.msg_fg", self.fg_pool, ["EventsIJ"])
        self.check_pool("teacher.status.msg_it", self.interference_pool, ["EventsIJ"], True)

