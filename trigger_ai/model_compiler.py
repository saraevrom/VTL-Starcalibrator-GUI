from .model import create_trigger_model
from common_GUI import TkDictForm
import tkinter as tk
import tkinter.simpledialog as simpledialog
from localization import get_locale
from .compiler_form import CompileForm
from .model_creating_form import NeuralNetworkCreator

from trigger_ai.models import ModelBuilder

class CompileDialog(simpledialog.Dialog):
    def body(self, master):
        self.form_parser = CompileForm()
        conf = self.form_parser.get_configuration_root()
        self.form = TkDictForm(master, conf, True)
        self.form.pack(fill="both", expand=True)
        self.result = None
        self.title(get_locale("app.model.form.title_compile"))

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
