import matplotlib.pyplot as plt
import tqdm

from ..tool_base import ToolBase
from .filepool import RandomIntervalAccess, RandomFileAccess, FilePool
import h5py
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from localization import get_locale, format_locale
from trigger_ai import compile_model, create_model
import gc
import numpy.random as rng
import numpy as np
from common_GUI import SettingMenu
import tkinter.filedialog as filedialog
from tensorflow import keras
from common_GUI import TkDictForm
from .advanced_form import SettingForm
from multiprocessing import Process, Pipe
from tensorflow.data import Dataset
import tensorflow as tf
from trigger_ai.models.model_wrapper import ModelWrapper, TargetParameters

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
        self.status_display = ScrolledText(self, height=16)
        self.status_display.grid(row=1, column=0, columnspan=4, sticky="nsew")
        self.status_display.config(state=tk.DISABLED)
        self.check_passed = False
        self.workon_model = None

        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=3, sticky="nsew")
        control_frame.rowconfigure(0, weight=1)

        self.settings_form = SettingForm()
        form_conf = self.settings_form.get_configuration_root()

        self.settings_menu = TkDictForm(control_frame, form_conf, True)
        self.settings_menu.commit_action = self.on_teach
        self.settings_menu.grid(row=0, column=0, sticky="nsew")

        probe_btn = tk.Button(control_frame, text=get_locale("teacher.button.probe"), command=self.on_probe)
        probe_btn.grid(row=1, column=0, sticky="ew")

        resetbtn = tk.Button(control_frame, text=get_locale("teacher.button.reset"), command=self.on_reset_model)
        resetbtn.grid(row=2, column=0, sticky="ew")

        recompbtn = tk.Button(control_frame, text=get_locale("teacher.button.recompile"), command=self.on_recompile_model)
        recompbtn.grid(row=3, column=0, sticky="ew")

        savebtn = tk.Button(control_frame, text=get_locale("teacher.button.save"), command=self.on_save_model)
        savebtn.grid(row=4, column=0, sticky="ew")

        loadbtn = tk.Button(control_frame, text=get_locale("teacher.button.load"), command=self.on_load_model)
        loadbtn.grid(row=5, column=0, sticky="ew")


        teachbtn = tk.Button(control_frame, text=get_locale("teacher.button.start"), command=self.on_teach)
        teachbtn.grid(row=6, column=0, sticky="ew")


    def try_reset_model(self):
        new_model = create_model(self)
        if new_model:
            self.workon_model = new_model

    def try_recompile_model(self):
        if self.workon_model:
            compile_model(self.workon_model.model, self)

    def ensure_model(self):
        if self.workon_model is None:
            self.try_reset_model()
            if not self.workon_model:
                self.println_status(get_locale("teacher.status.msg_model_missing"))
                return False

        self.println_status(get_locale("teacher.status.msg_model_ok"))
        if self.workon_model.model._is_compiled:
            self.println_status(get_locale("teacher.status.msg_model_compiled"))
            return True
        else:
            self.try_recompile_model()
            if self.workon_model.model._is_compiled:
                self.println_status(get_locale("teacher.status.msg_model_compiled"))
            else:
                self.println_status(get_locale("teacher.status.msg_model_nocompile"))
            return self.workon_model.model._is_compiled


    def on_save_model(self):
        if self.workon_model:
            filename = filedialog.asksaveasfilename(
                title=get_locale("app.filedialog.save_model.title"),
                filetypes=[(get_locale("app.filedialog_formats.model"), "*.h5")]
            )
            if filename:
                self.workon_model.save_model(filename)

    def on_load_model(self):
        filename = filedialog.askopenfilename(
            title=get_locale("app.filedialog.load_model.title"),
            filetypes=[(get_locale("app.filedialog_formats.model"), "*.h5")]
        )
        if filename:
            self.workon_model = ModelWrapper.load_model(filename)
            self.workon_model.model.summary()

    def on_reset_model(self):
        self.try_reset_model()

    def on_recompile_model(self):
        self.try_recompile_model()

    def on_teach(self):
        self.fg_pool.clear_cache()
        self.bg_pool.clear_cache()
        self.interference_pool.clear_cache()
        self.clear_status()
        if self.ensure_model():
            self.check_files()
            if self.check_passed:
                self.close_mat_file()
                conf = self.settings_menu.get_values()
                self.fg_pool.fast_cache = conf["fastcache"]
                self.bg_pool.fast_cache = conf["fastcache"]
                self.interference_pool.fast_cache = conf["fastcache"]
                self.settings_form.parse_formdata(conf)
                conf = self.settings_form.get_data()
                gc.collect()

                if conf.config["pregenerate"] is not None:
                    N = conf.config["pregenerate"]
                    trainX = np.zeros((N, 128, 16, 16))
                    trainY = np.zeros((N, 2))
                    gen = self.data_generator(conf)
                    for i in tqdm.tqdm(range(N)):
                        x,y_par = next(gen)
                        trainX[i] = x
                        trainY[i] = self.workon_model.create_dataset_ydata_for_item(y_par)
                    self.workon_model.model.fit(trainX, trainY, **conf.get_fit_parameters_finite())
                else:
                    dataset = Dataset.from_generator(
                        lambda: self.batch_generator(conf),
                        output_signature=(tf.TensorSpec(shape=(None, 128, 16, 16), dtype=tf.double),
                                          tf.TensorSpec(shape=(None, 2), dtype=tf.double))
                    )
                    self.workon_model.model.fit(dataset, **conf.get_fit_parameters())
        self.fg_pool.clear_cache()
        self.bg_pool.clear_cache()
        self.interference_pool.clear_cache()


    def on_probe(self):
        self.clear_status()
        self.println_status(get_locale("teacher.status.msg_model_ok"))
        self.check_files()
        if self.check_passed:
            self.close_mat_file()
            conf = self.settings_menu.get_values()
            self.fg_pool.fast_cache = conf["fastcache"]
            self.bg_pool.fast_cache = conf["fastcache"]
            self.interference_pool.fast_cache = conf["fastcache"]
            self.settings_form.parse_formdata(conf)
            conf = self.settings_form.get_data()
            gc.collect()
            gen = self.data_generator(conf)
            x, y_par = next(gen)
            fig, ax = plt.subplots()
            display_data = np.max(x, axis=0)
            ax.matshow(display_data.T)
            if y_par.has_track():
                ax.set_title(get_locale("teacher.sampleplot.title_true"))
            else:
                ax.set_title(get_locale("teacher.sampleplot.title_false"))
            fig.show()


    def println_status(self, message, tabs=0):
        self.status_display.config(state=tk.NORMAL)
        if tabs == 0:
            self.status_display.insert(tk.INSERT, message + "\n")
        else:
            self.status_display.insert(tk.INSERT, "\t"*tabs + message + "\n")
        self.status_display.config(state=tk.DISABLED)

    def clear_status(self):
        self.status_display.config(state=tk.NORMAL)
        self.status_display.delete('1.0', tk.END)
        self.status_display.config(state=tk.DISABLED)

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


    def data_generator(self, conf, frame_size=128, amount=None):
        i = 0
        cycle_forever = amount is None
        preprocessor = conf.get_preprocessor()
        while cycle_forever or i < amount:
            bg_sample, (bg_start, bg_end), broken = self.bg_pool.random_access()
            if np.abs(bg_end-bg_start) < frame_size:
                continue
            if bg_start==bg_end-frame_size:
                sample_start = bg_start
            else:
                sample_start = rng.randint(bg_start, bg_end-frame_size)
            bg = bg_sample[sample_start:sample_start+frame_size]
            x_data = preprocessor.three_stage_preprocess(bg)
            y_params = TargetParameters(False, False, False, False)
            if self.interference_pool.files_list:
                if rng.random() < 0.5:
                    interference = self.interference_pool.random_access()
                    interference = conf.process_it(interference)
                    x_data = x_data+interference
            if rng.random() < 0.5:
                pass
            else:
                fg = np.zeros(bg.shape)
                #conf.process_fg(self.fg_pool.random_access)
                rng_append = rng.randint(1,16)
                if rng_append % 2 == 1:
                    y_params.pmt_bottom_left = True
                    fg[:, :8, :8] = conf.process_fg(self.fg_pool.random_access())
                if rng_append // 2 % 2 == 1:
                    y_params.pmt_bottom_right = True
                    fg[:, 8:, :8] = conf.process_fg(self.fg_pool.random_access())
                if rng_append // 4 % 2 == 1:
                    y_params.pmt_top_left = True
                    fg[:, :8, 8:] = conf.process_fg(self.fg_pool.random_access())
                if rng_append // 8 % 2 == 1:
                    y_params.pmt_top_right = True
                    fg[:, 8:, 8:] = conf.process_fg(self.fg_pool.random_access())
                x_data = x_data + fg
            i += 1
            x_data[:, broken] = 0
            #y_data = self.workon_model.create_dataset_ydata_for_item(y_params)
            yield x_data, y_params

    def batch_generator(self, conf, frame_size=128):
        generator = self.data_generator(conf, frame_size)
        batchX = []
        batchY = []
        gen_params = conf.generator_params()
        batch_size = gen_params["batch_size"]
        while True:
            batchX.clear()
            batchY.clear()
            for _ in range(batch_size):
                X, Y_par = next(generator)
                batchX.append(X)
                batchY.append(self.workon_model.create_dataset_ydata_for_item(Y_par))
            yield np.array(batchX), np.array(batchY)


    def check_files(self):
        self.check_passed = True
        self.check_pool("teacher.status.msg_bg", self.bg_pool, ["data0", "marked_intervals", "broken"])
        self.check_pool("teacher.status.msg_fg", self.fg_pool, ["EventsIJ"])
        self.check_pool("teacher.status.msg_it", self.interference_pool, ["EventsIJ"], True)

