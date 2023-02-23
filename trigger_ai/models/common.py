import numpy as np
import numba as nb
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

@nb.njit
def splat_select(bool_arg, window):
    result_arr = np.full(bool_arg.shape[0] + window - 1, False)
    for i in range(bool_arg.shape[0]):
        result_arr[i:i + window] = np.logical_or(bool_arg[i], result_arr[i:i + window])
    return result_arr

def plot_offset(axes, xs, ys, offset, label, style):
    axes.plot(xs, ys + offset, style, color="black", label=label)
    axes.fill_between(xs, offset, ys + offset, color="gray")

def apply_layer_array(inputs, layer_array):
    if not layer_array:
        return inputs
    workon = layer_array[0](inputs)
    for layer in layer_array[1:]:
        workon = layer(workon)
    return workon