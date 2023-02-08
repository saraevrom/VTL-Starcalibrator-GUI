import numpy as np

from preprocessing.denoising import reduce_noise, antiflash, moving_average_subtract
class DataPreProcessor(object):
    def __init__(self, ma_win=10, mstd_win=100, use_antiflash=True):
        self.ma_win = ma_win
        self.mstd_win = mstd_win
        self.use_antiflash = use_antiflash

    def three_stage_preprocess(self, src, ma_win_override=None, mstd_win_override=None, use_antiflash_override = None,
                               broken=None):
        if ma_win_override is None:
            ma_win = self.ma_win
        else:
            ma_win = ma_win_override

        if mstd_win_override is None:
            mstd_win = self.mstd_win
        else:
            mstd_win = mstd_win_override

        if use_antiflash_override is None:
            use_antiflash = self.use_antiflash
        else:
            use_antiflash = use_antiflash_override

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

        if broken is not None:
            noise = np.std(stage3[:, np.logical_not(broken)])
            mean = np.mean(stage3[:, np.logical_not(broken)])
            broken_exp = np.expand_dims(broken,0)
            np.putmask(stage3, np.repeat(broken_exp, stage3.shape[0], axis=0),
                                np.random.normal(mean, noise, stage3.shape))
        return stage3