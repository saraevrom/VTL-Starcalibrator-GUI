import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from vtl_common.parameters import NPROC
from multiprocessing import Pool
import numba as nb
from numba import prange

BATCH = 1000


@nb.njit(cache=True)
def window_limiting(index, window, target_length):
    start = index - window // 2
    if start < 0:
        start = 0
    end = start + window
    if end > target_length:
        end = target_length
        start = end - window
    return start, end

@nb.njit(nb.float64[:](nb.float64[:], nb.int64),cache=True)
def sliding_median_single(x, win):
    if win >= x.shape[0]:
        med = np.median(x)
        return np.full(x.shape[0],med)
    res = np.zeros(x.shape[0])
    for i in range(x.shape[0]):
        # start = i-win//2
        # if start<0:
        #     start = 0
        # end = start+win
        # if end >= x.shape[0]:
        #     end = x.shape[0]-1
        #     start = end - win
        start, end = window_limiting(i, win, x.shape[0])
        res[i] = np.median(x[start:end])
    return res


@nb.njit(nb.float64[:, :, :](nb.float64[:, :, :], nb.int64), parallel=True,cache=True)
def sliding_median_pixels(x, win):
    res = np.zeros(x.shape)
    for i in nb.prange(x.shape[1]):
        for j in nb.prange(x.shape[1]):
            res[:, i, j] = sliding_median_single(x[:,i,j],win)
    return res


@nb.njit(nb.float64[:, :, :](nb.float64[:, :, :], nb.float64[:, :]),cache=True)
def divide_multidim_3to2(a, b):
    res = np.zeros(a.shape)
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            for k in range(a.shape[2]):
                if b[j,k] != 0:
                    res[i, j, k] = a[i, j, k]/b[j, k]

    return res


@nb.njit(nb.float64[:, :, :](nb.float64[:, :, :], nb.float64[:, :, :]),cache=True)
def divide_multidim_3to3(a, b):
    res = np.zeros(a.shape)
    for i in range(a.shape[0]):
        for j in range(a.shape[1]):
            for k in range(a.shape[2]):
                if b[i, j, k] != 0:
                    res[i, j, k] = a[i, j, k]/b[i, j, k]

    return res


@nb.njit(parallel=True,cache=True)
def sliding_std(src, win):
    meansq_array = np.zeros(src.shape)
    sqmean_array = np.zeros(src.shape)
    lhalf = win//2
    for j in range(win):
        for i in prange(src.shape[0]):
            ti = i*1  # Otherwise "overwrite parallel index" error will occur...
            if ti < lhalf:
                ti = lhalf  # ...here
            elif ti > src.shape[0]-win+lhalf:
                ti = src.shape[0]-win+lhalf
            meansq_array[i] += src[ti-lhalf+j]**2
            sqmean_array[i] += src[ti-lhalf+j]
    return np.sqrt(meansq_array / win - (sqmean_array / win)**2)

#numba aka gotta go fast
@nb.njit(cache=True)
def sliding_std_old(data, window_size):
    output_shape = data.shape
    #output_shape[0] = output_shape[0]-window_size+1
    res_array = np.zeros(output_shape)
    for i in range(output_shape[0]-window_size+1):
        mean = np.zeros(data.shape[1:])
        meansq = np.zeros(data.shape[1:])
        for j in range(i, i+window_size):
            mean += data[j]
            meansq += data[j]**2

        #meansq = np.sum(frame**2, axis=0)/window_size
        #mean = np.sum(frame, axis=0)/window_size
        res_array[i] = np.sqrt(meansq/window_size-(mean/window_size)**2)
    return res_array[:output_shape[0]-window_size+1]


@nb.njit(cache=True)
def sliding_robust_dev_centered(data, window_size):
    return sliding_median_pixels(np.abs(data), window_size)


@nb.njit(cache=True)
def antiflash(data):
    data1 = np.zeros(data.shape)
    for i in range(data.shape[0]):
        data1[i] = data[i] - np.median(data[i])
    return data1


@nb.njit(cache=True)
def antiflash_single(part_data, full_data):
    data1 = np.zeros(part_data.shape)
    for i in range(part_data.shape[0]):
        data1[i] = part_data[i] - np.median(full_data[i])
    return data1


@nb.njit(nb.float64[:, :](nb.float64[:, :, :]),cache=True)
def nb_std0(data):
    '''
    apply std along axis 0
    :param data:
    :return:
    '''
    res = np.zeros(shape=(data.shape[1], data.shape[2]))
    for i in range(data.shape[1]):
        for j in range(data.shape[2]):
            res[i, j] = np.std(data[:, i, j])
    return res


@nb.njit(cache=True)
def reduce_noise(data,sliding_win):
    if sliding_win>=data.shape[0]:
        std = nb_std0(data)
        return divide_multidim_3to2(data, std)
    else:
        std = sliding_std(data, sliding_win)
        ret_data = divide_multidim_3to3(data, std)
        return ret_data


@nb.njit(cache=True)
def reduce_noise_robust(data, sliding_win):
    std = sliding_robust_dev_centered(data, sliding_win)*(np.pi/2)**0.5
    ret_data = divide_multidim_3to3(data, std)
    return ret_data


@nb.njit(parallel=True,cache=True)
def moving_average_edged(src, win):
    res_array = np.zeros(src.shape)
    lhalf = win//2
    for j in range(win):
        for i in prange(src.shape[0]):
            ti = i*1  # Otherwise "overwrite parallel index" error will occur...
            if ti < lhalf:
                ti = lhalf  # ...here
            elif ti > src.shape[0]-win+lhalf:
                ti = src.shape[0]-win+lhalf
            res_array[i] += src[ti-lhalf+j]
    return res_array / win




@nb.njit(cache=True)
def mean_by_axis(src, axis=0):
    summed = np.sum(src, axis=axis)
    return summed/src.shape[0]



@nb.njit(cache=True)
def moving_average_subtract(src, win):
    if src.shape[0] >= win:
        average = moving_average_edged(src, win)
        return src - average
    else:
        return src - mean_by_axis(src, axis=0)

@nb.njit(cache=True)
def moving_median_subtract(src, win):
    average = sliding_median_pixels(src, win)
    return src - average
