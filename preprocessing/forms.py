from common_GUI.tk_forms_assist import FormNode, BoolNode, AlternatingNode, IntNode
from common_GUI.tk_forms_assist.factory import create_label, create_value_field
from localization import get_locale
from .data_preprocess import DataPreProcessor

def create_int_option(default_value, none_first=True):
    if none_first:
        class IntOptionWrapped(AlternatingNode):
            SEL__none = create_label(get_locale("app.preprocess.advform.none"))
            SEL__const = create_value_field(IntNode, get_locale("app.preprocess.advform.win"), default_value)
            USE_SCROLLVIEW = False

        return IntOptionWrapped
    else:
        class IntOptionWrapped(AlternatingNode):
            SEL__const = create_value_field(IntNode, get_locale("app.preprocess.advform.win"), default_value)
            SEL__none = create_label(get_locale("app.preprocess.advform.none"))
            USE_SCROLLVIEW = False

        return IntOptionWrapped

class DataPreProcessorForm(FormNode):
    USE_SCROLLVIEW = False
    DISPLAY_NAME = get_locale("app.preprocess.form.preprocess.title")
    FIELD__ma_win = create_value_field(create_int_option(10, False), get_locale("app.preprocess.form.preprocess.stage1"))
    FIELD__mstd_win = create_value_field(create_int_option(100, False), get_locale("app.preprocess.form.preprocess.stage2"))
    FIELD__use_antiflash = create_value_field(BoolNode, get_locale("app.preprocess.form.preprocess.stage3"), True)

    def get_data(self):
        raw_data = super().get_data()
        return DataPreProcessor(**raw_data)