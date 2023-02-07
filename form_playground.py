# from tools.tool_teacher.advanced_form import SettingForm
# from trigger_ai.compiler_form import CompileForm
# from tools.tool_track_markup.form import TrackMarkupForm
# from trigger_ai.neural_builder.form_elements import LayerSequenceConstructor
import tkinter as tk
from common_GUI import TkDictForm
# from common_GUI.tk_forms_assist import FormNode



class Playground(tk.Tk):
    def __init__(self, formclass):
        super().__init__()
        self.title("Playground")
        self.formparser = formclass()
        conf = self.formparser.get_configuration_root()
        print("# TkDictForm configuration")
        print(conf)
        self.form = TkDictForm(self, conf, True)
        self.form.pack(fill="both", expand=True)

        commit_btn = tk.Button(self, text="Read data", command=self.on_getdata_btn_click)
        commit_btn.pack(side="bottom", fill="x")

    def on_getdata_btn_click(self):
        values = self.form.get_values()
        print("# Raw form data")
        print(values)
        self.formparser.parse_formdata(values)
        parsed = self.formparser.get_data()
        print("# Parsed form data")
        print(parsed)

    
