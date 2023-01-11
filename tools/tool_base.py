import tkinter as tk
import warnings

class ToolBase(tk.Frame):

    def __init__(self, master):
        super(ToolBase, self).__init__(master)

    def on_loaded_file_success(self):
        pass


    def title(self,*args,**kwargs):
        warnings.warn("Now all tools are frames, not toplevels")


    def get_mat_file(self):
        if hasattr(self, "master") and hasattr(self.master, "file"):
            self.file = self.master.file
            if self.file:
                self.on_loaded_file_success()

    def propagate_mat_file(self, file):
        self.file = file
        self.on_loaded_file_success()

    def get_ff_model(self):
        return self.winfo_toplevel().get_ffmodel()

    def trigger_ff_model_reload(self):
        self.winfo_toplevel().reload_ffmodel()