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
    def __init__(self, conv_layers, dense_count):
        self.pmt_layers = []
        for i in [0, 1, 10, 11]:
            self.pmt_layers.append([
                create_lambda(i),
                #tf.keras.layers.LayerNormalization(axis=1),
                tf.keras.layers.Lambda(lambda x: tf.expand_dims(x, -1)),
                tf.keras.layers.Conv3D(1, (8, 3, 3)),
                tf.keras.layers.MaxPooling3D(pool_size=(16, 2, 2)),
                tf.keras.layers.Flatten()
            ])

        self.common_layers = [
            tf.keras.layers.Concatenate(),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(2, activation="softmax")
        ]

    def apply(self, inputs):
        workon = [apply_layer_array(inputs, pmt_layer) for pmt_layer in self.pmt_layers]
        return apply_layer_array(workon, self.common_layers)


def create_trigger_model(frames, conv_outputs=1, dense_count=16, slider=20):
    inputs = tf.keras.Input(shape=(frames, 16, 16))
    print(inputs.shape)
    processor = SingleProcessor(conv_layers=conv_outputs, dense_count=dense_count)
    output = processor.apply(inputs)
    # slided = []
    # for start_index in range(frames-slider+1):
    #     timecut = cut_interval(start_index, start_index+slider)(inputs)
    #     slided.append(processor.apply(timecut))
    #
    # merged = tf.keras.layers.Concatenate()(slided)
    # output = tf.keras.layers.Dense(2, activation="softmax")(merged)

    return tf.keras.Model(inputs, output)




if __name__=="__main__":
    model = create_trigger_model(128)
    model.summary()