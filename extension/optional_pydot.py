from .mod_base import PackageInstallModifier

try:
    import pydot
    PYDOT_INSTALLED = True
except ModuleNotFoundError:
    PYDOT_INSTALLED = False


import subprocess
import sys
from tkinter.messagebox import askokcancel, showinfo, showerror
from localization import get_locale, format_locale

'''
Make pydot optional.
'''


class OptionalPydotModifier(PackageInstallModifier):

    PKG_NAME = "pydot"
    PKG_DESC_KEY = "app.extension.action_install_pydot_desc"

    @staticmethod
    def modify_needed():
        return not PYDOT_INSTALLED