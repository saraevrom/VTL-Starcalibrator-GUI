from vtl_common.common_GUI import TkDictForm
from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode, ComboNode, BoolNode, FloatNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from vtl_common.localization import get_locale
from preprocessing.forms import DataPreProcessorField


class PmtSelect(ComboNode):
    DISPLAY_NAME = get_locale("track_markup.form.pmt_select")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "full"
    VALUES = ["full", "topright", "topleft", "bottomright", "bottomleft"]


class TriggerParameters(FormNode):
    DISPLAY_NAME = get_locale("track_markup.form.trigger")
    FIELD__threshold = create_value_field(FloatNode, get_locale("track_markup.form.trigger.threshold"), 0.5)
    # FIELD__edge_shift = create_value_field(IntNode, get_locale("track_markup.form.trigger.edge_shift"), 64)
    FIELD__stabilize_slide = create_value_field(BoolNode, get_locale("track_markup.form.trigger.stabilize"), True)
    FIELD__max_plot = create_value_field(IntNode, get_locale("track_markup.form.trigger.max_data_plot"), 5000)
    USE_SCROLLVIEW = False


class TrackMarkupForm(FormNode):
    FIELD__max_frame = create_value_field(IntNode, get_locale("track_markup.form.max_frame"), 0)
    FIELD__preprocessing = DataPreProcessorField
    FIELD__min_frame = create_value_field(IntNode, get_locale("track_markup.form.min_frame"), 256)
    FIELD__pmt_select = PmtSelect
    FIELD__trigger = TriggerParameters
    FIELD__override_ann_filter = create_value_field(BoolNode, get_locale("track_markup.form.override_ann"), False)
    FIELD__auto_cont = create_value_field(BoolNode, get_locale("track_markup.form.auto_continue"), False)