import tkinter as tk
from tkinter import ttk
import traceback
import sys

from vtl_common.common_GUI.modified_base import EntryWithEnterKey
from vtl_common.localization import get_locale, format_locale
from ftplib import FTP, error_perm
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
import os.path as ospath
import os
from multiprocessing import Process, Pipe
import time
import gc
from vtl_common.workspace_manager import Workspace
from compatibility.h5py_aliased_fields import SafeMatHDF5
from .file_access import RemoteFileAccess

UNPROCESSED_DATA_WORKSPACE = Workspace("unprocessed_data")

class FtpBrowser(simpledialog.Dialog):
    LAST_CONN = None  # preserves connection parameters for consecutive opens
    def __init__(self, parent):
        self.lpanel = None
        self.result_filelist = None
        self.result_directory = None
        self.login = None
        self.password = None
        self.addr = None
        self.ftp_obj = None
        super().__init__(parent)


    def listdir(self):
        self.files_listbox.delete(0, tk.END)
        if self.ftp_obj is not None:
            self.files_listbox.insert(tk.END, "..")
            def append_line(line):
                self.files_listbox.insert(tk.END, line.split()[-1])
            self.ftp_obj.retrlines('LIST', append_line)
            self.cwd.set(self.ftp_obj.pwd())
            self.ftp_obj.dir()

    def connect(self):
        try:
            self.ftp_obj = FTP(host=self.addr.get(),user=self.login.get(),passwd=self.password.get())
            type(self).LAST_CONN = dict(host=self.addr.get(),user=self.login.get(),passwd=self.password.get())
        except Exception:
            print("Exception FTP:")
            print("-" * 60)
            traceback.print_exc(file=sys.stdout)
            print("-" * 60)
            self.ftp_obj = None
        self.listdir()

    def body(self, master):
        print("BROWSER BUILDING")

        self.lpanel = tk.Frame(master)
        self.lpanel.pack(side="left", fill=tk.Y)

        self.login = tk.StringVar()
        self.password = tk.StringVar()
        self.addr = tk.StringVar()

        if type(self).LAST_CONN is not None:
            print("Found last conn")
            self.addr.set(type(self).LAST_CONN["host"])
            self.login.set(type(self).LAST_CONN["user"])
            self.password.set(type(self).LAST_CONN["passwd"])

        self.add_entry("mat_converter.downloader.addr", self.addr, 1)
        self.add_entry("mat_converter.downloader.login", self.login, 2)
        self.add_entry("mat_converter.downloader.password", self.password, 3, show="*")
        ok_btn = tk.Button(self.lpanel, text=get_locale("mat_converter.downloader.button.access"), command=self.connect)
        ok_btn.grid(row=5, column=0, columnspan=2, sticky="nsew")

        rpanel = tk.Frame(master)
        rpanel.pack(side="right",fill="both",expand=True)

        self.files_listbox = tk.Listbox(rpanel, selectmode=tk.EXTENDED)
        self.files_listbox.bind("<Double-1>", self.on_doubleclick)
        self.cwd = tk.StringVar(self)



        self.listdir()
        path_show = tk.Label(rpanel,textvariable=self.cwd)
        path_show.pack(side="top", fill="x")
        self.files_listbox.pack(side="top", fill="both", expand=True)
        self.result_directory = None
        self.result_filelist = None

    def on_doubleclick(self, event):
        if self.ftp_obj is not None:
            cs = self.files_listbox.curselection()
            if cs:
                sel = self.files_listbox.get(cs[0])
                print(sel)
                try:
                    self.ftp_obj.cwd(sel)
                except error_perm:
                    pass
                finally:
                    self.listdir()

    def apply(self):
        if self.ftp_obj is None:
            self.result_filelist = None
        else:
            self.result_directory = self.cwd.get()
            print("PARTIAL SELECT")
            cs = self.files_listbox.curselection()
            self.result_filelist = [RemoteFileAccess(self.addr.get(),
                                                     self.login.get(),
                                                     self.password.get(),
                                                     os.path.join(self.result_directory,self.files_listbox.get(i))
                                                     ) for i in cs]

    def add_entry(self, label_key, variable, row, **kwargs):
        entry = EntryWithEnterKey(self.lpanel, textvariable=variable, **kwargs)
        label_tk = tk.Label(self.lpanel, text=get_locale(label_key))
        label_tk.grid(row=row, column=0, sticky="nsew")
        entry.grid(row=row, column=1, sticky="nsew")