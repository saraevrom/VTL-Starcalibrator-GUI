from vtl_common.common_GUI import TkDictForm
from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode, FloatNode, StringNode, ComboNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from .parameters_defs import PARAMETERS_DEFINITION

class MainParametersForm(FormNode):
    pass

for par_name, par_type, default_value in PARAMETERS_DEFINITION:
    setattr(MainParametersForm,
            "FIELD__"+par_name,
            create_value_field(par_type,
                               par_name,
                               default_value)
            )


def localize_fields():
    from vtl_common.localization import get_locale
    for par_name, par_type, default_value in PARAMETERS_DEFINITION:
        getattr(MainParametersForm,
                "FIELD__" + par_name).DISPLAY_NAME = get_locale("app.parameters."+par_name)

