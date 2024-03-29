from vtl_common.common_GUI.tk_forms_assist import FormNode, FloatNode, IntNode
from vtl_common.common_GUI.tk_forms_assist import BoolNode, OptionNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field, create_label, kwarg_builder
from vtl_common.localization import get_locale
from .parameters_processing import Augmenter, DualProcessing, LearnParameters
from preprocessing import DataPreProcessorField
from .signal_modulator import ProcessingSubform, PostprocessingSubform
from .track_generator import TrackGeneratorField, GeneratorArray

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

@kwarg_builder(Augmenter)
class Augmentation(FormNode):
    USE_SCROLLVIEW = False
    FIELD__use_transpose = create_value_field(BoolNode,
                                                     get_locale("teacher.form.augmentation.use_transpose"), True)
    FIELD__use_reverse = create_value_field(BoolNode,
                                                   get_locale("teacher.form.augmentation.use_reverse"), True)


class PregenerateDataset(OptionNode):
    DISPLAY_NAME = get_locale("teacher.form.pregenerate_dataset")
    ITEM_TYPE = create_value_field(IntNode, get_locale("teacher.advform.amount"), 1000)
    DEFAULT_VALUE = None


class ProbeParameters(FormNode):
    DISPLAY_NAME = get_locale("teacher.form.probing")
    FIELD__frame_size = create_value_field(IntNode, get_locale("teacher.form.probing.size"), 128)


class TrackSuppressorBackground(OptionNode):
    DISPLAY_NAME = get_locale("teacher.form.track_suppress")
    ITEM_TYPE = create_value_field(IntNode,"teacher.form.track_suppress.threshold", 1000)

class SettingForm(FormNode):
    FIELD__label_dataset_parameters = create_label(get_locale("teacher.form.separator.dataset_parameters"), True)
    FIELD__preprocessing = DataPreProcessorField
    FIELD__track_suppression = TrackSuppressorBackground
    FIELD__artificial_interference = create_value_field(BoolNode,
                                                        get_locale("teacher.form.artificial_interference"), False)
    FIELD__quick_track_probability = create_value_field(FloatNode,
                                                        get_locale("teacher.form.quick_track_probability"), 0.5)
    FIELD__quick_track_attempts = create_value_field(IntNode,
                                                     get_locale("teacher.form.quick_track_attempts"), 5)
    FIELD__flash_probability = create_value_field(FloatNode,
                                                  get_locale("teacher.form.flash_probability"), 0.0)

    #FIELD__shift_threshold = create_value_field(IntNode, get_locale("teacher.form.shift_allow_threshold"), 64)
    FIELD__flash_maxsize = create_value_field(IntNode, get_locale("teacher.form.flash_maxsize"), 10)
    FIELD__flash_attempts = create_value_field(IntNode, get_locale("teacher.form.flash_attempts"), 0)

    FIELD__trackgen = TrackGeneratorField
    FIELD__false_track_probability = create_value_field(FloatNode, get_locale("teacher.form.false_track_probability"), 0.5)
    FIELD__false_track_gen = create_value_field(GeneratorArray,get_locale("teacher.form.trackgen_false"))
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

    FIELD__postprocess = create_value_field(PostprocessingSubform, get_locale("teacher.advform.offset"))
    FIELD__label_teaching = create_label(get_locale("teacher.form.separator.model_teaching"), True)
    FIELD__seed = create_value_field(IntNode, get_locale("teacher.form.seed"), 42)
    FIELD__track_probability = create_value_field(FloatNode, get_locale("teacher.form.track_probability"), 0.9375)
    FIELD__epochs = create_value_field(IntNode, get_locale("teacher.form.epochs"), 1)
    FIELD__steps_per_epoch = create_value_field(IntNode, get_locale("teacher.form.steps_per_epoch"), 10)
    FIELD__batch_size = create_value_field(IntNode, get_locale("teacher.form.batch_size"), 32)
    FIELD__workers = create_value_field(IntNode, get_locale("teacher.form.workers"), 1)
    FIELD__fastcache = create_value_field(BoolNode, get_locale("teacher.form.fastcache"), False)
    FIELD__pregenerate = PregenerateDataset
    FIELD__probe_params = ProbeParameters

    def get_data(self):
        data = super().get_data()
        return LearnParameters(data)