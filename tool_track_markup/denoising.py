import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from parameters import NPROC
from multiprocessing import Pool
import numba as nb

BATCH = 1000

def divide_multidim(a,b):
    #print("Incoming data shape", a.shape)
    #print("Incoming divider shape", b.shape)
    if len(a.shape)>1:
        res = a/b
        if a.shape != b.shape:
            res[:,b==0] = 0
        else:
            res[b==0] = 0
        return res
    elif hasattr(b,"shape") :
        res = a/b
        res[b==0] = 0
        return res
    elif b==0:
        return np.zeros(a.shape)
    else:
        return a/b


#numba aka gotta go fast
@nb.njit()
def sliding_std(data, window_size):
    output_shape = data.shape
    #output_shape[0] = output_shape[0]-window_size+1
    res_array = np.zeros(output_shape)
    for i in range(output_shape[0]-window_size+1):
        mean = np.zeros(data.shape[1:])
        meansq = np.zeros(data.shape[1:])
        for j in range(i,i+window_size):
            mean += data[j]
            meansq += data[j]**2

        #meansq = np.sum(frame**2, axis=0)/window_size
        #mean = np.sum(frame, axis=0)/window_size
        res_array[i] = np.sqrt(meansq/window_size-(mean/window_size)**2)
    return res_array[:output_shape[0]-window_size+1]


@nb.njit()
def antiflash(data):
    data1 = np.zeros(data.shape)
    for i in range(data.shape[0]):
        data1[i] = data[i] - np.median(data[i])
    return data1

def reduce_noise(data,sliding_win):
    if sliding_win>=data.shape[0]:
        std = np.std(data,axis=0)
        return divide_multidim(data, std)
    else:
        #slider = sliding_window_view(data, window_shape=sliding_win, axis=0)
        #slided_std = [np.std(slider[i], axis=-1) for i in range(slider.shape[0])]
        # batches = []
        # for i in range(0,slider.shape[0],BATCH):
        #     batch_start = i
        #     batch_end = min(i+BATCH, slider.shape[0])
        #     batches.append(np.std(slider[batch_start:batch_end], axis=-1))
        # slided_std = np.concatenate(batches)

        #slided_std = np.array(slided_std)
        #slided_std = sliding_std(slider)

        #slided_std = np.std(slider, axis=-1)  #Somehow requires lot of memory
        slided_std = sliding_std(data,sliding_win)
        lower_bound = sliding_win//2 # sliding window can be odd
        upper_bound = lower_bound+slided_std.shape[0]
        ret_data = np.zeros(data.shape)
        ret_data[lower_bound:upper_bound] = divide_multidim(data[lower_bound:upper_bound], slided_std)
        ret_data[:lower_bound] = divide_multidim(data[:lower_bound], slided_std[0])
        ret_data[upper_bound:] = divide_multidim(data[upper_bound:], slided_std[-1])
        return ret_data