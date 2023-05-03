from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode, OptionNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from vtl_common.localization import get_locale
from noise.noising import FloatDistributedAlter
from preprocessing.forms import DataPreProcessorField
from track_gen.track_forms import TrajectoryField, LightCurveField, PSFField


class TimeCapOption(OptionNode):
    DISPLAY_NAME = get_locale("track_toolbox.form.time_cap")
    ITEM_TYPE = create_value_field(IntNode,get_locale("track_toolbox.form.time"),128)
    DEFAULT_VALUE = None

class RealBgForm(FormNode):
    DISPLAY_NAME = get_locale("track_toolbox.form.real_bg.params")
    FIELD__preprocessor = DataPreProcessorField
    FIELD__start_frame = create_value_field(IntNode, get_locale("track_toolbox.form.real_bg.params.start"), 0)


class RealBgOption(OptionNode):
    DISPLAY_NAME = get_locale("track_toolbox.form.real_bg")
    ITEM_TYPE = RealBgForm


class ToolboxForm(FormNode):
    FIELD__trajectory = TrajectoryField
    FIELD__light_curve = LightCurveField
    FIELD__psf = PSFField
    FIELD__duration = create_value_field(IntNode, get_locale("track_toolbox.form.duration"),128)
    FIELD__subframes = create_value_field(IntNode, get_locale("track_toolbox.form.subframes"),10)
    FIELD__time_cap = TimeCapOption
    FIELD__seed = create_value_field(IntNode, get_locale("track_toolbox.form.seed"),42)
    FIELD__noise = create_value_field(FloatDistributedAlter, get_locale("track_toolbox.form.noise"))
    FIELD__real_bg = RealBgOption