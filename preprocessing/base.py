import numpy as np

class Preprocessor(object):
    def preprocess(self, signal, broken=None):
        if broken is not None:
            noise = np.std(signal[:, np.logical_not(broken)])
            mean = np.mean(signal[:, np.logical_not(broken)])
            broken_exp = np.expand_dims(broken, 0)
            np.putmask(signal, np.repeat(broken_exp, signal.shape[0], axis=0),
                       np.random.normal(mean, noise, signal.shape))
        return signal