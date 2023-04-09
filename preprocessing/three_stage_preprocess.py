import numpy as np
from .base import Preprocessor
from .denoising import reduce_noise, antiflash, moving_average_subtract, divide_multidim_3to2
from .denoising import  moving_median_subtract, reduce_noise_robust, window_limiting, slice_for_preprocess
from numba.experimental import jitclass
import numba as nb
from numba.core.types.containers import UniTuple
import warnings


@nb.njit(UniTuple(nb.float64, 2)(nb.float64[:,:,:], nb.boolean[:,:]))
def get_noise(signal, broken):
    '''
    gets mean and std from signal[:, np.logical_not(broken)]
    :return:
    '''
    acc_sum = 0
    acc_sqr = 0
    n = 0
    for i in range(signal.shape[0]):
        for j in range(signal.shape[1]):
            for k in range(signal.shape[2]):
                if not broken[j,k]:
                    acc_sum += signal[i, j, k]
                    acc_sqr += signal[i, j, k]**2
                    n += 1
    if n == 0:
        return 0.0, 0.0
    mean = acc_sum/n
    stdev = np.sqrt(acc_sqr/n - mean**2)
    return mean, stdev


@nb.njit()
def noisy(signal, broken):
    mean, stdev = get_noise(signal, broken)
    # res = np.zeros(signal.shape)
    for i in range(signal.shape[0]):
        for j in range(signal.shape[1]):
            for k in range(signal.shape[2]):
                if broken[j, k]:
                    signal[i,j,k] = np.random.normal(mean, stdev)
                else:
                    signal[i,j,k] = signal[i,j,k]
    return signal


#@jitclass()
class DataThreeStagePreProcessor(object):
    # ma_win: nb.int64
    # mstd_win: nb.int64
    # use_antiflash: nb.boolean
    # use_robust: nb.boolean
    # independent_pmt: nb.boolean

    def __init__(self, ma_win=10, mstd_win=100, use_antiflash=True, use_robust=False, independent_pmt=False):
        self.ma_win = ma_win
        self.mstd_win = mstd_win
        self.use_antiflash = use_antiflash
        self.use_robust = use_robust
        self.independent_pmt = independent_pmt

    def get_representation(self):
        res = "Filter:\n"
        off = True
        if self.ma_win != 0:
            res += f"\tMA={self.ma_win}\n"
            off = False
        if self.mstd_win != 0:
            res += f"\tMSTD={self.mstd_win}\n"
            off = False
        if self.use_antiflash:
            res += f"\tAntiflash ON\n"
            off = False
        if off:
            res += f"\tOFF\n"
        else:
            if self.use_robust:
                res += f"\tRobust mode ON\n"
            else:
                res += f"\tRobust mode OFF\n"

            if self.independent_pmt:
                res += "\tIndependent PMT\n"

        return res

    def preprocess_bulk_robust(self, src_in):
        src = src_in.astype(float)
        ma_win = self.ma_win
        mstd_win = self.mstd_win
        use_antiflash = self.use_antiflash
        if ma_win != 0:
            stage1 = moving_median_subtract(src, ma_win)
        else:
            stage1 = src[:]

        if mstd_win != 0:
            stage2 = reduce_noise_robust(stage1, mstd_win)
        else:
            stage2 = stage1[:]

        if use_antiflash:
            stage3 = antiflash(stage2)
        else:
            stage3 = stage2[:]

        return stage3[:]

    def preprocess_bulk_norobust(self, src):

        ma_win = self.ma_win

        mstd_win = self.mstd_win

        use_antiflash = self.use_antiflash

        if ma_win != 0:
            stage1 = moving_average_subtract(src, ma_win)
        else:
            stage1 = src[:]

        if mstd_win != 0:
            stage2 = reduce_noise(stage1, mstd_win)
        else:
            stage2 = stage1[:]

        if use_antiflash:
            stage3 = antiflash(stage2)
        else:
            stage3 = stage2[:]

        return stage3


    def _preprocess_bulk(self, src):
        if self.use_robust:
            return self.preprocess_bulk_robust(src)
        else:
            return self.preprocess_bulk_norobust(src)

    def preprocess_whole(self, src: np.ndarray, broken: np.ndarray):
        if self.independent_pmt:
            signal = np.zeros(src.shape)
            signal[:, :8, :8] = self._preprocess_bulk(src[:, :8, :8])
            signal[:, 8:, :8] = self._preprocess_bulk(src[:, 8:, :8])
            signal[:, :8, 8:] = self._preprocess_bulk(src[:, :8, 8:])
            signal[:, 8:, 8:] = self._preprocess_bulk(src[:, 8:, 8:])
        else:
            signal = self._preprocess_bulk(src)

        if broken is not None:
            # noise = np.std(signal[:, np.logical_not(broken)])
            # mean = np.mean(signal[:, np.logical_not(broken)])
            # mean, noise = get_noise(signal, broken)
            # broken_exp = np.expand_dims(broken, 0)
            signal = noisy(signal, broken)
            # np.putmask(signal, np.repeat(broken_exp, signal.shape[0], axis=0),
            #            np.random.normal(mean, noise, signal.shape))
        return signal

    def preprocess_range(self, src: np.ndarray, broken: np.ndarray, slice_start, slice_end):
        margin = self.get_affected_range()
        truncated, inner_slice = slice_for_preprocess(src, slice_start, slice_end, margin)
        preprocessed = self.preprocess_whole(truncated, broken)
        return preprocessed[inner_slice]

    def stabilized_sliding(self, src: np.ndarray, broken: np.ndarray, window: int):
        warnings.warn("REMOVE IT ASAP. It will take forever. Edge effect suppression is under construction.")
        length = src.shape[0]
        if window >= length:
            return np.expand_dims(self.preprocess_whole(src, broken), 0)
        else:
            res = np.zeros(shape=(length-window+1, window, src.shape[1], src.shape[2]))
            for i in range(length-window+1):
                sub_src = src[i:i+window]
                res[i] = self.preprocess_whole(sub_src, broken)
            return res

    def get_affected_range(self):
        if self.ma_win>self.mstd_win:
            return self.ma_win
        else:
            return self.mstd_win



    def preprocess_single(self, ffmodel, src, index, broken):
        '''
        Since DataThreeStagePreProcessor has some limitation use this function instead for reading the h5py data
        :return:
        '''
        if self.is_sliding():
            subsrc, new_index = get_window_data(src, index, self)
        else:
            subsrc = src[index:index + 1]
            new_index = 0

        if ffmodel is not None:
            subsrc = ffmodel.apply(subsrc)
        #return self.preprocess_single(subsrc, broken, new_index)
        return self.preprocess_whole(subsrc, broken)[new_index]

    def is_sliding(self):
        return self.ma_win != 0 or self.mstd_win != 0

    def is_working(self):
        return self.is_sliding() or self.use_antiflash

    def prepare_array(self, src, slice_start, slice_end):
        if self.is_working():
            return slice_for_preprocess(src, slice_start, slice_end, self.get_affected_range())
        else:
            return src, slice(None,None,None)

def get_window_data(signal_source, index, filter_obj:DataThreeStagePreProcessor):
    affect_window = filter_obj.get_affected_range()
    start, end = window_limiting(index, affect_window, signal_source.shape[0])
    new_index = index-start
    return signal_source[start:end], new_index

def absmed(x, *args, **kwargs):
    return np.median(np.abs(x), *args, **kwargs)


