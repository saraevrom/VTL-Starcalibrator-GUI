import numpy as np


class Sampler(object):
    def sample(self, rng, shape=None):
        raise NotImplementedError()


class SamplerConstant(Sampler):
    def __init__(self, value):
        self.value = value

    def sample(self, rng, shape=None):
        if shape is None:
            return self.value
        else:
            return np.full(shape, self.value)


class SamplerUniform(Sampler):
    def __init__(self, low: Sampler, high: Sampler):
        self.low = low
        self.high = high

    def sample(self, rng, shape=None):
        low = self.low.sample(rng)
        high = self.high.sample(rng)
        if shape is None:
            return rng.random()*(high-low)+low
        else:
            return rng.random(*shape) * (high - low) + low


class SamplerGauss(Sampler):

    def __init__(self, mean: Sampler, stdev: Sampler):
        self.mean = mean
        self.stdev = stdev

    def sample(self, rng, shape=None):
        mean = self.mean.sample(rng)
        stdev = self.stdev.sample(rng)
        return rng.normal(mean, stdev, size=shape)


SQRT_2 = np.sqrt(2)


class SamplerLaplace(Sampler):

    def __init__(self, mean: Sampler, stdev: Sampler):
        self.mean = mean
        self.stdev = stdev

    def sample(self, rng, shape=None):
        mean = self.mean.sample(rng)
        stdev = self.stdev.sample(rng)
        return rng.laplace(mean, stdev/SQRT_2, size=shape)

