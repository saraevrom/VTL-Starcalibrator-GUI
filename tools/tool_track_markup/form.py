from common_GUI import TkDictForm
from common_GUI.tk_forms_assist import FormNode, IntNode, ComboNode, BoolNode
from common_GUI.tk_forms_assist.factory import create_value_field
from localization import get_locale
from ..tool_teacher.advanced_form import DataPreProcessorForm

class PmtSelect(ComboNode):
    DISPLAY_NAME = get_locale("track_markup.form.pmt_select")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "full"
    VALUES = ["full", "topright", "topleft", "bottomright", "bottomleft"]

class TrackMarkupForm(FormNode):
    FIELD__preprocessing = DataPreProcessorForm
    FIELD__min_frame = create_value_field(IntNode, get_locale("track_markup.form.min_frame"), 256)
    FIELD__pmt_select = PmtSelect