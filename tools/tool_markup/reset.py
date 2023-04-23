import tkinter.simpledialog as simpledialog
from vtl_common.localization import get_locale

from vtl_common.common_GUI import TkDictForm

FORM_CONF = {
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
    def __init__(self, parent, tgt_length):
        self.tgt_length = tgt_length
        self.result = None
        self.form = None
        super().__init__(parent)
    
    def body(self, master):
        self.title(get_locale("track_markup.dialog.reset"))
        self.form = TkDictForm(master,tk_form_configuration=FORM_CONF,use_scrollview=False)
        self.form.pack(side="bottom",fill="both",expand=True)

    def apply(self):
        formdata = self.form.get_values()
        start = formdata["start_skip"]
        end = formdata["end_skip"]
        self.result = min(start,self.tgt_length), min(end,self.tgt_length)