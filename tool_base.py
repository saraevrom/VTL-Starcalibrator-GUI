import tkinter as tk

class ToolBase(tk.Toplevel):

    def __init__(self, master):
        super(ToolBase, self).__init__(master)

    def on_loaded_file_success(self):
        pass


    def get_mat_file(self):
        if hasattr(self,"master") and hasattr(self.master, "file"):
            self.file = self.master.file
            if self.file:
                self.on_loaded_file_success()