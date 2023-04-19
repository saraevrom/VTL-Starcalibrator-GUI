import tkinter as tk
from vtl_common.localization import get_locale
from .storage import IntervalStorage


class Storing(object):
    def __init__(self):
        self.storage = None

    def disconnect_storage(self):
        if self.storage:
            self.storage.on_take = None
            self.storage.on_store = None
        self.storage = None

    def set_storage(self, new_storage):
        self.storage = new_storage
        self.storage.on_store = self.on_change
        self.storage.on_take = self.on_change
        self.on_change()

    def on_change(self):
        pass


class DisplayStorage(tk.Frame, Storing):
    def __init__(self, master, label_key):
        tk.Frame.__init__(self, master)
        Storing.__init__(self)
        label = tk.Label(self,text=get_locale(label_key))
        label.pack(side="top", fill=tk.X)
        self.listbox = tk.Listbox(self)
        self.listbox.pack(side="bottom", fill=tk.BOTH, expand=True)
        self.on_propose_item = None

    def on_change(self):
        if self.storage:
            intervals = self.storage.get_available()
            self.listbox.delete(0,tk.END)
            for item in intervals:
                self.listbox.insert(tk.END, f"{item.start} - {item.end}")

    def clear(self):
        self.storage.clear()
        self.on_change()

    def on_listbox_select(self, event):
        if self.on_propose_item:
            pass
