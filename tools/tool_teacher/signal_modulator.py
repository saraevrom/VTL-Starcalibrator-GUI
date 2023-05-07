from vtl_common.common_GUI.tk_forms_assist import FormNode
from vtl_common.localization import get_locale
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field, kwarg_builder
from noise.noising import FloatDistributedAlter
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
        if len(data.shape)<=3:
            return self.offset.sample(rng, data.shape)+data
        else:
            addition = self.offset.sample(rng, data.shape[:3])
            dat1 = data.copy()
            dat1[:, :, :, 0] = dat1[:, :, :, 0] + addition
            dat1[:, :, :, 1] = dat1[:, :, :, 1] + addition
            return dat1

@kwarg_builder(SignalModifier)
class ProcessingSubform(FormNode):
    USE_SCROLLVIEW = False
    FIELD__multiplier = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.multiplier"))
    DEFAULT_VALUE = {
        "multiplier": {
            "selection_type": "const",
            "value": 1.0
        },
    }

@kwarg_builder(PostProcessor)
class PostprocessingSubform(FormNode):
    USE_SCROLLVIEW = False
    FIELD__offset = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.offset"))
    DEFAULT_VALUE = {
        "offset": {
            "selection_type": "const",
            "value": 0.0
        }
    }