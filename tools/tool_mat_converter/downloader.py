import tkinter as tk
from common_GUI.modified_base import EntryWithEnterKey
from localization import get_locale
from ftplib import FTP

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
        ok_btn = tk.Button(self, text=get_locale("mat_converter.downloader.button.access"))
        ok_btn.grid(row=4, column=0, columnspan=2, sticky="nsew")
        # addr_field = EntryWithEnterKey(self, textvariable=self.addr)
        # login_field = EntryWithEnterKey(self, textvariable=self.login)
        # passwd_field = EntryWithEnterKey(self, show="*", textvariable=self.passwd)

    def add_entry(self, label_key, variable, row, **kwargs):
        entry = EntryWithEnterKey(self, textvariable=variable, **kwargs)
        label_tk = tk.Label(self, text=get_locale(label_key))
        label_tk.grid(row=row, column=0, sticky="nsew")
        entry.grid(row=row, column=1, sticky="nsew")

    def on_access(self):
        ftp = FTP(self.addr.get(), user=self.login.get(), passwd=self.passwd.get())
