from vtl_common.common_GUI.tk_forms_assist import FormNode, FloatNode, AlternatingNode
from vtl_common.localization import get_locale
from .sampling import SamplerConstant, SamplerUniform, SamplerGauss, SamplerLaplace
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field

class Constant(FloatNode):
    DISPLAY_NAME = get_locale("teacher.advform.constant")
    def get_data(self):
        data = super().get_data()
        return SamplerConstant(data)


class FloatDistributedAlter(AlternatingNode):
    SEL__const = Constant



LowerEnd = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.lower"))
HigherEnd = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.higher"))

Mean = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.mean"))
Stdev = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.stdev"),
                           dict(value=1.0, selection_type="const")
                           )


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


FloatDistributedAlter.SEL__uniform = UniformValue
FloatDistributedAlter.SEL__gauss = GaussValue
FloatDistributedAlter.SEL__laplace = LaplaceValue
