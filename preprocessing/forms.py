from common_GUI.tk_forms_assist import FormNode, BoolNode, OptionNode, IntNode, AlternatingNode
from common_GUI.tk_forms_assist.factory import create_label, create_value_field
from localization import get_locale
from .three_stage_preprocess import DataThreeStagePreProcessor
from .sliding_median_normalizer import SlidingMedianNormalizer

def create_int_option(default_value):
        class IntOptionWrapped(OptionNode):
            SEL__none = create_label(get_locale("app.preprocess.advform.none"))
            ITEM_TYPE = create_value_field(IntNode, get_locale("app.preprocess.advform.win"), default_value)
            DEFAULT_VALUE = default_value

        return IntOptionWrapped


def data_changed(new_dict, reference_dict):
    for i in ["ma_win", "mstd_win", "use_antiflash", "use_robust", "independent_pmt"]:
        if new_dict[i] != reference_dict[i]:
            return True
    return False


def correct_data(new_dict):
    for i in ["ma_win", "mstd_win"]:
        if new_dict[i] is None:
            new_dict[i] = 0

class DataThreeStagesFilter(FormNode):
    USE_SCROLLVIEW = False
    DISPLAY_NAME = get_locale("app.preprocess.form.preprocess.tsf.title")
    FIELD__ma_win = create_value_field(create_int_option(10), get_locale("app.preprocess.form.preprocess.stage1"))
    FIELD__mstd_win = create_value_field(create_int_option(100), get_locale("app.preprocess.form.preprocess.stage2"))
    FIELD__use_antiflash = create_value_field(BoolNode, get_locale("app.preprocess.form.preprocess.stage3"), True)
    FIELD__use_robust = create_value_field(BoolNode, get_locale("app.preprocess.form.preprocess.robust"), False)
    FIELD__independent_pmt = create_value_field(BoolNode,
                                                get_locale("app.preprocess.form.preprocess.independent_pmt"), False)

    def __init__(self):
        super().__init__()
        self.cached_filter = None
        self.cached_settings = None

    def get_data(self):
        raw_data = super().get_data()
        correct_data(raw_data)
        if (self.cached_filter is None) or data_changed(raw_data, self.cached_settings):
            print("FILTER:", raw_data)

            self.cached_filter = DataThreeStagePreProcessor(**raw_data)
            self.cached_settings = raw_data
        return self.cached_filter


# class DataMedianNormForm(FormNode):
#     DISPLAY_NAME = get_locale("app.preprocess.form.preprocess.mn.title")
#     FIELD__median_window = create_value_field(IntNode, get_locale("app.preprocess.advform.win"), 10)
#
#     def get_data(self):
#         raw_data = super().get_data()
#         return SlidingMedianNormalizer(**raw_data)
#
# class DataPreProcessorField(AlternatingNode):
#     DISPLAY_NAME = get_locale("app.preprocess.form.preprocess.title")
#     SEL__three_stages_filter = DataThreeStagesFilter
#     SEL__median_norm = DataMedianNormForm

DataPreProcessorField = DataThreeStagesFilter