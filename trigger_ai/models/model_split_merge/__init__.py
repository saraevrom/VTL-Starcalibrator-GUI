'''
Model with independent for every pmt and common layers
'''
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from ..model_wrapper import ModelWrapper
import numba as nb

from common_GUI.tk_forms_assist import FormNode
from common_GUI.tk_forms_assist.factory import create_value_field
from ..neural_builder.form_elements import LayerSequenceConstructor
from localization import get_locale
import tensorflow as tf
from .model import SingleProcessor
from .default_configuration import DEFAULT_CONF
from ..common import splat_select


class SplitMergeModel(ModelWrapper):
    def create_dataset_ydata_for_item(self, y_data_parameters):
        if y_data_parameters.has_track():
            return np.array([0., 1.])
        else:
            return np.array([1., 0.])

    def trigger(self, x, threshold):
        x_data = sliding_window_view(x, 128, axis=0)
        x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        y_data = self.model.predict(x_data)
        y_data = y_data[:, 1]
        booled =  y_data > threshold

        print("R0", booled)
        booled_full = splat_select(booled, 128)
        return booled_full

    def plot_over_data(self, x, start, end, axes):
        x_data = sliding_window_view(x, 128, axis=0)
        x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        y_data: np.ndarray = self.model.predict(x_data)[:, 1]
        xs = np.arange(start, end - 127)
        print("PLOT!")
        axes.plot(xs, y_data+20, "-", color="black")

    def get_y_spec(self):
        return tf.TensorSpec(shape=(None, 2), dtype=tf.double)

    def get_y_signature(self, n):
        return n, 2


class IndependentGetter(LayerSequenceConstructor):
    DISPLAY_NAME = get_locale("models.splitmerge.independent")
    
    def get_data(self):
        return super().get_data(), super().get_data(), super().get_data(), super().get_data()

class SplitMergeForm(FormNode):
    DEFAULT_VALUE = DEFAULT_CONF
    DISPLAY_NAME = "SplitMerge"
    FIELD__independent = IndependentGetter
    FIELD__common = create_value_field(LayerSequenceConstructor, get_locale("models.splitmerge.common"))

    def get_data(self):
        data = super().get_data()
        inputs = tf.keras.Input(shape=(128, 16, 16))
        processor = SingleProcessor(**data)
        output = processor.apply(inputs)
        model = tf.keras.Model(inputs, output)
        return SplitMergeModel(model)


SplitMergeModel.MODEL_FORM = SplitMergeForm

