import numpy as np
import numpy.random as rng

class Sampler(object):
    def sample(self, shape=None):
        raise NotImplementedError()


class SamplerConstant(Sampler):
    def __init__(self, value):
        self.value = value

    def sample(self, shape=None):
        if shape is None:
            return self.value
        else:
            return np.full(shape, self.value)


class SamplerUniform(Sampler):
    def __init__(self, low, high):
        self.low = low
        self.high = high

    def sample(self, shape=None):
        low = self.low.sample()
        high = self.high.sample()
        if shape is None:
            return rng.random()*(high-low)+low
        else:
            return rng.random(*shape) * (high - low) + low

class SamplerGauss(Sampler):

    def __init__(self, mean, stdev):
        self.mean = mean
        self.stdev = stdev

    def sample(self, shape=None):
        mean = self.mean.sample()
        stdev = self.stdev.sample()
        return rng.normal(mean, stdev, size=shape)


SQRT_2 = np.sqrt(2)


class SamplerLaplace(Sampler):

    def __init__(self, mean, stdev):
        self.mean = mean
        self.stdev = stdev

    def sample(self, shape=None):
        mean = self.mean.sample()
        stdev = self.stdev.sample()
        return rng.laplace(mean, stdev/SQRT_2, size=shape)

