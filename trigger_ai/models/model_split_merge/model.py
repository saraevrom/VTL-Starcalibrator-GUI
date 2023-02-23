import tensorflow as tf
from ..common import apply_layer_array, create_lambda


def cut_interval(start, end):
    return tf.keras.layers.Lambda(lambda x: x[:, start:end, :, :])

class SingleProcessor(object):
    def __init__(self, independent, common):
        self.pmt_layers = []
        j = 0
        for i in [0, 1, 10, 11]:
            self.pmt_layers.append([create_lambda(i)]+independent[j])
            j += 1

        self.common_layers = [tf.keras.layers.Concatenate()]+common+[tf.keras.layers.Dense(2, activation="softmax")]

    def apply(self, inputs):
        workon = [apply_layer_array(inputs, pmt_layer) for pmt_layer in self.pmt_layers]
        return apply_layer_array(workon, self.common_layers)




