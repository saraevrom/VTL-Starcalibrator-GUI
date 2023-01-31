from common_GUI.tk_forms_assist import *
from common_GUI.tk_forms_assist.factory import create_value_field
from localization import get_locale
import inspect
from .model import create_trigger_model

class DenseActivation(ComboNode):
    DISPLAY_NAME = get_locale("app.model_create.form.dense_activation")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "relu"
    VALUES = list(sorted(["linear", "relu", "sigmoid", "softplus", "softsign", "tanh", "selu", "elu"]))


class NeuralNetworkCreator(FormNode):
    USE_SCROLLVIEW = False
    DISPLAY_NAME = get_locale("app.model_create.form.title")
    FIELD__conv_outputs = create_value_field(IntNode, get_locale("app.model_create.form.conv_outputs"), 1)
    FIELD__conv_X = create_value_field(IntNode, get_locale("app.model_create.form.conv_X"), 3)
    FIELD__conv_Y = create_value_field(IntNode, get_locale("app.model_create.form.conv_Y"), 3)
    FIELD__conv_T = create_value_field(IntNode, get_locale("app.model_create.form.conv_T"), 8)
    FIELD__dense_count = create_value_field(IntNode, get_locale("app.model_create.form.dense_count"), 16)
    FIELD__dense_activation = DenseActivation

    def get_data(self):
        return create_trigger_model(128, **super().get_data())
