from .mod_base import AppModifier

try:
    import tensorflow
    TENSORFLOW_INSTALLED = True
except ModuleNotFoundError:
    TENSORFLOW_INSTALLED = False

import subprocess
import sys
from tkinter.messagebox import askokcancel, showinfo, showerror
from localization import get_locale

'''
Make tensorflow and ANN stuff optional.
'''

class OptionalTfModifier(AppModifier):
    EXT_NAME = get_locale("app.extension.action_install_tf")

    @staticmethod
    def modify_needed():
        return not TENSORFLOW_INSTALLED

    @staticmethod
    def modify_apply():
        if askokcancel(title=get_locale("app.extension.action_install_tf"),
                       message=get_locale("app.extension.action_install_tf_desc")):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "tensorflow-cpu"])
                showinfo(title=get_locale("app.extension.action_install_tf"),
                         message=get_locale("app.extension.action_install_tf_info_ok"))
            except subprocess.CalledProcessError:
                showerror(title=get_locale("app.extension.action_install_tf"),
                          message=get_locale("app.extension.action_install_tf_info_err"))
