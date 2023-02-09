import numpy as np
from .base import Preprocessor
from preprocessing.denoising import reduce_noise, antiflash, moving_average_subtract
class DataThreeStagePreProcessor(Preprocessor):
    def __init__(self, ma_win=10, mstd_win=100, use_antiflash=True):
        self.ma_win = ma_win
        self.mstd_win = mstd_win
        self.use_antiflash = use_antiflash

    def preprocess(self, src, broken=None):
        ma_win = self.ma_win

        mstd_win = self.mstd_win

        use_antiflash = self.use_antiflash

        if ma_win is not None:
            stage1 = moving_average_subtract(src, ma_win)
        else:
            stage1 = src

        if mstd_win is not None:
            stage2 = reduce_noise(stage1, mstd_win)
        else:
            stage2 = stage1

        if use_antiflash:
            stage3 = antiflash(stage2)
        else:
            stage3 = stage2

        return super().preprocess(stage3, broken)