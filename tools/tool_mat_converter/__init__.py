import tkinter as tk
from tkinter import ttk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
import h5py
import numpy as np
import tqdm
import scipy.io as scipio
from localization import get_locale, format_locale
from tools.tool_base import ToolBase
from .converter import Converter
from .converter_new import ConverterNew
from .downloader import Downloader

class MatConverter(ToolBase):
    def __init__(self, master):
        super(MatConverter, self).__init__(master)
        converter = ConverterNew(self,self)
        converter.grid(row=0, column=0, sticky="nsew")
        downloader = Downloader(self)
        downloader.grid(row=0, column=1, sticky="nsew")


if __name__=="__main__":
    root = tk.Tk()
    conv = MatConverter(root)
    root.mainloop()