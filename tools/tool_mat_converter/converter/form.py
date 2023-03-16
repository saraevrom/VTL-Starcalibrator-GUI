from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from vtl_common.localization import get_locale


class ConverterForm(FormNode):
    USE_SCROLLVIEW = False
    FIELD__average = create_value_field(IntNode, get_locale("mat_converter.label.averaging"), 1000)
    FIELD__lcut = create_value_field(IntNode, get_locale("mat_converter.label.l_cut"), 0)
    FIELD__rcut = create_value_field(IntNode, get_locale("mat_converter.label.r_cut"), 0)