import tkinter as tk

try:
    from tkinter.ttk import Spinbox
except ImportError:
    from compatibility.py36xspinbox import Spinbox
    print("Spinbox compat is loaded")

from tkinter.simpledialog import _get_temp_root, _destroy_temp_root, _setup_dialog, _place_window
from tkinter import messagebox
from tkinter.simpledialog import Dialog

class EntryWithEnterKey(tk.Entry):
    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        self.bind("<Return>", self.on_keypress_enter)
        self.on_commit = None

    def on_keypress_enter(self, *args):
        self.winfo_toplevel().focus()
        if self.on_commit:
            self.on_commit()


class SpinboxWithEnterKey(Spinbox):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.bind("<Return>", self.on_keypress_enter)

    def on_keypress_enter(self, *args):
        self.winfo_toplevel().focus()


# If you try to scale tk.dialog it will hurt your eyes. Overriding its consstructor helps.
class DialogScalable(Dialog):
    def __init__(self, parent, title=None):
        '''Initialize a dialog.
        Arguments:
            parent -- a parent window (the application window)
            title -- the dialog title
        '''
        master = parent
        if master is None:
            master = _get_temp_root()

        tk.Toplevel.__init__(self, master)

        self.withdraw() # remain invisible for now
        # If the parent is not viewable, don't
        # make the child transient, or else it
        # would be opened withdrawn
        if parent is not None and parent.winfo_viewable():
            self.transient(parent)

        if title:
            self.title(title)

        _setup_dialog(self)

        self.parent = parent

        self.result = None

        body = tk.Frame(self)
        self.initial_focus = self.body(body)
        body.pack(fill="both", padx=5, pady=5, expand=True) #Override filling

        self.buttonbox()

        if self.initial_focus is None:
            self.initial_focus = self

        self.protocol("WM_DELETE_WINDOW", self.cancel)

        _place_window(self, parent)

        self.initial_focus.focus_set()

        # wait for window to appear on screen before calling grab_set
        self.wait_visibility()
        self.grab_set()
        self.wait_window(self)
