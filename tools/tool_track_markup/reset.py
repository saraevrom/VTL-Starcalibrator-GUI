import tkinter as tk
import tkinter.simpledialog as simpledialog
from localization import get_locale

from tk_forms import TkDictForm

FORM_CONF = {
    "max_frame": {
        "type": "int",
        "default": 0,
        "display_name": get_locale("track_markup.form.max_frame")
    },
    "start_skip":{
        "type": "int",
        "default": 0,
        "display_name": get_locale("track_markup.form.start_skip")
    },
    "end_skip":{
        "type": "int",
        "default": 0,
        "display_name": get_locale("track_markup.form.end_skip")
    },

}

class ResetAsker(simpledialog.Dialog):
    def body(self, master):
        self.title(get_locale("track_markup.dialog.reset"))
        self.form = TkDictForm(master,tk_form_configuration=FORM_CONF,use_scrollview=False)
        self.form.pack(side="bottom",fill="both",expand=True)
        self.result = None

    def apply(self):
        self.result = self.form.get_values()