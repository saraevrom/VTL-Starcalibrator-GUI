import json
import os.path as ospath
import tkinter as tk
import tkinter.filedialog as filedialog
import tkinter.messagebox as messagebox
from localization import get_locale
import os

cwd = ospath.abspath(__file__)
CONF_PATH = ospath.join(ospath.dirname(cwd), "workspace.json")


class Workspace(object):
    WORKSPACE_DIR = None

    def __init__(self, subspace):
        self.subspace = subspace

    def ensure_directory(self):
        if self.WORKSPACE_DIR:
            os.makedirs(ospath.join(self.WORKSPACE_DIR, self.subspace),exist_ok=True)
            return ospath.join(self.WORKSPACE_DIR, self.subspace)
        return None

    def _modify_kwargs(self, kwargs):
        cwd = self.ensure_directory()
        if cwd:
            kwargs["initialdir"] = cwd

    def askopenfilename(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        return filedialog.askopenfilename(*args, **kwargs)

    def askdirectory(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        return filedialog.askdirectory(*args, **kwargs)

    def asksaveasfilename(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        return filedialog.asksaveasfilename(*args, **kwargs)

    def askopenfilenames(self, *args, **kwargs):
        self._modify_kwargs(kwargs)
        return filedialog.askopenfilenames(*args, **kwargs)

    @classmethod
    def initialize_workspace(cls, force=False):
        if ospath.isfile(CONF_PATH) and not force:
            with open(CONF_PATH, "r") as fp:
                cls.WORKSPACE_DIR = json.load(fp)["workspace"]
        else:
            messagebox.showinfo(
                title=get_locale("app.workspace_manager.greeter.title"),
                message=get_locale("app.workspace_manager.greeter.message")
            )
            workspace_dir = filedialog.askdirectory(initialdir=".",
                                                    title=get_locale("app.workspace_manager.askdir"))
            if not workspace_dir:
                workspace_dir = None
            with open(CONF_PATH, "w") as fp:
                json.dump({"workspace": workspace_dir}, fp)
            cls.WORKSPACE_DIR = workspace_dir
