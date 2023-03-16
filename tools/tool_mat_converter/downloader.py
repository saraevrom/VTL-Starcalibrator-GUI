import tkinter as tk
from tkinter import ttk
from vtl_common.common_GUI.modified_base import EntryWithEnterKey
from vtl_common.localization import get_locale, format_locale
from ftplib import FTP, error_perm
import tkinter.messagebox as messagebox
import tkinter.simpledialog as simpledialog
import os.path as ospath
import os
from multiprocessing import Process, Pipe
import h5py
import time
import gc
from vtl_common.workspace_manager import Workspace

UNPROCESSED_DATA_WORKSPACE = Workspace("unprocessed_data")

class FtpBrowser(simpledialog.Dialog):

    def __init__(self, parent, ftp_obj):
        self.ftp_obj = ftp_obj
        super().__init__(parent)


    def listdir(self):
        self.files_listbox.delete(0, tk.END)
        self.files_listbox.insert(tk.END, "..")
        def append_line(line):
            self.files_listbox.insert(tk.END, line.split()[-1])
        self.ftp_obj.retrlines('LIST', append_line)
        self.cwd.set(self.ftp_obj.pwd())
        self.ftp_obj.dir()

    def body(self, master):
        print("BROWSER BUILDING")
        self.files_listbox = tk.Listbox(self)
        self.files_listbox.bind("<Double-1>", self.on_doubleclick)
        self.cwd = tk.StringVar(self)
        self.listdir()
        path_show = tk.Label(self,textvariable=self.cwd)
        path_show.pack(side="top", fill="x")
        self.files_listbox.pack(side="top", fill="both", expand=True)
        self.result_directory = None
        self.result_filelist = None

    def on_doubleclick(self, event):
        cs = self.files_listbox.curselection()
        if cs:
            sel = self.files_listbox.get(cs)
            print(sel)
            try:
                self.ftp_obj.cwd(sel)
            except error_perm:
                pass
            finally:
                self.listdir()

    def apply(self):
        self.result_directory = self.cwd.get()
        self.result_filelist = self.files_listbox.get(1,tk.END)


def verify_mat(file_path: str):
    if not file_path.endswith(".mat"):
        return False
    if not ospath.isfile(file_path):
        return False
    try:
        f = h5py.File(file_path, "r")
        f.close()
        return True
    except OSError:
        return False


class DownloaderWorker(Process):
    def __init__(self, conndata, src_dir, dst_dir, filelist, conn_pipe, *args, **kwargs):
        super().__init__(*args,**kwargs)
        addr,login,passwd = conndata
        self.ftp_addr = addr
        self.ftp_login = login
        self.ftp_passwd = passwd
        self.ftp_src_dir = src_dir
        self.ftp_dst_dir = dst_dir
        self.ftp_filelist = filter(lambda x: x.endswith(".mat"), filelist)
        self.ftp_pipe = conn_pipe

    def run(self):
        self.ftp_pipe.send([True, "", 0])
        ftp = None
        for i, filename in enumerate(self.ftp_filelist):


            ftp_destination = ospath.join(self.ftp_dst_dir, filename)
            self.ftp_pipe.send([True, filename, i])
            if verify_mat(ftp_destination):
                print("Skipped", filename)
            else:
                finished = False
                with open(ftp_destination, "ab") as fp:
                    while not finished:
                        if ftp is None:
                            ftp = FTP(self.ftp_addr, user=self.ftp_login, passwd=self.ftp_passwd, timeout=10)
                            ftp.cwd(self.ftp_src_dir)
                        try:
                            rest = fp.tell()
                            if rest == 0:
                                rest = None
                                print("Starting new transfer", filename)
                            else:
                                print(f"Resuming transfer from {rest} for", filename)

                            ftp.retrbinary(f'RETR {filename}', fp.write, rest=rest)
                            print("Done")
                            finished = True
                        except Exception as e:
                            ftp = None
                            gc.collect()
                            sec = 5
                            print(f"Transfer failed: {e}, will retry in {sec} seconds...")
                            time.sleep(sec)

        self.ftp_pipe.send([False])

class Downloader(tk.Frame):
    def __init__(self,master):
        super().__init__(master, highlightthickness=1)
        self.config(highlightbackground="black", highlightcolor="black")
        self.addr = tk.StringVar(self)
        self.addr.set("ftp.sinp.msu.ru")
        self.login = tk.StringVar(self)
        self.passwd = tk.StringVar(self)
        tk.Label(self, text=get_locale("mat_converter.downloader.title"), font='TkDefaultFont 10 bold') \
            .grid(row=0, column=0, columnspan=2, sticky="nsew")

        self.add_entry("mat_converter.downloader.addr", self.addr, 1)
        self.add_entry("mat_converter.downloader.login", self.login, 2)
        self.add_entry("mat_converter.downloader.password", self.passwd, 3, show="*")
        ok_btn = tk.Button(self, text=get_locale("mat_converter.downloader.button.access"), command=self.on_access)
        ok_btn.grid(row=5, column=0, columnspan=2, sticky="nsew")
        progress_panel = tk.Frame(self)
        self.progressbar = ttk.Progressbar(progress_panel)
        self.current_file = tk.StringVar(self)
        self.progress_display = tk.StringVar(self)
        fileindicator = tk.Label(progress_panel, textvariable=self.current_file)
        fileindicator.grid(row=0, column=0, columnspan=2, sticky="nsew")

        progress_indicator = tk.Label(progress_panel, textvariable=self.progress_display)
        progress_indicator.grid(row=1, column=0, sticky="nsew")
        self.progressbar.grid(row=1, column=1, sticky="nsew")
        progress_panel.grid(row=4, column=0, columnspan=2, sticky="nsew")
        progress_panel.columnconfigure(1, weight=1)
        self.download_pipe = None
        self.downloader_process = None
        self.max_files = 0
        # addr_field = EntryWithEnterKey(self, textvariable=self.addr)
        # login_field = EntryWithEnterKey(self, textvariable=self.login)
        # passwd_field = EntryWithEnterKey(self, show="*", textvariable=self.passwd)

    def add_entry(self, label_key, variable, row, **kwargs):
        entry = EntryWithEnterKey(self, textvariable=variable, **kwargs)
        label_tk = tk.Label(self, text=get_locale(label_key))
        label_tk.grid(row=row, column=0, sticky="nsew")
        entry.grid(row=row, column=1, sticky="nsew")

    def watch_pipe(self):
        if self.download_pipe is None:
            return
        if self.download_pipe.poll():
            data = self.download_pipe.recv()
            if data[0]:
                self.progressbar["value"] = data[2]
                self.current_file.set(data[1])
                self.progress_display.set(f"{data[2]+1}/{self.max_files}")
            else:
                self.progressbar["value"] = 0
                self.downloader_process.join()
                self.downloader_process = None
                self.download_pipe = None
                self.progress_display.set("")
                self.current_file.set("")
        self.after(100, self.watch_pipe)

    def start_watching_pipe(self):
        self.after(20, self.watch_pipe)

    def on_access(self):
        if self.downloader_process is not None:
            return
        print("Accessing", self.addr.get())
        try:
            ftp = FTP(self.addr.get(), user=self.login.get(), passwd=self.passwd.get())
            print(ftp.dir())
            ftp_target = FtpBrowser(self, ftp)
            if ftp_target.result_directory:
                local_target = UNPROCESSED_DATA_WORKSPACE.askdirectory(parent=self, mustexist=True,
                                                       initialdir=".",
                                                       title=get_locale("mat_converter.downloader.fieldialog.title"))
                if local_target:
                    print("REMOTE DIR:", ftp_target.result_directory)
                    print("REMOTE FILES:", ftp_target.result_filelist)
                    print("LOCAL_TGT:", local_target)
                    dirname = ospath.basename(ftp_target.result_directory)
                    destination = ospath.join(local_target, dirname)
                    os.makedirs(destination, exist_ok=True)
                    conndata = self.addr.get(), self.login.get(), self.passwd.get()
                    parent_conn, child_conn = Pipe()
                    self.download_pipe = parent_conn
                    self.downloader_process = DownloaderWorker(conndata,
                                                               ftp_target.result_directory,
                                                               destination,
                                                               ftp_target.result_filelist,
                                                               child_conn)
                    self.downloader_process.start()
                    self.progressbar.configure(maximum=len(ftp_target.result_filelist)-1)
                    self.max_files = len(ftp_target.result_filelist)
                    self.start_watching_pipe()
            ftp.close()
        except error_perm:
            messagebox.showerror(
                parent=self,
                title=get_locale("mat_converter.downloader.messagebox.login_error.title"),
                message=format_locale("mat_converter.downloader.messagebox.login_error.msg",server=self.addr.get())
            )