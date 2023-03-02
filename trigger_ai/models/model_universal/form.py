
from common_GUI.tk_forms_assist import FormNode, ComboNode
from common_GUI.tk_forms_assist.factory import create_value_field
from ..neural_builder.form_elements import LayerSequenceConstructor
from localization import get_locale, format_locale
from .model import OUTPUT_TYPES, OUT_SPLIT, OUT_SOFT, OUT_SINGLE_SIGMA, UniversalModel, create_tf_model, OUTPUT_SHAPES
from tkinter import messagebox
import tensorflow as tf
from .default_values import DEFAULT_VALUES

class OutputType(ComboNode):
    DISPLAY_NAME = get_locale("models.universal.output_type")
    VALUES = OUTPUT_TYPES
    DEFAULT_VALUE = OUT_SPLIT
    SELECTION_READONLY = True

class UniversalModelForm(FormNode):
    DEFAULT_VALUE = DEFAULT_VALUES
    DISPLAY_NAME = "Universal"
    FIELD__layers = create_value_field(LayerSequenceConstructor, get_locale("models.universal.layers"))
    FIELD__output_mode = OutputType

    def get_data(self):
        data = super().get_data()
        layers = data["layers"]
        mode = data["output_mode"]
        index = OUTPUT_TYPES.index(mode)
        target_shape = OUTPUT_SHAPES[index]
        model = create_tf_model(layers)
        if layers:
            last = layers[-1]
            oshape = last.output_shape[1:]
            print("WWWWW!", oshape)

            fix_layers = target_shape != oshape
        else:
            fix_layers = True
            oshape = "..."

        if fix_layers:
            messagebox.showwarning(title=get_locale("models.universal.shape_warning.title"),
                                   message=format_locale("models.universal.shape_warning.content",
                                                         output=oshape,
                                                         request=target_shape))
            if mode == OUT_SPLIT:
                layers.append(tf.keras.layers.Dense(4, activation="sigmoid"))
            elif mode == OUT_SOFT:
                layers.append(tf.keras.layers.Dense(2, activation="softmax"))
            elif mode == OUT_SINGLE_SIGMA:
                layers.append(tf.keras.layers.Dense(1, activation="sigmoid"))
            else:
                raise RuntimeError("Unknown mode "+mode)
            model = create_tf_model(layers)

            last = layers[-1]
            oshape = last.output_shape[1:]
            assert target_shape == oshape

        add_data = dict(mode=mode)
        return UniversalModel(model=model, additional_params=add_data)