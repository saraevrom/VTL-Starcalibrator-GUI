from common_GUI.tk_forms_assist import FormNode, FloatNode, AlternatingNode
from localization import get_locale
from common_GUI.tk_forms_assist.factory import create_value_field
from .noising import FloatDistributedAlter
from .parameters_processing import Appliance


class SignalModifier(Appliance):
    def __init__(self, multiplier, offset):
        self.multiplier = multiplier
        self.offset = offset

    def apply(self, data):
        return self.multiplier.sample()*data + self.offset.sample(data.shape)


class ProcessingSubform(FormNode):
    USE_SCROLLVIEW = False
    FIELD__multiplier = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.multiplier"))
    FIELD__offset = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.offset"))
    DEFAULT_VALUE = {
        "multiplier": {
            "selection_type": "const",
            "value": 1.0
        },
        "offset": {
            "selection_type": "const",
            "value": 0.0
        }
    }

    def get_data(self):
        data = super().get_data()
        return SignalModifier(**data)