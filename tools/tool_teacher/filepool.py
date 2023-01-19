import tkinter as tk
import tkinter.filedialog as filedialog

import numpy as np

from ..tool_base import ToolBase
from localization import get_locale
import os.path as ospath
import numpy.random as random
import h5py

class FilePool(tk.Frame):
    def __init__(self, master, title_key, src_extension, allow_clear = False):
        super().__init__(master)
        label = tk.Label(self, text=get_locale(title_key))
        label.grid(row=0, column=0, sticky="nsew")
        self.src_extension = src_extension
        self.files_listbox = tk.Listbox(self)
        self.files_list = []
        self.open_files_cache = dict()
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

    def on_clear(self):
        self.files_list.clear()
        self.files_listbox.delete(0, tk.END)
        for v in self.open_files_cache.values():
            v.close()
        self.open_files_cache.clear()


    def on_select_sources(self):
        filenames = filedialog.askopenfilenames(title=get_locale("teacher.filedialog.title"),
                                                filetypes=[
                                                    (get_locale("teacher.filedialog.source"), self.src_extension)],
                                                parent=self)
        if filenames:
            self.on_clear()
            for f in filenames:
                self.files_listbox.insert(tk.END, ospath.basename(f))
                self.files_list.append(f)

    def pull_random_file(self):
        filename = random.choice(self.files_list)
        if filename in self.open_files_cache.keys():
            return self.open_files_cache[filename]
        else:
            obj = h5py.File(filename, "r")
            self.open_files_cache[filename] = obj
            return obj

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

    def random_access(self):
        raise NotImplementedError("Random access is not implemented")

class RandomFileAccess(FilePool):
    def __init__(self, master, title_key, reading_field="EventsIJ", allow_clear=False):
        super().__init__(master, title_key, "*.mat *.hdf *.h5", allow_clear=allow_clear)
        self.reading_field = reading_field

    def random_access(self):
        f = self.pull_random_file()
        dataset = f[self.reading_field]
        length = dataset.shape[0]
        i = random.randint(0, length)
        sample = dataset[i]
        return sample

class RandomIntervalAccess(FilePool):
    def __init__(self, master, title_key, allow_clear=False):
        super().__init__(master, title_key, "*.mat *.hdf *.h5", allow_clear=allow_clear)

    def random_access(self):
        f = self.pull_random_file()
        intervals = np.array(f["marked_intervals"])
        data0 = f["data0"]
        weights = intervals[:, 2]
        p = weights/np.sum(weights)
        length = intervals.shape[0]
        i = random.choice(np.arange(length), p=p)
        sample_interval = intervals[i]
        start = sample_interval[0]
        end = sample_interval[1]
        print(start,end)
        sample = data0[int(start):int(end)]
        return sample