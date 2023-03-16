
from tkinter.messagebox import askokcancel, showinfo, showerror
from vtl_common.localization import get_locale, format_locale
import subprocess
import sys

class AppModifier(object):

    @classmethod
    def get_ext_name(cls):
        return "FIXME"

    @staticmethod
    def modify_apply():
        raise NotImplementedError()

    @staticmethod
    def modify_needed():
        raise NotImplementedError()

class PackageInstallModifier(AppModifier):
    PKG_NAME = "FIXME"
    PKG_DESC_KEY = "FIXME"

    @classmethod
    def get_ext_name(cls):
        return format_locale("app.extension.action_install_pkg", cls.PKG_NAME)

    @classmethod
    def modify_apply(cls):
        if askokcancel(title=format_locale("app.extension.action_install_pkg", cls.PKG_NAME),
                       message=get_locale(cls.PKG_DESC_KEY)):
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", cls.PKG_NAME])
                showinfo(title=format_locale("app.extension.action_install_pkg", cls.PKG_NAME),
                         message=format_locale("app.extension.action_install_pkg_info_ok", cls.PKG_NAME))
            except subprocess.CalledProcessError:
                showerror(title=format_locale("app.extension.action_install_pkg", cls.PKG_NAME),
                          message=format_locale("app.extension.action_install_pkg_info_err", cls.PKG_NAME))
