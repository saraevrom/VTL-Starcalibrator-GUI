import tkinter as tk

try:
    from tkinter.ttk import Spinbox
except ImportError:
    from compatibility.py36xspinbox import Spinbox
    print("Spinbox compat is loaded")

from tkinter import messagebox
from tkinter.simpledialog import Dialog

class EntryWithEnterKey(tk.Entry):
    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<Return>", self.on_keypress_enter)
        self.on_commit = None

    def on_keypress_enter(self, *args):
        self.winfo_toplevel().focus()
        if self.on_commit:
            self.on_commit()


class SpinboxWithEnterKey(Spinbox):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.bind("<Return>", self.on_keypress_enter)

    def on_keypress_enter(self, *args):
        self.winfo_toplevel().focus()

