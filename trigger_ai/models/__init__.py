#from .model_split_merge import SplitMergeModel
#from .model_splitted import SplitedModel
#from .model_nosplit import NoSplitModel
# ^^^ OBSOLETE

from .model_universal import UniversalModelForm
from vtl_common.common_GUI.tk_forms_assist import FormNode, AlternatingNode
from vtl_common.localization import get_locale


class ModelBuilderAlter(AlternatingNode):
    DISPLAY_NAME = get_locale("app.model_builder.model")
    #SEL__split_merge = SplitMergeModel.MODEL_FORM
    #SEL__splited = SplitedModel.MODEL_FORM
    #SEL__nosplit = NoSplitModel.MODEL_FORM
    SEL__universal = UniversalModelForm


class ModelBuilder(FormNode):
    FIELD__model = ModelBuilderAlter

    def get_data(self):
        data = super().get_data()
        return data["model"]

