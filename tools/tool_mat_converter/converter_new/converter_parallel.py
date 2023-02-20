from multiprocessing import Process, Pipe
import tkinter as tk
import tkinter.ttk as ttk
from localization import get_locale

class ParallelWorker(Process):
    def __init__(self, conn, filelist, output_filename):
        super().__init__()
        self.conn = conn
        self.filelist = filelist
        self.output_filename = output_filename

class ConverterParallel(tk.Toplevel):
    def __init__(self, master, filelist, output_filename, conv_parameters):
        super().__init__(master)
        self.title(get_locale("mat_converter.title"))
        self.filelist = filelist
        self.output_filename = output_filename
        self.conv_parameters = conv_parameters
        self.current_file_display = tk.StringVar()
        tk.Label(self, textvariable=self.current_file_display).pack(side="top", fill="x")
        self.files_display = self._add_bar()
        self.frames_display = self._add_bar()
        parent_pipe, child_pipe = Pipe(duplex=True)
        self.conn = parent_pipe
        self.converter = ParallelWorker(child_pipe, filelist=filelist, output_filename=output_filename)

    def _add_bar(self):
        variable = tk.StringVar()
        frame = tk.Frame(self)
        frame.pack(side="top", fill="x")
        bar = ttk.Progressbar(frame, orient=tk.HORIZONTAL)
        bar.pack(side="left", fill="x", expand=True)
        tk.Label(frame, textvariable=variable).pack(side="right")
        return variable, bar
