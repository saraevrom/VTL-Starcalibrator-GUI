import matplotlib.pyplot as plt
from multiprocessing import cpu_count
import os.path as ospath
import json
from .parameters_defs import get_defaults
from .forms import MainParametersForm
from .forms import localize_fields as localize_parameters_fields
import tkinter as tk
from tkinter.simpledialog import Dialog
from common_GUI import TkDictForm

cwd = ospath.abspath(__file__)
settings_path = ospath.join(ospath.dirname(cwd), "parameters.json")

if ospath.isfile(settings_path):
    with open(settings_path, "r") as fp:
        LOADED_SETTINGS = json.load(fp)
        print("Loaded settings")
else:
    settings = get_defaults()
    print("Created settings file")
    with open(settings_path, "w") as fp:
        json.dump(settings, fp, indent=4)
    LOADED_SETTINGS = settings

parser = MainParametersForm()
parser.parse_formdata(LOADED_SETTINGS)
LOADED_SETTINGS_OBJ = parser.get_data()
for k in LOADED_SETTINGS_OBJ.keys():
    globals()[k] = LOADED_SETTINGS_OBJ[k]

del parser
del LOADED_SETTINGS_OBJ


class SettingsDialog(Dialog):
    
    def __init__(self,master, title):
        self.__title = title
        super().__init__(master)

    def body(self, master):
        self.title(self.__title)
        self.parser = MainParametersForm()
        self.form = TkDictForm(master, self.parser.get_configuration_root())
        self.form.pack(fill=tk.BOTH, expand=True)
        self.form.set_values(LOADED_SETTINGS)
        master.pack_forget()
        master.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

    def apply(self):
        with open(settings_path, "w") as fp:
            json.dump(self.form.get_values(), fp, indent=4)
            print("Settings saved. Restart application for effect.")


def add_parameters_menu(app_menu: tk.Menu):
    from workspace_manager import Workspace
    from localization import get_locale
    menu = tk.Menu(app_menu, tearoff=0)

    def settings_wrapper():
        SettingsDialog(app_menu.winfo_toplevel(), get_locale("app.parameters"))

    def workspace_wrapper():
        Workspace.initialize_workspace(True)

    menu.add_command(label=get_locale("app.parameters"), command=settings_wrapper)
    menu.add_command(label=get_locale("app.workspace_manager.setup"), command=workspace_wrapper)
    app_menu.add_cascade(label=get_locale("app.menu.settings"), menu=menu)