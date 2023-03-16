from .mod_base import PackageInstallModifier

try:
    import tensorflow
    TENSORFLOW_INSTALLED = True
except ModuleNotFoundError:
    TENSORFLOW_INSTALLED = False

import subprocess
import sys
from tkinter.messagebox import askokcancel, showinfo, showerror
from vtl_common.localization import get_locale, format_locale

'''
Make tensorflow and ANN stuff optional.
'''


class OptionalTfModifier(PackageInstallModifier):
    PKG_NAME = "tensorflow-cpu"
    PKG_DESC_KEY = "app.extension.action_install_tf_desc"

    @staticmethod
    def modify_needed():
        return not TENSORFLOW_INSTALLED
