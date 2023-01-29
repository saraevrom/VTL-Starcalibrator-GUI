from preprocessing.denoising import reduce_noise, antiflash, moving_average_subtract
class DataPreProcessor(object):
    def __init__(self, ma_win=10, mstd_win=100, use_antiflash=True):
        self.ma_win = ma_win
        self.mstd_win = mstd_win
        self.use_antiflash = use_antiflash

    def three_stage_preprocess(self, src, ma_win_override=None, mstd_win_override=None, use_antiflash_override = None):
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
            return antiflash(stage2)
        else:
            return stage2
