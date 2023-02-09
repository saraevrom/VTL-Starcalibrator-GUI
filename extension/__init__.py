from .optional_tensorflow import OptionalTfModifier
from .optional_pydot import OptionalPydotModifier
import tkinter as tk
from localization import get_locale

MODS = [OptionalTfModifier, OptionalPydotModifier]


def expand_app(app_menu):
    menu = None
    for mod in MODS:
        if mod.modify_needed():
            if menu is None:
                menu = tk.Menu(app_menu, tearoff=0)
            menu.add_command(label=mod.get_ext_name(), command=mod.modify_apply)

    if menu is not None:
        app_menu.add_cascade(label=get_locale("app.menu.extension"), menu=menu)