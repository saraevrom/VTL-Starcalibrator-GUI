import numpy as np
import numba as nb
from .base import Preprocessor


@nb.njit(nb.float64[:](nb.float64[:], nb.int64, nb.float64))
def sliding_normalize_single(x, win, eps):
    if win >= x.shape[0]:
        med = np.median(x)
        return x / (med+eps)
    res = np.zeros(x.shape[0])
    for i in range(x.shape[0]):
        start = i-win//2
        if start<0:
            start = 0
        end = start+win
        if end >= x.shape[0]:
            end = x.shape[0]-1
            start = end - win
        res[i] = x[i] / (np.median(x[start:end])+eps)
    return res


@nb.njit(nb.float64[:, :, :](nb.float64[:, :, :], nb.int64, nb.float64), parallel=True)
def sliding_normalize_pixels(x, win, eps):
    res = np.zeros(x.shape)
    for i in nb.prange(x.shape[1]):
        for j in nb.prange(x.shape[1]):
            res[:, i, j] = sliding_normalize_single(x[:,i,j],win, eps)
    return res


class SlidingMedianNormalizer(Preprocessor):
    def __init__(self, median_window):
        self.median_window = median_window

    def preprocess(self, signal: np.ndarray, broken=None):
        signal = sliding_normalize_pixels(signal.astype(float), self.median_window, 1e-8)
        return super().preprocess(signal, broken)
