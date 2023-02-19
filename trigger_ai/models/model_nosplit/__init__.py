'''
Model shared for every pmt
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
from .model import create_sequential_classifier
from .default_configuration import DEFAULT_CONF
from ..common import splat_select, plot_offset


class NoSplitModel(ModelWrapper):
    def create_dataset_ydata_for_item(self, y_data_parameters):
        ydata = np.array([0., 0., 0., 0.])
        if y_data_parameters.pmt_bottom_left:
            ydata[0] = 1.0
        if y_data_parameters.pmt_bottom_right:
            ydata[1] = 1.0
        if y_data_parameters.pmt_top_left:
            ydata[2] = 1.0
        if y_data_parameters.pmt_top_right:
            ydata[3] = 1.0
        return ydata

    def trigger(self, x, threshold):
        x_data = sliding_window_view(x, 128, axis=0)
        x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        y_data = self.model.predict(x_data)
        y_data = 1 - np.prod(1 - y_data, axis=1)
        booled = y_data > threshold

        print("R0", booled)
        booled_full = splat_select(booled, 128)
        return booled_full

    def plot_over_data(self, x, start, end, axes):
        x_data = sliding_window_view(x, 128, axis=0)
        x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        y_data: np.ndarray = self.model.predict(x_data)
        xs = np.arange(start, end - 127)
        print("PLOT!")
        plot_offset(axes, xs, y_data[:, 0], 20, "bottom left", "-")
        plot_offset(axes, xs, y_data[:, 1], 22, "bottom right", "--")
        plot_offset(axes, xs, y_data[:, 2], 24, "top left", "-.")
        plot_offset(axes, xs, y_data[:, 3], 26, "top right", ":")

    def get_y_spec(self):
        return tf.TensorSpec(shape=(None, 4), dtype=tf.double)

    def get_y_signature(self, n):
        return n, 4

class IndependentGetter(LayerSequenceConstructor):
    DISPLAY_NAME = get_locale("models.splitmerge.independent")

    def get_data(self):
        return super().get_data(), super().get_data(), super().get_data(), super().get_data()


class NoSplitModelForm(FormNode):
    DEFAULT_VALUE = DEFAULT_CONF
    DISPLAY_NAME = "NoSplit"
    FIELD__common = create_value_field(LayerSequenceConstructor, get_locale("models.splitmerge.common"))

    def get_data(self):
        data = super().get_data()
        model = create_sequential_classifier(data["common"])
        return NoSplitModel(model)


NoSplitModel.MODEL_FORM = NoSplitModelForm
