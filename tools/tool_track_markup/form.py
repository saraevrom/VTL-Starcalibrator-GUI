from common_GUI import TkDictForm
from common_GUI.tk_forms_assist import FormNode, IntNode, ComboNode, BoolNode, FloatNode
from common_GUI.tk_forms_assist.factory import create_value_field
from localization import get_locale
from preprocessing.forms import DataPreProcessorForm
from .edges import EdgeProcessor

class PmtSelect(ComboNode):
    DISPLAY_NAME = get_locale("track_markup.form.pmt_select")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "full"
    VALUES = ["full", "topright", "topleft", "bottomright", "bottomleft"]


class TriggerParameters(FormNode):
    DISPLAY_NAME = get_locale("track_markup.form.trigger")
    FIELD__threshold = create_value_field(FloatNode, get_locale("track_markup.form.trigger.threshold"), 0.5)
    FIELD__edge_shift = create_value_field(IntNode, get_locale("track_markup.form.trigger.edge_shift"), 64)
    USE_SCROLLVIEW = False
    
    def get_data(self):
        return EdgeProcessor(**super().get_data())

class TrackMarkupForm(FormNode):
    FIELD__preprocessing = DataPreProcessorForm
    FIELD__min_frame = create_value_field(IntNode, get_locale("track_markup.form.min_frame"), 256)
    FIELD__pmt_select = PmtSelect
    FIELD__trigger = TriggerParameters
    FIELD__auto_cont = create_value_field(BoolNode, get_locale("track_markup.form.auto_continue"), False)