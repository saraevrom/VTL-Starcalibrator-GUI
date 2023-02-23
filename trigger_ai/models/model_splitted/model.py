import tensorflow as tf
from ..common import apply_layer_array, create_lambda



def cut_interval(start, end):
    return tf.keras.layers.Lambda(lambda x: x[:, start:end, :, :])

# Seems to have same structure as split-merge. Probably will be refactored
class SingleProcessor(object):
    def __init__(self, independent):
        self.pmt_layers = []
        j = 0
        for i in [0, 10, 1, 11]:
            self.pmt_layers.append([create_lambda(i)]+independent[j]+[tf.keras.layers.Dense(1, activation="sigmoid")])
            j += 1

        self.common_layers = [tf.keras.layers.Concatenate(),
                              # In case labels are messed up one dense layer fixes issue.
                              # tf.keras.layers.Dense(4, use_bias=False, activation="linear"),
                              tf.keras.layers.Flatten()
                              ]

    def apply(self, inputs):
        workon = [apply_layer_array(inputs, pmt_layer) for pmt_layer in self.pmt_layers]
        return apply_layer_array(workon, self.common_layers)




