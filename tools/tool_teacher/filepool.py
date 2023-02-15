import tkinter as tk

import numpy as np
from tkinter import filedialog

from localization import get_locale
import os.path as ospath
import h5py

import numba as nb

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
        self.src_extension = src_extension
        self.files_listbox = tk.Listbox(self)
        self.files_list = []
        self.open_files_cache = dict()
        self.data_cache = dict()
        self.files_listbox.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        selectbtn = tk.Button(self, text=get_locale("teacher.button.select_sources"), command=self.on_select_sources)
        selectbtn.grid(row=2, column=0, sticky="nsew")
        if allow_clear:
            clearbtn = tk.Button(self, text=get_locale("teacher.button.clear"), command=self.on_clear)
            clearbtn.grid(row=2, column=0, sticky="nsew")

            selectbtn.grid(row=3, column=0, sticky="nsew")
        else:
            selectbtn.grid(row=2, column=0, sticky="nsew")

        self.fast_cache = False

    def on_clear(self):
        self.files_list.clear()
        self.files_listbox.delete(0, tk.END)
        self.clear_cache()


    def on_select_sources(self):
        filenames = self.workspace.askopenfilenames(title=get_locale("teacher.filedialog.title"),
                                                filetypes=[
                                                    (get_locale("teacher.filedialog.source"), self.src_extension)],
                                                parent=self)
        if filenames:
            self.on_clear()
            for f in filenames:
                self.files_listbox.insert(tk.END, ospath.basename(f))
                self.files_list.append(f)


    def get_cached_fileaccess(self, filename):
        if filename in self.open_files_cache.keys():
            return self.open_files_cache[filename]
        else:
            obj = h5py.File(filename, "r")
            self.open_files_cache[filename] = obj
            return obj

    def pull_random_file(self, rng):
        filename = rng.choice(self.files_list)
        obj = self.get_cached_fileaccess(filename)
        return obj

    def pull_fields_from_random_file(self, fields, rng):
        filename = rng.choice(self.files_list)
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
            with h5py.File(file, "r") as testfile:
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

    def random_access(self, rng):
        raise NotImplementedError("Random access is not implemented")

class RandomFileAccess(FilePool):
    def __init__(self, master, title_key, reading_field="EventsIJ", workspace=None, allow_clear=False):
        super().__init__(master, title_key, "*.mat *.hdf *.h5", workspace=workspace, allow_clear=allow_clear)
        self.reading_field = reading_field

    def random_access(self, rng):
        dataset, = self.pull_fields_from_random_file([self.reading_field], rng)
        length = dataset.shape[0]
        if length > 0:
            i = rng.integers(0, length)
            sample = dataset[i]
            signal_present = np.logical_or.reduce(sample,axis=(1,2))
            length = np.count_nonzero(signal_present)
            if length < 128:
                first = find_first_true(signal_present)
                assert first >= 0
                lc_cut = sample[first:first + length]
                new_start = rng.integers(0, 128 - length)
                new_sample = np.zeros(shape=sample.shape)
                new_sample[new_start:new_start + length] = lc_cut
                return new_sample, length
            else:
                return sample, length
        return None


class RandomIntervalAccess(FilePool):
    def __init__(self, master, title_key, workspace=None, allow_clear=False):
        super().__init__(master, title_key, "*.mat *.hdf *.h5", workspace=workspace, allow_clear=allow_clear)

    def random_access(self, rng):
        intervals, data0, broken = self.pull_fields_from_random_file(["marked_intervals", "data0", "broken"], rng)
        weights = intervals[:, 2]
        p = weights/np.sum(weights)
        length = intervals.shape[0]
        i = rng.choice(np.arange(length), p=p)
        sample_interval = intervals[i]
        start = sample_interval[0]
        end = sample_interval[1]
        #print(start, end)
        #sample = data0[int(start):int(end)]
        return data0, (int(start), int(end)), broken
