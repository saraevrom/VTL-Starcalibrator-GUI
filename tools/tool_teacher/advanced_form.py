from common_GUI.tk_forms_assist import FormNode, FloatNode, AlternatingNode, IntNode
from common_GUI.tk_forms_assist import BoolNode
from common_GUI.tk_forms_assist.factory import create_value_field, create_label
from localization import get_locale
from .sampling import SamplerConstant, SamplerRange
from .parameters_processing import Augmenter, DualProcessing, SignalModifier, LearnParameters

#Constant = create_value_field(FloatNode, get_locale("teacher.advform.constant"))
class Constant(FloatNode):
    DISPLAY_NAME = get_locale("teacher.advform.constant")
    def get_data(self):
        data = super().get_data()
        return SamplerConstant(data)


LowerEnd = create_value_field(FloatNode, get_locale("teacher.advform.lower"))
HigherEnd = create_value_field(FloatNode, get_locale("teacher.advform.higher"))


class RangedValue(FormNode):
    DISPLAY_NAME = get_locale("teacher.advform.range")
    FIELD__low = LowerEnd
    FIELD__high = HigherEnd
    USE_SCROLLVIEW = False

    def get_data(self):
        raw_data = super().get_data()
        l = raw_data["low"]
        h = raw_data["high"]
        return SamplerRange(l, h)


class FloatDistributedAlter(AlternatingNode):
    SEL__const = Constant
    SEL__uniform = RangedValue


class IntOption(AlternatingNode):
    SEL__none = create_label(get_locale("teacher.advform.none"))
    SEL__const = create_value_field(IntNode, get_locale("teacher.advform.constant"))
    USE_SCROLLVIEW = False





def create_dual(shared_field, common_title, title_master, title_slave):
    class MasterField(shared_field):
        DISPLAY_NAME = title_master

    class IndependentSlaveField(shared_field):
        DISPLAY_NAME = get_locale("teacher.advform.parameters")

    class SlaveFieldAlter(AlternatingNode):
        DISPLAY_NAME = title_slave
        SEL__same = create_label(get_locale("teacher.advform.same"))
        SEL__independent = IndependentSlaveField

    class DualForm(FormNode):
        DISPLAY_NAME = common_title
        FIELD__master = MasterField
        FIELD__slave = SlaveFieldAlter
        USE_SCROLLVIEW = False

        def get_data(self):
            data = super().get_data()

            return DualProcessing(data["master"], data["slave"])

    return DualForm

class Augmentation(FormNode):
    USE_SCROLLVIEW = False
    FIELD__use_transpose = create_value_field(BoolNode,
                                                     get_locale("teacher.form.augmentation.use_transpose"), True)
    FIELD__use_reverse = create_value_field(BoolNode,
                                                   get_locale("teacher.form.augmentation.use_reverse"), True)

    def get_data(self):
        data = super().get_data()
        return Augmenter(**data)

class ProcessingSubform(FormNode):
    USE_SCROLLVIEW = False
    FIELD__multiplier = create_value_field(FloatDistributedAlter, get_locale("teacher.advform.multiplier"))
    DEFAULT_VALUE = {
        "multiplier":{
            "selection_type":"const",
            "value":1.0
        }
    }

    def get_data(self):
        data = super().get_data()
        return SignalModifier(**data)

class SettingForm(FormNode):
    FIELD__label_dataset_parameters = create_label(get_locale("teacher.form.separator.dataset_parameters"), True)
    FIELD__modification = create_dual(ProcessingSubform,
                                      get_locale("teacher.form.dataset_modification"),
                                      get_locale("teacher.status.msg_fg"),
                                      get_locale("teacher.status.msg_it")
                                      )
    FIELD__augment = create_dual(Augmentation,
                                 get_locale("teacher.form.dataset_augmentation"),
                                 get_locale("teacher.status.msg_fg"),
                                 get_locale("teacher.status.msg_it")
                                 )
    FIELD__label_teaching = create_label(get_locale("teacher.form.separator.model_teaching"), True)
    FIELD__epochs = create_value_field(IntNode, get_locale("teacher.form.epochs"), 10)
    FIELD__steps_per_epoch = create_value_field(IntNode, get_locale("teacher.form.steps_per_epoch"), 100)
    FIELD__batch_size = create_value_field(IntNode, get_locale("teacher.form.batch_size"), 32)
    FIELD__workers = create_value_field(IntNode, get_locale("teacher.form.workers"), 1)

    def get_data(self):
        data = super().get_data()
        return LearnParameters(data)