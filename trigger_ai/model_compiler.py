from .model import create_trigger_model
from common_GUI import TkDictForm
import tkinter as tk
import tkinter.simpledialog as simpledialog
from localization import get_locale
from .compiler_form import CompileForm



class CompileDialog(simpledialog.Dialog):
    def body(self, master):
        self.form_parser = CompileForm()
        conf = self.form_parser.get_configuration_root()
        self.form = TkDictForm(master, conf, True)
        self.form.pack(fill="both", expand=True)
        self.result = None
        self.title(get_locale("app.model.form.title"))

    def apply(self):
        formdata = self.form.get_values()
        self.form_parser.parse_formdata(formdata)
        self.result = self.form_parser.get_data()

    def compile_model(self):
        print(self.result)
        model = self.result["model"]
        kwargs = {k: self.result[k] for k in ["loss", "optimizer", "metrics"]}
        model.compile(**kwargs)
        model.summary()
        return model


def compile_model(frames, tk_parent):
    compile_params = CompileDialog(tk_parent)
    if compile_params.result:
        model = compile_params.compile_model()
        return model
    return None