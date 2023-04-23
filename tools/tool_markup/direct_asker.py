import tkinter.simpledialog as simpledialog
from vtl_common.localization import get_locale

from vtl_common.common_GUI import TkDictForm

from .storage import Interval

FORM_CONF = {
    "start": {
        "type": "int",
        "default": 0,
        "display_name": get_locale("track_markup.form.start")
    },
    "length": {
        "type": "int",
        "default": 1,
        "display_name": get_locale("track_markup.form.length")
    },

}


class RangeAsker(simpledialog.Dialog):
    def __init__(self, parent):
        self.result = None
        self.form = None
        super().__init__(parent)

    def body(self, master):
        self.title(get_locale("track_markup.dialog.reset"))
        self.form = TkDictForm(master, tk_form_configuration=FORM_CONF, use_scrollview=False)
        self.form.pack(side="bottom", fill="both", expand=True)

    def apply(self):
        formdata = self.form.get_values()
        start = formdata["start"]
        length = formdata["length"]
        if length>0:
            self.result = Interval(start, start+length)