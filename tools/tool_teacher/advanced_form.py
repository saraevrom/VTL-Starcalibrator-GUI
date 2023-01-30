from common_GUI.tk_forms_assist import FormNode, FloatNode, AlternatingNode, IntNode
from common_GUI.tk_forms_assist import BoolNode, OptionNode
from common_GUI.tk_forms_assist.factory import create_value_field, create_label
from localization import get_locale
from .parameters_processing import Augmenter, DualProcessing, LearnParameters
from preprocessing import DataPreProcessorForm
from .signal_modulator import ProcessingSubform


def create_dual(shared_field, common_title, title_master, title_slave):
    class MasterField(shared_field):
        DISPLAY_NAME = title_master

    class IndependentSlaveField(shared_field):
        DISPLAY_NAME = get_locale("teacher.advform.parameters")

    class SlaveFieldAlter(OptionNode):
        DISPLAY_NAME = title_slave
        DEFAULT_VALUE = None
        ITEM_TYPE = IndependentSlaveField
        #SEL__same = create_label(get_locale("teacher.advform.same"))
        #SEL__independent = IndependentSlaveField

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


class PregenerateDataset(OptionNode):
    DISPLAY_NAME = get_locale("teacher.form.pregenerate_dataset")
    ITEM_TYPE = create_value_field(IntNode, get_locale("teacher.advform.amount"), 40000)
    DEFAULT_VALUE = None

class SettingForm(FormNode):
    FIELD__label_dataset_parameters = create_label(get_locale("teacher.form.separator.dataset_parameters"), True)
    FIELD__preprocessing = DataPreProcessorForm
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
    FIELD__fastcache = create_value_field(BoolNode, get_locale("teacher.form.fastcache"), False)
    FIELD__pregenerate = PregenerateDataset

    def get_data(self):
        data = super().get_data()
        return LearnParameters(data)