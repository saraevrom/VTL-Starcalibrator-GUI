import tensorflow as tf

def create_lambda(index, *args, **kwrags):
    if index==0:
        return tf.keras.layers.Lambda(lambda x: x[:, :, :8, :8], *args, **kwrags)
    elif index==1:
        return tf.keras.layers.Lambda(lambda x: x[:, :, :8, 8:], *args, **kwrags)
    elif index==10:
        return tf.keras.layers.Lambda(lambda x: x[:, :, 8:, :8], *args, **kwrags)
    elif index==11:
        return tf.keras.layers.Lambda(lambda x: x[:, :, 8:, 8:], *args, **kwrags)


def cut_interval(start, end):
    return tf.keras.layers.Lambda(lambda x: x[:, start:end, :, :])

def apply_layer_array(inputs, layer_array):
    workon = layer_array[0](inputs)
    for layer in layer_array[1:]:
        workon = layer(workon)
    return workon

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




