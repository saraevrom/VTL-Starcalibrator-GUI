import tkinter as tk

try:
    from tkinter.ttk import Spinbox
except ImportError:
    from compatibility.py36xspinbox import Spinbox
    print("Spinbox compat is loaded")

class EntryWithEnterKey(tk.Entry):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.bind("<Return>", self.on_keypress_enter)

    def on_keypress_enter(self, *args):
        self.winfo_toplevel().focus()


class SpinboxWithEnterKey(Spinbox):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.bind("<Return>", self.on_keypress_enter)

    def on_keypress_enter(self, *args):
        self.winfo_toplevel().focus()