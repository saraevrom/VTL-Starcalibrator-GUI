import tkinter as tk
from tools.tool_base import ToolBase
#from .converter_old import ConverterOld
from .converter import Converter
from .downloader import Downloader

class MatConverter(ToolBase):
    def __init__(self, master):
        super(MatConverter, self).__init__(master)
        converter = Converter(self, self)
        converter.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0,weight=1)
        downloader = Downloader(self)
        downloader.grid(row=0, column=1, sticky="nsew")


if __name__=="__main__":
    root = tk.Tk()
    conv = MatConverter(root)
    root.mainloop()