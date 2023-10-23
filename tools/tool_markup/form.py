from vtl_common.common_GUI import TkDictForm
from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode, ComboNode, BoolNode, FloatNode, OptionNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field, kwarg_builder
from vtl_common.localization import get_locale
from preprocessing.forms import DataPreProcessorField


from extension.optional_tensorflow import TENSORFLOW_INSTALLED
if TENSORFLOW_INSTALLED:
    from trigger_ai.models.common import deconvolve_windows_mean, deconvolve_windows_max
else:
    deconvolve_windows_mean = None
    deconvolve_windows_max = None

from .phase_cutter import PhaseCutter

class PmtSelect(ComboNode):
    DISPLAY_NAME = get_locale("track_markup.form.pmt_select")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "full"
    VALUES = ["full", "topright", "topleft", "bottomright", "bottomleft"]


DECONVOLVERS = {
    "mean":deconvolve_windows_mean,
    "max":deconvolve_windows_max
}

class DeconvolveWindowCombo(ComboNode):
    SELECTION_READONLY = True
    DISPLAY_NAME = get_locale("track_markup.form.trigger.deconvolve_window")
    VALUES = list(DECONVOLVERS.keys())
    DEFAULT_VALUE = list(DECONVOLVERS.keys())[0]

    def get_data(self):
        dat = super().get_data()
        return DECONVOLVERS[dat]


class TriggerParameters(FormNode):
    DISPLAY_NAME = get_locale("track_markup.form.trigger")
    FIELD__threshold = create_value_field(FloatNode, get_locale("track_markup.form.trigger.threshold"), 0.5)
    # FIELD__edge_shift = create_value_field(IntNode, get_locale("track_markup.form.trigger.edge_shift"), 64)
    #FIELD__stabilize_slide = create_value_field(BoolNode, get_locale("track_markup.form.trigger.stabilize"), True)
    FIELD__max_plot = create_value_field(IntNode, get_locale("track_markup.form.trigger.max_data_plot"), 5000)
    FIELD__deconvolve_window = DeconvolveWindowCombo
    FIELD__expand_window = create_value_field(BoolNode, get_locale("track_markup.form.trigger.expand_window"), True)
    USE_SCROLLVIEW = False


@kwarg_builder(PhaseCutter)
class PhaseCutterForm(FormNode):
    DISPLAY_NAME = ""
    FIELD__lower_intensity = create_value_field(FloatNode, get_locale("track_markup.form.phase_cut.lower_intensity"))
    FIELD__lower_duration = create_value_field(FloatNode, get_locale("track_markup.form.phase_cut.lower_duration"))
    FIELD__upper_duration = create_value_field(FloatNode, get_locale("track_markup.form.phase_cut.upper_duration"))


class PhaseCutterOption(OptionNode):
    DISPLAY_NAME = get_locale("track_markup.form.phase_cut")
    ITEM_TYPE = PhaseCutterForm

class TrackMarkupForm(FormNode):
    FIELD__max_frame = create_value_field(IntNode, get_locale("track_markup.form.max_frame"), 9000)
    FIELD__apply_ff = create_value_field(BoolNode, get_locale("track_markup.form.apply_ff"), True)
    FIELD__preprocessing = DataPreProcessorField
    FIELD__phase_cut = PhaseCutterOption
    FIELD__min_frame = create_value_field(IntNode, get_locale("track_markup.form.min_frame"), 256)
    FIELD__pmt_select = PmtSelect
    FIELD__trigger = TriggerParameters
    FIELD__override_ann_filter = create_value_field(BoolNode, get_locale("track_markup.form.override_ann"), False)
    FIELD__auto_cont = create_value_field(BoolNode, get_locale("track_markup.form.auto_continue"), False)