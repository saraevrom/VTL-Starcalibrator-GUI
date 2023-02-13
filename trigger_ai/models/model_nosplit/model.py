import tensorflow as tf


def create_sequential_classifier(layers):
    used_layers = [tf.keras.Input(shape=(128, 16, 16))]+layers+[tf.keras.layers.Dense(4, activation="sigmoid")]
    return tf.keras.Sequential(used_layers)



