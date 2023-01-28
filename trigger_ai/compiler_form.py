
from common_GUI.tk_forms_assist import *
from localization import get_locale
import inspect
import tensorflow.keras.optimizers as optimizers
import tensorflow.keras.optimizers.experimental as optimizers_exp
import tensorflow.keras.losses as losses
import tensorflow.keras.metrics as metrics


def get_subclasses(source_module, required_class_name):
    testclass = getattr(source_module, required_class_name)
    return list(filter(lambda x: x != required_class_name and
                                 inspect.isclass(getattr(source_module,x)) and
                                 issubclass(getattr(source_module,x), testclass), dir(source_module)))


def attach_options(target, source_module, typemap, required_class_name):

    classes = get_subclasses(source_module, required_class_name)
    for opt in classes:
        optclass = getattr(source_module, opt)
        setattr(target, "SEL__" + opt, create_parameters_lookup(optclass, typemap))


class DefaultNode(LabelNode):
    DISPLAY_NAME = get_locale("app.model.form.set_to_default")

CLASS_MAP = {
    int: IntNode,
    float: FloatNode,
    str: StringNode,
    bool: BoolNode
}

def create_parameters_lookup(func, typemap):
    args, _, _, defaults, _, _, _ = inspect.getfullargspec(func)
    args = args[1:]
    assert len(args) == len(defaults)
    class ResultForm(FormNode):
        DISPLAY_NAME = "Parameters"
        USE_SCROLLVIEW = False

        def get_data(self):
            data = super().get_data()
            return func(**data)

    for i in range(len(args)):
        name = args[i]
        default = defaults[i]
        if default is None:
            if name in typemap.keys():
                actual_type = typemap[name]
                if actual_type in CLASS_MAP.keys():
                    class ArgField(CLASS_MAP[actual_type]):
                        DISPLAY_NAME = get_locale("app.model.form.value")

                    class Option(AlternatingNode):
                        DISPLAY_NAME = name
                        SEL__auto = DefaultNode
                        SEL__manual = ArgField

                    setattr(ResultForm, "FIELD__" + name, Option)
        else:
            class ArgField(CLASS_MAP[type(default)]):
                DISPLAY_NAME = name
                DEFAULT_VALUE = default

            setattr(ResultForm, "FIELD__"+name, ArgField)
    return ResultForm


OPTIMIZER_MAP = {
        "weight_decay": float,
        "ema_overwrite_frequency": int,
        "clipnorm": float,
        "global_clipnorm": float,
        "clipvalue": float
    }

class OptimizerData(AlternatingNode):
    DISPLAY_NAME = get_locale("app.model.form.optimizer")
    DEFAULT_VALUE = {"selection_type": "Adam"}

class LossData(AlternatingNode):
    DISPLAY_NAME = get_locale("app.model.form.loss")
    DEFAULT_VALUE = {"selection_type": "CategoricalCrossentropy"}


class MetricDataSingle(ComboNode):
    DISPLAY_NAME = get_locale("app.model.form.metric")
    DEFAULT_VALUE = "Accuracy"
    SELECTION_READONLY = True
    VALUES = get_subclasses(metrics, "Metric")

    def get_data(self):
        index_data = super().get_data()
        return getattr(metrics, index_data)()

class MetricData(ArrayNode):
    DISPLAY_NAME = get_locale("app.model.form.metrics")
    DEFAULT_VALUE = []
    ITEM_TYPE = MetricDataSingle


attach_options(OptimizerData, optimizers, OPTIMIZER_MAP, "Optimizer")
attach_options(OptimizerData, optimizers_exp, OPTIMIZER_MAP, "Optimizer")

attach_options(LossData, losses, dict(), "Loss")

class CompileForm(FormNode):
    FIELD__optimizer = OptimizerData
    FIELD__loss = LossData
    FIELD__metrics = MetricData