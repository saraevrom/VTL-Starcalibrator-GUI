#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedialog
import h5py
from tools import add_tools
from tools.tool_flatfielder import FlatFieldingModel

from localization import get_locale, format_locale
from tools.tool_starcalibrator import StarCalibrator
import warnings
import os.path as ospath

class Tool(object):
    def __init__(self,master,tool_class):
        self.master = master
        self.tool_class = tool_class

    def __call__(self):
        return self.tool_class(self.master)

class App(tk.Tk):

    def __init__(self):
        super(App, self).__init__()

        self.topmenu = tk.Menu(self)

        self.filemenu = tk.Menu(self.topmenu, tearoff=0)
        self.filemenu.add_command(label=get_locale("app.menu.file.open_mat"), command=self.on_open_mat_file)
        self.filemenu.add_command(label=get_locale("app.filedialog.load_ff_settings.title"),
                                  command=self.on_open_ffmodel)
        #self.filemenu.add_command(label=get_locale("app.menu.file.load_settings"), command=self.on_settings_load)
        #self.filemenu.add_command(label=get_locale("app.menu.file.save_settings"), command=self.on_settings_save)

        #self.toolsmenu = tk.Menu(self.topmenu, tearoff=0)
        self.topmenu.add_cascade(label=get_locale("app.menu.file"), menu=self.filemenu)
        #self.topmenu.add_cascade(label=get_locale("app.menu.tools"), menu=self.toolsmenu)
        self.config(menu=self.topmenu)
        self.file = None
        self.filename = ""
        self.ffmodel = None
        self.tool_list = []
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(side="top",fill="both",expand=True)
        self.bind("<1>", self.set_focus)
        add_tools(self.add_tool)
        self.update_title()


    def update_title(self):
        title = get_locale("app.title")
        warnings = []
        if self.file:
            warnings.append(format_locale("app.loaded_file",self.filename))
        if not self.ffmodel:
            warnings.append(get_locale("app.ff_warning"))
        if warnings:
            self.title(f"{title} ({', '.join(warnings)})")

    def add_tool(self, label_key, toolclass):
        tool_frame = toolclass(self.main_notebook)
        tool_frame.pack(fill="both",expand=True)
        self.main_notebook.add(tool_frame,text=get_locale(label_key))
        self.tool_list.append(tool_frame)
        #tool_inst = Tool(self, toolclass)
        #self.toolsmenu.add_command(label=get_locale(label_key), command=tool_inst)

    def on_open_mat_file(self):
        filename = filedialog.askopenfilename(title=get_locale("app.filedialog.load_mat.title"),
                                              filetypes=[
                                                  (get_locale("app.filedialog_formats.processed_mat"), "*.mat *.hdf")
                                              ])
        if filename and os.path.isfile(filename):
            new_file = h5py.File(filename, "r")
            if self.file:
                self.file.close()
            self.filename = filename
            self.file = new_file
            for tool in self.tool_list:
                tool.propagate_mat_file(self.file)
        self.update_title()

    def close_mat_file(self):
        if self.file:
            self.file.close()
            self.file = None
            self.filename = ""
        self.update_title()

    def on_open_ffmodel(self):
        filename = filedialog.askopenfilename(title=get_locale("app.filedialog.load_ff_settings.title"),
                                              filetypes=[
                                                  (get_locale("app.filedialog_formats.ff_json"), "*.json")
                                              ])
        if filename:
            model: FlatFieldingModel
            model = FlatFieldingModel.load(filename)
            self.ffmodel = model
            for tool in self.tool_list:
                tool.on_ff_reload()
        self.update_title()

    def reload_ffmodel(self):
        warnings.warn("Flat fielding coefficients are now loaded manually")

    def get_ffmodel(self):
        return self.ffmodel

    def get_loaded_filename(self):
        if self.file:
            base = ospath.basename(self.filename)
            return base
        else:
            return ""

    def set_focus(self, event=None):
        x, y = self.winfo_pointerxy()
        self.focus()
        focus_target = self.winfo_containing(x, y)
        if focus_target:
            focus_target.focus()



if __name__ == "__main__":
    root = App()
    root.mainloop()
