import tkinter as tk
from tkinter import ttk

'''
In python <=3.6.x implementation of spinbox is omitted. This might help
'''

class Spinbox(ttk.Entry):

    def __init__(self, master=None, **kw):

        ttk.Entry.__init__(self, master, "ttk::spinbox", **kw)
    def set(self, value):
        self.tk.call(self._w, "set", value)