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
import numpy.random as numpy_rng
import numpy as np
from common_GUI import SettingMenu
from workspace_manager import Workspace
from tensorflow import keras
from localized_GUI import SaveableTkDictForm
from .advanced_form import SettingForm
from .plotting import plot_roc
from multiprocessing import Process, Pipe
from tensorflow.data import Dataset
from tensorflow.keras.utils import plot_model
import tensorflow as tf
from trigger_ai.models.model_wrapper import ModelWrapper, TargetParameters
from extension.optional_pydot import PYDOT_INSTALLED
import numba as nb
from common_GUI.button_panel import ButtonPanel
from tkinter.simpledialog import askinteger


TENSORFLOW_MODELS_WORKSPACE = Workspace("ann_models")
MDATA_WORKSPACE = Workspace("merged_data")
MODELED_TRACK_WORKSPACE = Workspace("modelled_tracks")
EVENTS_PRESET_WORKSPACE = Workspace("ann_event_presets")

@nb.njit(nb.float64[:, :, :](nb.float64[:], nb.float64[:, :]))
def signal_multiply(profile, mask):
    T = profile.shape[0]
    W, H = mask.shape
    result = np.zeros((T, W, H))
    for k in range(T):
        for i in range(W):
            for j in range(H):
                result[k, i, j] = profile[k] * mask[i, j]
    return result


@nb.njit(nb.int64(nb.boolean[:]))
def find_first_true(arr):
    for i in range(len(arr)):
        if arr[i]:
            return i
    return -1


def ask_test():
    return askinteger(title=get_locale("teacher.dialog.test.title"),
                      prompt=get_locale("teacher.dialog.test.prompt"))




class ToolTeacher(ToolBase):
    def __init__(self, master):
        super().__init__(master)
        self.bg_pool = RandomIntervalAccess(self, "teacher.pool_bg.title", workspace=MDATA_WORKSPACE)
        self.bg_pool.grid(row=0, column=0, sticky="nsew")
        self.fg_pool = RandomFileAccess(self, "teacher.pool_fg.title", workspace=MODELED_TRACK_WORKSPACE)
        self.fg_pool.grid(row=0, column=1, sticky="nsew")
        self.interference_pool = RandomFileAccess(self, "teacher.pool_interference.title",
                                                  workspace=MODELED_TRACK_WORKSPACE, allow_clear=True)
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
        self.rng = None

        control_frame = tk.Frame(self)
        control_frame.grid(row=0, column=3, sticky="nsew")
        control_frame.rowconfigure(0, weight=1)

        self.settings_form = SettingForm()
        form_conf = self.settings_form.get_configuration_root()

        self.settings_menu = SaveableTkDictForm(control_frame, form_conf, True, file_asker=EVENTS_PRESET_WORKSPACE)
        self.settings_menu.commit_action = self.on_teach
        self.settings_menu.grid(row=0, column=0, sticky="nsew")

        button_panel = ButtonPanel(control_frame)
        button_panel.grid(row=1, column=0, sticky="nsew")
        button_panel.add_button(text=get_locale("teacher.button.probe_track"),
                                command=lambda: self.on_probe(True), row=0)
        button_panel.add_button(text=get_locale("teacher.button.probe_trackless"),
                                command=lambda: self.on_probe(False), row=0)
        button_panel.add_button(text=get_locale("teacher.button.probe_test"), command=self.on_test, row=0)
        button_panel.add_button(text=get_locale("teacher.button.probe_roc"), command=self.on_plot_roc, row=0)

        button_panel.add_button(text=get_locale("teacher.button.reset"), command=self.on_reset_model, row=1)
        button_panel.add_button(text=get_locale("teacher.button.recompile"), command=self.on_recompile_model, row=1)
        button_panel.add_button(text=get_locale("teacher.button.save"), command=self.on_save_model, row=2)
        button_panel.add_button(text=get_locale("teacher.button.load"), command=self.on_load_model, row=2)
        button_panel.add_button(text=get_locale("teacher.button.reset_seed"), command=self.reset_generator, row=3)
        button_panel.add_button(text=get_locale("teacher.button.start"), command=self.on_teach, row=3)


        self.reset_generator()


    def reset_generator(self):
        conf = self.settings_menu.get_values()
        self.settings_form.parse_formdata(conf)
        conf = self.settings_form.get_data()
        self.rng = numpy_rng.Generator(numpy_rng.MT19937(seed=conf.seed))

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
            file_types = [(get_locale("app.filedialog_formats.model"), "*.h5")]
            if PYDOT_INSTALLED:
                file_types.append((get_locale("app.filedialog_formats.png"), "*.png"))
            filename = TENSORFLOW_MODELS_WORKSPACE.asksaveasfilename(
                title=get_locale("app.filedialog.save_model.title"),
                filetypes=file_types
            )
            if filename:
                if filename.endswith(".png") and PYDOT_INSTALLED:
                    plot_model(self.workon_model.model, to_file=filename,
                               show_shapes=True,
                               show_dtype=True,
                               show_layer_activations=True,
                              )
                else:
                    self.workon_model.save_model(filename)

    def on_load_model(self):
        filename = TENSORFLOW_MODELS_WORKSPACE.askopenfilename(
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
                preferred_filter = conf["preprocessing"]
                self.workon_model.set_preferred_filter_data(preferred_filter)
                conf = self.settings_form.get_data()
                gc.collect()

                if conf.pregenerate is not None:
                    N = conf.pregenerate
                    trainX = np.zeros((N, 128, 16, 16))
                    trainY = np.zeros(self.workon_model.get_y_signature(N))
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
                                          self.workon_model.get_y_spec())
                    )
                    self.workon_model.model.fit(dataset, **conf.get_fit_parameters())
        self.fg_pool.clear_cache()
        self.bg_pool.clear_cache()
        self.interference_pool.clear_cache()


    def generate_test(self):
        self.clear_status()
        self.check_files()
        if self.check_passed and self.ensure_model():
            self.close_mat_file()
            conf = self.settings_menu.get_values()
            self.fg_pool.fast_cache = conf["fastcache"]
            self.bg_pool.fast_cache = conf["fastcache"]
            self.settings_form.parse_formdata(conf)
            conf = self.settings_form.get_data()
            generator = self.data_generator(conf)
            batch_size = ask_test()
            return self.generate_batch(generator, batch_size)

    def on_test(self):
        testd = self.generate_test()
        if testd is not None:
            x_test, y_test = testd
            self.workon_model.model.evaluate(x_test, y_test)

            self.fg_pool.clear_cache()
            self.bg_pool.clear_cache()
            self.interference_pool.clear_cache()


    def on_plot_roc(self):
        testd = self.generate_test()
        if testd is not None:
            x_test, y_test = testd
            y_pred = self.workon_model.model.predict(x_test)
            plot_roc(y_pred, y_test, 101)

            self.fg_pool.clear_cache()
            self.bg_pool.clear_cache()
            self.interference_pool.clear_cache()

    def on_probe(self, needstrack):
        self.clear_status()
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
            x_gen, y_par = next(gen)
            while y_par.has_track() != needstrack:
                x_gen, y_par = next(gen)
            print("GENERATE_SUCCESS:", (x_gen!=0).any())
            fig, ax = plt.subplots()
            # display_data = np.max(x_gen, axis=0)
            # ax.matshow(display_data.T)
            plot_xs = np.arange(x_gen.shape[0])
            for i in range(16):
                for j in range(16):
                    ax.plot(plot_xs, x_gen[:, i, j])
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


    def generate_artificial_flash(self, conf):
        # There is another type of interference: flashes.
        # It can also confuse ANN. We can craft it from light curve of foreground signal
        searching = True
        lightcurve = None
        attempts = 10000
        min_length = None
        while searching:
            source_foreground, length = self.fg_pool.random_access(self.rng)
            lightcurve = np.sum(source_foreground, axis=(1, 2))
            if (min_length is None) or length < min_length:
                min_length = length
            attempts -= 1
            if attempts == 0:
                raise RuntimeError(f"Could not generate artificial flash. Minimal encountered length of track is {min_length}")
            searching = length > conf.flash_maxsize

        flash_mask = self.rng.random((16, 16)) * 2 - 1
        flash_interference = signal_multiply(lightcurve, flash_mask)
        return conf.process_it(flash_interference, rng=self.rng)

    def get_interference(self, conf, use_artificial):
        if use_artificial:
            source_foreground, e_length = self.fg_pool.random_access(self.rng)
            # We can create artificial "meteor" interference signal from foreground signal
            flattened = np.sum(source_foreground, axis=0)
            interference = np.zeros(source_foreground.shape)
            interference[self.rng.integers(source_foreground.shape[0])] = flattened
            return conf.process_it(interference/np.max(interference)*np.max(source_foreground), rng=self.rng)
        else:
            return conf.process_it(self.interference_pool.random_access(self.rng)[0], rng=self.rng)

    def data_generator(self, conf, frame_size=128, amount=None):
        i = 0
        cycle_forever = amount is None
        preprocessor = conf.get_preprocessor()
        while cycle_forever or i < amount:
            bg_sample, (bg_start, bg_end), broken = self.bg_pool.random_access(self.rng)
            if np.abs(bg_end-bg_start) < frame_size:
                continue
            if bg_start==bg_end-frame_size:
                sample_start = bg_start
            else:
                sample_start = self.rng.integers(bg_start, bg_end-frame_size)
            bg = bg_sample[sample_start:sample_start+frame_size]
            broken = np.array(broken)
            x_data = preprocessor.preprocess(bg, broken)
            y_params = TargetParameters()
            artificial_interference = conf.intergerence_artificial()
            if artificial_interference or self.interference_pool.files_list:
                interf = np.zeros(bg.shape)
                for _ in range(conf.quick_track_attempts):
                    if self.rng.random() < conf.quick_track_probability:
                        y_params.interference_bottom_left = True
                        interf[:, :8, :8] = interf[:, :8, :8] + self.get_interference(conf, artificial_interference)
                    if self.rng.random() < conf.quick_track_probability:
                        y_params.interference_bottom_right = True
                        interf[:, 8:, :8] = interf[:, 8:, :8] + self.get_interference(conf, artificial_interference)
                    if self.rng.random() < conf.quick_track_probability:
                        y_params.interference_top_left = True
                        interf[:, :8, 8:] = interf[:, :8, 8:] + self.get_interference(conf, artificial_interference)
                    if self.rng.random() < conf.quick_track_probability:
                        y_params.interference_top_right = True
                        interf[:, 8:, 8:] = interf[:, 8:, 8:] + self.get_interference(conf, artificial_interference)

                if artificial_interference and self.rng.random() < conf.flash_probability:
                    interf = interf + self.generate_artificial_flash(conf)
                x_data = x_data + interf
            if self.rng.random() >= conf.track_probability:
                pass
            else:
                fg = np.zeros(bg.shape)
                rng_append = self.rng.integers(1, 16)
                if rng_append % 2 == 1:
                    y_params.pmt_bottom_left = True
                    fg[:, :8, :8] = conf.process_fg(self.fg_pool.random_access(self.rng)[0], rng=self.rng)
                if rng_append // 2 % 2 == 1:
                    y_params.pmt_bottom_right = True
                    fg[:, 8:, :8] = conf.process_fg(self.fg_pool.random_access(self.rng)[0], rng=self.rng)
                if rng_append // 4 % 2 == 1:
                    y_params.pmt_top_left = True
                    fg[:, :8, 8:] = conf.process_fg(self.fg_pool.random_access(self.rng)[0], rng=self.rng)
                if rng_append // 8 % 2 == 1:
                    y_params.pmt_top_right = True
                    fg[:, 8:, 8:] = conf.process_fg(self.fg_pool.random_access(self.rng)[0], rng=self.rng)
                fg[:, broken] = 0
                x_data = x_data + fg
            i += 1
            # obfuscating neural network,
            # so it won't use changing noise for track detection
            x_data = conf.process_bg(x_data, y_params, rng=self.rng)
            yield x_data, y_params

    def batch_generator(self, conf, frame_size=128):
        generator = self.data_generator(conf, frame_size)
        # batchX = []
        # batchY = []
        gen_params = conf.generator_params()
        batch_size = gen_params["batch_size"]

        while True:
            yield self.generate_batch(generator,batch_size)
            # batchX.clear()
            # batchY.clear()
            # for _ in range(batch_size):
            #     X, Y_par = next(generator)
            #     batchX.append(X)
            #     batchY.append(self.workon_model.create_dataset_ydata_for_item(Y_par))
            # yield np.array(batchX), np.array(batchY)


    def generate_batch(self, generator, size):
        x_data = []
        y_data = []
        for _ in range(size):
            X, Y_par = next(generator)
            x_data.append(X)
            y_data.append(self.workon_model.create_dataset_ydata_for_item(Y_par))
        return np.array(x_data), np.array(y_data)


    def check_files(self):
        self.check_passed = True
        self.check_pool("teacher.status.msg_bg", self.bg_pool, ["data0", "marked_intervals", "broken"])
        self.check_pool("teacher.status.msg_fg", self.fg_pool, ["EventsIJ"])
        self.check_pool("teacher.status.msg_it", self.interference_pool, ["EventsIJ"], True)

