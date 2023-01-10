#!/usr/bin/env python3
import os
import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedialog
import h5py
from tool_mat_converter import MatConverter
from tool_flatfielder import FlatFielder, FlatFieldingModel
from tool_mat_player import MatPlayer
from tool_track_markup import TrackMarkup

from localization import get_locale
from tool_starcalibrator import StarCalibrator

class Tool(object):
    def __init__(self,master,tool_class):
        self.master = master
        self.tool_class = tool_class

    def __call__(self):
        return self.tool_class(self.master)

class App(tk.Tk):

    def __init__(self):
        super(App, self).__init__()
        self.title(get_locale("app.title"))

        self.topmenu = tk.Menu(self)

        self.filemenu = tk.Menu(self.topmenu, tearoff=0)
        self.filemenu.add_command(label=get_locale("app.menu.file.open_mat"), command=self.open_mat_file)
        #self.filemenu.add_command(label=get_locale("app.menu.file.load_settings"), command=self.on_settings_load)
        #self.filemenu.add_command(label=get_locale("app.menu.file.save_settings"), command=self.on_settings_save)

        #self.toolsmenu = tk.Menu(self.topmenu, tearoff=0)
        self.topmenu.add_cascade(label=get_locale("app.menu.file"), menu=self.filemenu)
        #self.topmenu.add_cascade(label=get_locale("app.menu.tools"), menu=self.toolsmenu)
        self.config(menu=self.topmenu)
        self.file = None
        self.tool_list = []
        self.main_notebook = ttk.Notebook(self)
        self.main_notebook.pack(side="top",fill="both",expand=True)
        self.add_tool("app.menu.tools.mat_player", MatPlayer)
        self.add_tool("app.menu.tools.starcalibrator", StarCalibrator)
        self.add_tool("app.menu.tools.mat_converter", MatConverter)
        self.add_tool("app.menu.tools.flatfielder", FlatFielder)
        self.add_tool("app.menu.tools.track_markup", TrackMarkup)



    def add_tool(self, label_key, toolclass):
        tool_frame = toolclass(self.main_notebook)
        tool_frame.pack(fill="both",expand=True)
        self.main_notebook.add(tool_frame,text=get_locale(label_key))
        self.tool_list.append(tool_frame)
        #tool_inst = Tool(self, toolclass)
        #self.toolsmenu.add_command(label=get_locale(label_key), command=tool_inst)

    def open_mat_file(self):
        filename = filedialog.askopenfilename(title=get_locale("app.filedialog.load_mat.title"),
                                              filetypes=[
                                                  (get_locale("app.filedialog_formats.processed_mat"), "*.mat *.hdf")
                                              ])
        if filename and os.path.isfile(filename):
            new_file = h5py.File(filename, "r")
            if self.file:
                self.file.close()
            self.file = new_file
            for tool in self.tool_list:
                tool.propagate_mat_file(self.file)

    def close_mat_file(self):
        if self.file:
            self.file.close()
            self.file = None





if __name__ == "__main__":
    root = App()
    root.mainloop()
