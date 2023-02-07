from .model import create_trigger_model
from common_GUI import TkDictForm
import tkinter as tk
import tkinter.simpledialog as simpledialog
from localization import get_locale
from .compiler_form import CompileForm
import json

from trigger_ai.models import ModelBuilder
from tkinter import filedialog

class TkFormControlPanel(tk.Frame):
    def __init__(self,master):
        super().__init__(master)
        btn1 = tk.Button(self, text=get_locale("app.filedialog.load_settings.title"), command=self.on_load)
        btn1.pack(side="left", fill="x", expand=True)
        btn2 = tk.Button(self, text=get_locale("app.filedialog.save_settings.title"), command=self.on_save)
        btn2.pack(side="right", fill="x", expand=True)
        self.connected_form = None

    def connect_form(self, form):
        self.connected_form = form

    def on_save(self):
        filename = filedialog.asksaveasfilename(title=get_locale("app.filedialog.save_settings.title"),
                                     filetypes=[(get_locale("app.filedialog_formats.form_json"), "*.json")],
                                     initialdir=".",
                                     parent=self)
        if filename and self.connected_form:
            jsd = self.connected_form.get_values()
            with open(filename, "w") as fp:
                json.dump(jsd, fp, indent=4)

    def on_load(self):
        filename = filedialog.askopenfilename(title=get_locale("app.filedialog.save_settings.title"),
                                                filetypes=[(get_locale("app.filedialog_formats.form_json"), "*.json")],
                                                initialdir=".",
                                                parent=self)
        if filename and self.connected_form:
            with open(filename, "r") as fp:
                jsd = json.load(fp)
            self.connected_form.set_values(jsd)

class CompileDialog(simpledialog.Dialog):
    def body(self, master):
        self.form_parser = CompileForm()
        conf = self.form_parser.get_configuration_root()
        self.form = TkDictForm(master, conf, True)
        self.form.pack(fill="both", expand=True)
        self.result = None
        self.title(get_locale("app.model.form.title_compile"))

        controller = TkFormControlPanel(master)
        controller.pack(side="bottom", fill="x")
        controller.connect_form(self.form)

        # Due to inconsistency of python tk.simpledialog implementations, this fix should enable rescaling.
        master.pack_forget()
        master.pack(padx=5, pady=5, expand=True, fill=tk.BOTH)

    def apply(self):
        formdata = self.form.get_values()
        self.form_parser.parse_formdata(formdata)
        self.result = self.form_parser.get_data()

    def compile_model(self, model):
        print(self.result)
        #model = self.result["model"]
        kwargs = {k: self.result[k] for k in ["loss", "optimizer", "metrics"]}
        model.compile(**kwargs)
        model.summary()


class CreateDialog(simpledialog.Dialog):
    def body(self, master):
        self.form_parser = ModelBuilder()
        conf = self.form_parser.get_configuration_root()
        self.form = TkDictForm(master, conf, True)
        self.form.pack(fill="both", expand=True)
        self.result = None
        self.title(get_locale("app.model.form.title_create"))

        controller = TkFormControlPanel(master)
        controller.pack(side="bottom", fill="x")
        controller.connect_form(self.form)

        # Due to inconsistency of python tk.simpledialog implementations, this fix should enable rescaling.
        master.pack_forget()
        master.pack(padx=5, pady=5, expand=True, fill=tk.BOTH)

    def apply(self):
        formdata = self.form.get_values()
        self.form_parser.parse_formdata(formdata)
        self.result = self.form_parser.get_data()


def create_model(tk_parent):
    create_params = CreateDialog(tk_parent)
    if create_params.result:
        return create_params.result


def compile_model(model,  tk_parent):
    compile_params = CompileDialog(tk_parent)
    if compile_params.result:
        compile_params.compile_model(model)
