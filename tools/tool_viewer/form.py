from vtl_common.common_GUI.tk_forms_assist import FormNode,IntNode,BoolNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from vtl_common.localization import get_locale
from preprocessing import DataPreProcessorField


class GifRenderer(FormNode):
    DISPLAY_NAME = get_locale("matplayer.form.gif_renderer")
    FIELD__frame_skip = create_value_field(IntNode, get_locale("matplayer.form.gif_renderer.frame_skip"), 1)
    FIELD__fps = create_value_field(IntNode, get_locale("matplayer.form.gif_renderer.fps"), 5)

class ViewerForm(FormNode):
    FIELD__use_flatfielding = create_value_field(BoolNode, get_locale("matplayer.form.use_flatfielding"), True)
    FIELD__use_times = create_value_field(BoolNode, get_locale("matplayer.form.use_times"), False)
    FIELD__use_gtu = create_value_field(BoolNode, get_locale("matplayer.form.use_gtu"), False)
    FIELD__filter = DataPreProcessorField
    #FIELD__use_filter = create_value_field(BoolNode, get_locale("matplayer.form.use_filter"), False)
    #FIELD__filter_window = create_value_field(IntNode, get_locale("matplayer.form.filter_window"), 60)
    FIELD__gif_renderer = GifRenderer