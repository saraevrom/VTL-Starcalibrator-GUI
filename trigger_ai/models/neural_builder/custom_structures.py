from tensorflow import keras
from ..common import apply_layer_array, create_lambda
import tensorflow as tf

class Residual(object):
    def __init__(self, main, shortcut):
        self.main = main
        self.shortcut = shortcut
        self._known_inputs = None

    def __call__(self, inputs):
        normal = apply_layer_array(inputs, self.main)
        shortcut = apply_layer_array(inputs, self.shortcut)
        self._known_inputs = inputs
        return keras.layers.Add()([normal, shortcut])

    @property
    def output_shape(self):
        assert self._known_inputs is not None
        if self.shortcut:
            sshape = self.shortcut[-1].output_shape
        else:
            sshape = tuple(self._known_inputs.shape)
        if self.main:
            mshape = self.main[-1].output_shape
        else:
            mshape =  tuple(self._known_inputs.shape)

        assert sshape == mshape
        return sshape

class TrainableScaling(keras.layers.Layer):
    def __init__(self, use_offset):
        super().__init__()
        self.use_offset = use_offset
        self.b = None
        self.w = None

    def build(self, input_shape):
        self.w = self.add_weight(shape=input_shape[1:], initializer="random_normal",
            trainable=True)
        if self.use_offset:
            self.b = self.add_weight(shape=input_shape[1:], initializer="random_normal",
                trainable=True)

    def call(self, inputs, *args, **kwargs):
        if self.use_offset:
            return self.w*inputs + self.b
        else:
            return self.w*inputs


class PMTSplit(object):
    def __init__(self, pmt_tuple):
        self.pmt_layers = []
        j = 0
        for i in [0, 10, 1, 11]:
            self.pmt_layers.append(
                [create_lambda(i)] + pmt_tuple[j] + [tf.keras.layers.Dense(1, activation="sigmoid")])
            j += 1
        self.cat = tf.keras.layers.Concatenate()

    def __call__(self, inputs):
        workon = [apply_layer_array(inputs, pmt_layer) for pmt_layer in self.pmt_layers]
        return self.cat(workon)

    @property
    def output_shape(self):
        return self.cat.output_shape
