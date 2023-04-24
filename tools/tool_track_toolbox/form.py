from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode, OptionNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from vtl_common.localization import get_locale

from track_gen.track_forms import TrajectoryField, LightCurveField, PSFField


class TimeCapOption(OptionNode):
    DISPLAY_NAME = get_locale("track_toolbox.form.time_cap")
    ITEM_TYPE = create_value_field(IntNode,get_locale("track_toolbox.form.time"),128)
    DEFAULT_VALUE = None

class ToolboxForm(FormNode):
    FIELD__trajectory = TrajectoryField
    FIELD__light_curve = LightCurveField
    FIELD__psf = PSFField
    FIELD__duration = create_value_field(IntNode, get_locale("track_toolbox.form.duration"),128)
    FIELD__subframes = create_value_field(IntNode, get_locale("track_toolbox.form.subframes"),10)
    FIELD__time_cap = TimeCapOption