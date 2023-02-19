from common_GUI.tk_forms_assist import FormNode,IntNode,BoolNode
from common_GUI.tk_forms_assist.factory import create_value_field
from localization import get_locale

class ViewerForm(FormNode):
    FIELD__use_filter = create_value_field(BoolNode, get_locale("matplayer.form.use_filter"), False)
    FIELD__filter_window = create_value_field(IntNode, get_locale("matplayer.form.filter_window"), 60)
    FIELD__use_flatfielding = create_value_field(BoolNode, get_locale("matplayer.form.use_flatfielding"), True)