import tensorflow as tf

def create_lambda(index, *args, **kwrags):
    if index==0: # bottom left
        return tf.keras.layers.Lambda(lambda x: x[:, :, :8, :8], *args, **kwrags)
    elif index==1: # top left
        return tf.keras.layers.Lambda(lambda x: x[:, :, :8, 8:], *args, **kwrags)
    elif index==10: # bottom right
        return tf.keras.layers.Lambda(lambda x: x[:, :, 8:, :8], *args, **kwrags)
    elif index==11: # top right
        return tf.keras.layers.Lambda(lambda x: x[:, :, 8:, 8:], *args, **kwrags)


def cut_interval(start, end):
    return tf.keras.layers.Lambda(lambda x: x[:, start:end, :, :])

def apply_layer_array(inputs, layer_array):
    workon = layer_array[0](inputs)
    for layer in layer_array[1:]:
        workon = layer(workon)
    return workon

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




