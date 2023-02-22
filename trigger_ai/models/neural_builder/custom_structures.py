from tensorflow import keras
from ..common import apply_layer_array

class Residual(object):
    def __init__(self, layer_array):
        self.layer_array = layer_array

    def __call__(self, inputs):
        normal = apply_layer_array(inputs, self.layer_array)
        return keras.layers.Add()([normal, inputs])
