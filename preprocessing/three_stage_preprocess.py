import numpy as np
from .base import Preprocessor
from .denoising import reduce_noise, antiflash, moving_average_subtract
from .denoising import  moving_median_subtract, reduce_noise_robust
class DataThreeStagePreProcessor(Preprocessor):
    def __init__(self, ma_win=10, mstd_win=100, use_antiflash=True, use_robust=False, independent_pmt=False):
        self.ma_win = ma_win
        self.mstd_win = mstd_win
        self.use_antiflash = use_antiflash
        self.use_robust = use_robust
        self.independent_pmt = independent_pmt

    def __repr__(self):
        res = "Filter:\n"
        off = True
        if self.ma_win is not None:
            res += f"\tMA={self.ma_win}\n"
            off = False
        if self.mstd_win is not None:
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



    def preprocess_bulk(self, src):
        if self.use_robust:
            stage1_f = moving_median_subtract
            stage2_f = reduce_noise_robust
        else:
            stage1_f = moving_average_subtract
            stage2_f = reduce_noise

        ma_win = self.ma_win

        mstd_win = self.mstd_win

        use_antiflash = self.use_antiflash

        if ma_win is not None:
            stage1 = stage1_f(src, ma_win)
        else:
            stage1 = src

        if mstd_win is not None:
            stage2 = stage2_f(stage1, mstd_win)
        else:
            stage2 = stage1

        if use_antiflash:
            stage3 = antiflash(stage2)
        else:
            stage3 = stage2

        return stage3


    def preprocess(self, src: np.ndarray, broken=None):
        if self.independent_pmt:
            stage3 = np.zeros(src.shape)
            stage3[:, :8, :8] = self.preprocess_bulk(src[:, :8, :8])
            stage3[:, 8:, :8] = self.preprocess_bulk(src[:, 8:, :8])
            stage3[:, :8, 8:] = self.preprocess_bulk(src[:, :8, 8:])
            stage3[:, 8:, 8:] = self.preprocess_bulk(src[:, 8:, 8:])
        else:
            stage3 = self.preprocess_bulk(src)

        return super().preprocess(stage3, broken)
