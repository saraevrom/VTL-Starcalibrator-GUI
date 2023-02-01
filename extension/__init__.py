from .optional_tensorflow import OptionalTfModifier
import tkinter as tk
from localization import get_locale

MODS = [OptionalTfModifier]


def expand_app(app_menu):
    menu = None
    for mod in MODS:
        if mod.modify_needed():
            if menu is None:
                menu = tk.Menu(app_menu, tearoff=0)
            menu.add_command(label=mod.EXT_NAME, command=mod.modify_apply)

    if menu is not None:
        app_menu.add_cascade(label=get_locale("app.menu.extension"), menu=menu)