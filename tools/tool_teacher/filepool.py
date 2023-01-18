import tkinter as tk
import tkinter.filedialog as filedialog
from ..tool_base import ToolBase
from localization import get_locale
import os.path as ospath
import random
import h5py

class FilePool(tk.Frame):
    def __init__(self, master, title_key, src_extension):
        super().__init__(master)
        label = tk.Label(self, text=get_locale(title_key))
        label.grid(row=0, column=0, sticky="nsew")
        self.src_extension = src_extension
        self.files_listbox = tk.Listbox(self)
        self.files_list = []
        self.files_listbox.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.columnconfigure(0, weight=1)
        selectbtn = tk.Button(self, text=get_locale("teacher.button.select_sources"), command=self.on_select_sources)
        selectbtn.grid(row=2, column=0, sticky="nsew")

    def on_select_sources(self):
        filenames = filedialog.askopenfilenames(title=get_locale("teacher.filedialog.title"),
                                                filetypes=[
                                                    (get_locale("teacher.filedialog.source"), self.src_extension)],
                                                parent=self)
        if filenames:
            self.files_list.clear()
            self.files_listbox.delete(0, tk.END)
            for f in filenames:
                self.files_listbox.insert(tk.END, ospath.basename(f))
                self.files_list.append(f)

    def pull_random_file(self):
        return random.choice(self.files_list)

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