from vtl_common.common_GUI.tk_forms_assist import FormNode, FloatNode, AlternatingNode
from vtl_common.localization import get_locale
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from .noising import FloatDistributedAlter
from .parameters_processing import Appliance


class SignalModifier(Appliance):
    def __init__(self, multiplier):
        self.multiplier = multiplier

    def apply(self, data, rng):
        return self.multiplier.sample(rng)*data


class PostProcessor(Appliance):
    def __init__(self, offset):
        self.offset = offset

    def apply(self, data, rng):
        return self.offset.sample(rng, data.shape)+data

class ProcessingSubform(FormNode):
    USE_SCROLLVIEW = False
    FIELD__multiplier = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.multiplier"))
    DEFAULT_VALUE = {
        "multiplier": {
            "selection_type": "const",
            "value": 1.0
        },
    }

    def get_data(self):
        data = super().get_data()
        return SignalModifier(**data)

class PostprocessingSubform(FormNode):
    USE_SCROLLVIEW = False
    FIELD__offset = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.multiplier"))
    DEFAULT_VALUE = {
        "multiplier": {
            "selection_type": "const",
            "value": 0.0
        }
    }

    def get_data(self):
        data = super().get_data()
        return PostProcessor(**data)