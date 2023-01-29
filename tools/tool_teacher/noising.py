from common_GUI.tk_forms_assist import FormNode, FloatNode, AlternatingNode
from localization import get_locale
from .sampling import SamplerConstant, SamplerUniform, SamplerGauss, SamplerLaplace
from common_GUI.tk_forms_assist.factory import create_value_field

class Constant(FloatNode):
    DISPLAY_NAME = get_locale("teacher.advform.constant")
    def get_data(self):
        data = super().get_data()
        return SamplerConstant(data)


LowerEnd = create_value_field(FloatNode, get_locale("teacher.advform.lower"))
HigherEnd = create_value_field(FloatNode, get_locale("teacher.advform.higher"))

Mean = create_value_field(FloatNode, get_locale("teacher.advform.mean"))
Stdev = create_value_field(FloatNode, get_locale("teacher.advform.stdev"), 1.0)



class UniformValue(FormNode):
    DISPLAY_NAME = get_locale("teacher.advform.uniform")
    FIELD__low = LowerEnd
    FIELD__high = HigherEnd
    USE_SCROLLVIEW = False

    def get_data(self):
        raw_data = super().get_data()
        l = raw_data["low"]
        h = raw_data["high"]
        return SamplerUniform(l, h)


class DistributedValue(FormNode):
    FIELD__mean = Mean
    FIELD__std = Stdev
    USE_SCROLLVIEW = False

class GaussValue(DistributedValue):
    DISPLAY_NAME = get_locale("teacher.advform.gauss")
    def get_data(self):
        data = super().get_data()
        return SamplerGauss(data["mean"],data["std"])


class LaplaceValue(DistributedValue):
    DISPLAY_NAME = get_locale("teacher.advform.laplace")
    def get_data(self):
        data = super().get_data()
        return SamplerLaplace(data["mean"], data["std"])


class FloatDistributedAlter(AlternatingNode):
    SEL__const = Constant
    SEL__uniform = UniformValue
    SEL__gauss = GaussValue
    SEL__laplace = LaplaceValue