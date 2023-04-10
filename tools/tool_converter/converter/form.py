from vtl_common.common_GUI.tk_forms_assist import FormNode, IntNode, ComboNode, AlternatingNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from vtl_common.localization import get_locale
from .cutters import IntervalCutter, CutoffCutter, SliceCutter

class CutoffUnits(ComboNode):
    DISPLAY_NAME = get_locale("mat_converter.label.units")
    SELECTION_READONLY = True
    VALUES = ["GTU", "Frames"]
    DEFAULT_VALUE = "GTU"


class CutoffOption(FormNode):
    DISPLAY_NAME = get_locale("mat_converter.label.mode.cutoff")
    FIELD__at_start = create_value_field(IntNode, get_locale("mat_converter.label.l_cut"), 0)
    FIELD__at_end = create_value_field(IntNode, get_locale("mat_converter.label.r_cut"), 0)

    def get_data(self):
        data = super().get_data()
        return CutoffCutter(**data)


class SliceOption(FormNode):
    DISPLAY_NAME = get_locale("mat_converter.label.mode.slice")
    FIELD__start = create_value_field(IntNode, get_locale("mat_converter.label.cut_start"), 0)
    FIELD__end = create_value_field(IntNode, get_locale("mat_converter.label.cut_end"), -1)

    def get_data(self):
        data = super().get_data()
        return SliceCutter(**data)

class IntervalOption(FormNode):
    DISPLAY_NAME = get_locale("mat_converter.label.mode.interval")
    FIELD__start = create_value_field(IntNode, get_locale("mat_converter.label.cut_start"), 0)
    FIELD__length = create_value_field(IntNode, get_locale("mat_converter.label.length"), 1)

    def get_data(self):
        data = super().get_data()
        return IntervalCutter(**data)

class CuttingAlter(AlternatingNode):
    DISPLAY_NAME = get_locale("mat_converter.label.cut")
    SEL__cutoff = CutoffOption
    SEL__slice = SliceOption
    SEL__interval = IntervalOption


class ConverterForm(FormNode):
    USE_SCROLLVIEW = False
    FIELD__average = create_value_field(IntNode, get_locale("mat_converter.label.averaging"), 1000)
    FIELD__units = CutoffUnits
    FIELD__cutter = CuttingAlter
    # FIELD__lcut = create_value_field(IntNode, get_locale("mat_converter.label.l_cut"), 0)
    # FIELD__rcut = create_value_field(IntNode, get_locale("mat_converter.label.r_cut"), 0)