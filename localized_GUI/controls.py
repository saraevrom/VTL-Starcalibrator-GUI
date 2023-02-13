import tkinter as tk
import tkinter.filedialog as filedialog
from localization import get_locale
import json

class TkFormControlPanel(tk.Frame):
    def __init__(self,master, file_asker = None):
        super().__init__(master)
        btn1 = tk.Button(self, text=get_locale("app.filedialog.load_settings.title"), command=self.on_load)
        btn1.pack(side="left", fill="x", expand=True)
        btn2 = tk.Button(self, text=get_locale("app.filedialog.save_settings.title"), command=self.on_save)
        btn2.pack(side="right", fill="x", expand=True)
        self.connected_form = None
        if file_asker is None:
            self.file_asker = filedialog
        else:
            self.file_asker = file_asker

    def connect_form(self, form):
        self.connected_form = form

    def on_save(self):
        filename = self.file_asker.asksaveasfilename(title=get_locale("app.filedialog.save_settings.title"),
                                     filetypes=[(get_locale("app.filedialog_formats.form_json"), "*.json")],
                                     initialdir=".",
                                     parent=self)
        if filename and self.connected_form:
            jsd = self.connected_form.get_values()
            with open(filename, "w") as fp:
                json.dump(jsd, fp, indent=4)

    def on_load(self):
        filename = self.file_asker.askopenfilename(title=get_locale("app.filedialog.save_settings.title"),
                                                filetypes=[(get_locale("app.filedialog_formats.form_json"), "*.json")],
                                                initialdir=".",
                                                parent=self)
        if filename and self.connected_form:
            with open(filename, "r") as fp:
                jsd = json.load(fp)
            self.connected_form.set_values(jsd)