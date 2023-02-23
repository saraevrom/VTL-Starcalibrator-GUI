from tensorflow import keras
from ..common import apply_layer_array
import tensorflow as tf

class Residual(object):
    def __init__(self, main, shortcut):
        self.main = main
        self.shortcut = shortcut

    def __call__(self, inputs):
        normal = apply_layer_array(inputs, self.main)
        shortcut = apply_layer_array(inputs, self.shortcut)
        return keras.layers.Add()([normal, shortcut])


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