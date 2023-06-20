import os.path as ospath
import tkinter as tk
from tkinter import filedialog
from tkinter.simpledialog import askinteger

import numpy as np
import numba as nb
#import h5py
from compatibility.h5py_aliased_fields import SafeMatHDF5

from vtl_common.localization import get_locale
from compatibility.AutoFF import fix_minima
from preprocessing.denoising import divide_multidim_3to2


@nb.njit(nb.int64(nb.boolean[:]))
def find_first_true(arr):
    for i in range(len(arr)):
        if arr[i]:
            return i
    return -1

class FilePool(tk.Frame):
    def __init__(self, master, title_key, src_extension, workspace=None, allow_clear = False):
        super().__init__(master)
        if workspace is None:
            self.workspace = filedialog
        else:
            self.workspace = workspace
        label = tk.Label(self, text=get_locale(title_key))
        label.grid(row=0, column=0, sticky="nsew")
        self.capacity_var = tk.StringVar(self)
        cap = tk.Label(self, textvariable=self.capacity_var)
        cap.grid(row=1, column=0, sticky="nsew")
        self.src_extension = src_extension
        self.files_listbox = tk.Listbox(self)
        self.files_listbox.bind("<Button-3>", self.on_rmb)
        self.files_list = []
        self.file_weights = []
        self.open_files_cache = dict()
        self.data_cache = dict()
        self.files_listbox.grid(row=2, column=0, sticky="nsew")
        self.rowconfigure(2, weight=1)
        self.columnconfigure(0, weight=1)
        selectbtn = tk.Button(self, text=get_locale("teacher.button.select_sources"), command=self.on_select_sources)
        #selectbtn.grid(row=3, column=0, sticky="nsew")
        if allow_clear:
            clearbtn = tk.Button(self, text=get_locale("teacher.button.clear"), command=self.on_clear)
            clearbtn.grid(row=3, column=0, sticky="nsew")

            selectbtn.grid(row=4, column=0, sticky="nsew")
        else:
            selectbtn.grid(row=3, column=0, sticky="nsew")

        self.fast_cache = False
        self.sync_capacity()

    def sync_capacity(self):
        self.capacity_var.set(str(self.get_capacity()))

    def get_capacity(self):
        return 0

    def on_clear(self):
        self.files_list.clear()
        self.file_weights = []
        self.files_listbox.delete(0, tk.END)
        self.clear_cache()

    def on_rmb(self, event):
        self.files_listbox.selection_clear(0, tk.END)
        selected_i = self.files_listbox.nearest(event.y)
        self.files_listbox.selection_set(selected_i)
        self.files_listbox.activate(selected_i)
        new_w = askinteger(get_locale("teacher.weight.title"), get_locale("teacher.weight.prompt"))
        if new_w is not None:
            f = self.files_list[selected_i]
            new_txt = f"{ospath.basename(f)} ({new_w})"
            self.file_weights[selected_i] = new_w
            self.set_listbox_entry(selected_i, new_txt)

    def set_listbox_entry(self, i, txt):
        self.files_listbox.delete(i)
        self.files_listbox.insert(i, txt)


    def on_select_sources(self):
        filenames = self.workspace.askopenfilenames(title=get_locale("teacher.filedialog.title"),
                                                filetypes=[
                                                    (get_locale("teacher.filedialog.source"), self.src_extension)],
                                                parent=self)
        if filenames:
            self.on_clear()
            for f in filenames:
                self.files_list.append(f)
                self.file_weights.append(1)
                self.files_listbox.insert(tk.END, f"{ospath.basename(f)} (1)")
            self.file_weights = np.array(self.file_weights)
        self.sync_capacity()


    def get_cached_fileaccess(self, filename):
        if filename in self.open_files_cache.keys():
            return self.open_files_cache[filename]
        else:
            obj = SafeMatHDF5(filename, "r")
            self.open_files_cache[filename] = obj
            return obj

    def get_random_filename(self, rng: np.random.Generator):
        p = self.file_weights/np.sum(self.file_weights)
        return rng.choice(self.files_list, p=p)

    def pull_random_file(self, rng):
        filename = self.get_random_filename(rng)
        obj = self.get_cached_fileaccess(filename)
        return obj

    def pull_fields_from_random_file(self, fields, rng):
        filename = self.get_random_filename(rng)
        if self.fast_cache:
            result = []
            obj = None
            if filename not in self.data_cache.keys():
                self.data_cache[filename] = dict()
            for i in fields:
                cachedict = self.data_cache[filename]
                if i not in cachedict.keys():
                    if obj is None:
                        obj = self.get_cached_fileaccess(filename)
                    print(f"Creating cache for {filename}[{i}]")
                    cachedict[i] = np.array(obj[i])
                    print(f"Created cache for {filename}[{i}]")
                result.append(cachedict[i])
            return result

        else:
            obj = self.get_cached_fileaccess(filename)
            return [obj[i] for i in fields]


    def clear_cache(self):
        for v in self.open_files_cache.values():
            v.close()
        self.open_files_cache.clear()
        self.data_cache.clear()

    def check_hdf5_fields(self,req_fields):
        failed = []
        for file in self.files_list:
            try:
                fix_minima(file)
            except OSError:
                print("Could not check means. Caveat emptor.")
            with SafeMatHDF5(file, "r") as testfile:
                for present_key in req_fields:
                    failkeys = []
                    if present_key not in testfile.keys():
                        failkeys.append(present_key)
                    if failkeys:
                        failed.append({
                            "file":file,
                            "fields":failkeys
                        })
        return failed

    def random_access(self, rng, target_length):
        raise NotImplementedError("Random access is not implemented")

class RandomFileAccess(FilePool):
    def __init__(self, master, title_key, reading_field="EventsIJ", workspace=None, allow_clear=False):
        super().__init__(master, title_key, "*.mat *.hdf *.h5", workspace=workspace, allow_clear=allow_clear)
        self.reading_field = reading_field
        self.shift_threshold = 32

    def set_shift_threshold(self,tgt):
        self.shift_threshold = tgt

    def random_access(self, rng, target_length):
        shift_threshold = self.shift_threshold
        dataset, = self.pull_fields_from_random_file([self.reading_field], rng)
        length = dataset.shape[0]
        if length > 0:
            i = rng.integers(0, length)
            sample = dataset[i]
            needed_zeros = target_length - sample.shape[0]
            if needed_zeros > 0:
                add_shape = list(sample.shape)
                add_shape[0] = needed_zeros
                sample = np.concatenate([sample, np.zeros(shape=add_shape, dtype=float)])
            signal_present = np.logical_or.reduce(sample,axis=(1,2))
            length = np.count_nonzero(signal_present)
            first = find_first_true(signal_present)
            if target_length > length > shift_threshold or first>5:
                lc_cut = sample[first:first + length]
                new_start = rng.integers(0, target_length - length)
                new_sample = np.zeros(shape=sample.shape)
                new_sample[new_start:new_start + length] = lc_cut
                return new_sample, length
            else:
                return sample, length
        return None


class RandomIntervalAccess(FilePool):
    def __init__(self, master, title_key, workspace=None, allow_clear=False):
        super().__init__(master, title_key, "*.mat *.hdf *.h5", workspace=workspace, allow_clear=allow_clear)


    def get_capacity(self):
        capacity = 0
        for file in self.files_list:
            with SafeMatHDF5(file, "r") as fp:
                if "marked_intervals" in fp.keys():
                    for i in range(fp["marked_intervals"].shape[0]):
                        start = fp["marked_intervals"][i, 0]
                        end = fp["marked_intervals"][i, 1]
                        capacity += int(end - start)

        return capacity

    def random_access(self, rng, target_length, **kwargs):
        intervals, data0, broken, means = self.pull_fields_from_random_file(["marked_intervals", "data0",
                                                                             "broken", "means"], rng)
        weights = intervals[:, 2]
        p = weights/np.sum(weights)
        length = intervals.shape[0]
        i = rng.choice(np.arange(length), p=p)
        sample_interval = intervals[i]
        start = sample_interval[0]
        end = sample_interval[1]
        #print(start, end)
        #sample = data0[int(start):int(end)]
        #return  data0,     (int(start), int(end)), broken
        #getting bg_sample, (bg_start, bg_end), broken
        bg_start = int(start)
        bg_end = int(end)

        if np.abs(bg_end - bg_start) < target_length:
            return None
        if bg_start == bg_end - target_length:
            sample_start = bg_start
        else:
            sample_start = rng.integers(bg_start, bg_end - target_length)
        bg = divide_multidim_3to2(data0[sample_start:sample_start + target_length], means/means[3,3])

        return bg, broken
