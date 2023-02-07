'''
Model with independent for every pmt and common layers
'''
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from ..model_wrapper import ModelWrapper


from common_GUI.tk_forms_assist import FormNode
from common_GUI.tk_forms_assist.factory import create_value_field
from ..neural_builder.form_elements import LayerSequenceConstructor
from localization import get_locale
import tensorflow as tf
from .model import SingleProcessor
from .default_configuration import DEFAULT_CONF


class SplitMergeModel(ModelWrapper):
    def create_dataset_ydata_for_item(self, y_data_parameters):
        if y_data_parameters.has_track():
            return np.array([0., 1.])
        else:
            return np.array([1., 0.])

    def trigger(self, x, threshold):
        x_data = sliding_window_view(x, 128, axis=0)
        x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        y_data = self.model.predict(x)
        y_data = y_data[:, 1]
        return y_data > threshold

    def plot_over_data(self, x, start, end, axes):
        x_data = sliding_window_view(x, 128, axis=0)
        x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        y_data: np.ndarray = self.model.predict(x_data)[:, 1]
        xs = np.arange(start, end - 127)
        axes.plot(xs, y_data, color="black")

class SplitMergeForm(FormNode):
    DEFAULT_VALUE = DEFAULT_CONF
    DISPLAY_NAME = "SplitMerge"
    FIELD__independent = create_value_field(LayerSequenceConstructor, get_locale("models.splitmerge.independent"))
    FIELD__common = create_value_field(LayerSequenceConstructor, get_locale("models.splitmerge.common"))

    def get_data(self):
        data = super().get_data()
        inputs = tf.keras.Input(shape=(128, 16, 16))
        processor = SingleProcessor(**data)
        output = processor.apply(inputs)
        model = tf.keras.Model(inputs, output)
        return SplitMergeModel(model)


SplitMergeModel.MODEL_FORM = SplitMergeForm

