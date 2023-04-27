import numpy as np
import numba as nb
import tensorflow as tf
from preprocessing.denoising import window_limiting

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
def deconvolve_windows(convolved, window):
    result_arr = np.full(convolved.shape[0] + window - 1, 0.0)
    norm_arr = np.full(convolved.shape[0] + window - 1, 0.0)
    for i in range(convolved.shape[0]):
        result_arr[i: i + window] = result_arr[i: i + window] + convolved[i]
        norm_arr[i: i + window] = norm_arr[i: i + window] + 1.0
    #print("SRC:", convolved)
    #print("RES:",result_arr)
    #print("NORM:", norm_arr)
    return result_arr/norm_arr



@nb.njit
def max_arrayscalar(array, scalar):
    res = np.zeros(shape=array.shape)
    for i in range(array.shape[0]):
        if scalar>array[i]:
            res[i] = scalar
        else:
            res[i] = array[i]
    return res

@nb.njit
def deconvolve_windows_max(convolved, window):
    result_arr = np.full(convolved.shape[0] + window - 1, 0.0)
    for i in range(convolved.shape[0]):

        result_arr[i: i + window] = max_arrayscalar(result_arr[i: i + window], convolved[i])
    #print("SRC:", convolved)
    #print("RES:",result_arr)
    #print("NORM:", norm_arr)
    return result_arr

@nb.njit
def expand_window(booled_full, window):
    result_arr = np.full(booled_full.shape[0], False)
    for i in range(booled_full.shape[0]):
        start,end = window_limiting(i, window, booled_full.shape[0])
        result_arr[start:end] = np.logical_or(result_arr[start:end], booled_full[i])
    return result_arr

@nb.njit
def splat_select(bool_arg, window):
    result_arr = np.full(bool_arg.shape[0] + window - 1, False)
    for i in range(bool_arg.shape[0]):
        result_arr[i:i + window] = np.logical_or(bool_arg[i], result_arr[i:i + window])
    return result_arr

def plot_offset(axes, xs, ys, offset, label, style, cutter = None):
    draw_y = deconvolve_windows(ys,128) + offset
    if cutter is not None:
        draw_y = draw_y[cutter]
    print(draw_y)
    axes.plot(xs, draw_y, style, color="black", label=label)
    axes.fill_between(xs, offset, draw_y, color="gray")

def apply_layer_array(inputs, layer_array):
    if not layer_array:
        return inputs
    workon = layer_array[0](inputs)
    for layer in layer_array[1:]:
        workon = layer(workon)
    return workon