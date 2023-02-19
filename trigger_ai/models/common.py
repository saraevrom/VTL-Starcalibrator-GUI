import numpy as np
import numba as nb


@nb.njit
def splat_select(bool_arg, window):
    result_arr = np.full(bool_arg.shape[0] + window - 1, False)
    for i in range(bool_arg.shape[0]):
        result_arr[i:i + window] = np.logical_or(bool_arg[i], result_arr[i:i + window])
    return result_arr

def plot_offset(axes, xs, ys, offset, label, style):
    axes.plot(xs, ys + offset, style, color="black", label=label)
    axes.fill_between(xs, offset, ys + offset, color="gray")