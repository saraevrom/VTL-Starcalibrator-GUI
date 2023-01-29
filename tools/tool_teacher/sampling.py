import numpy as np
import numpy.random as rng

class Sampler(object):
    def sample(self):
        raise NotImplementedError()


class SamplerConstant(Sampler):
    def __init__(self, value):
        self.value = value

    def sample(self):
        return self.value

class SamplerUniform(Sampler):
    def __init__(self,low,high):
        self.low = low
        self.high = high

    def sample(self):
        return rng.random()*(self.high-self.low)+self.low

class SamplerGauss(Sampler):

    def __init__(self, mean, stdev):
        self.mean = mean
        self.stdev = stdev

    def sample(self):
        return rng.normal(self.mean, self.stdev)


SQRT_2 = np.sqrt(2)

class SamplerLaplace(Sampler):

    def __init__(self, mean, stdev):
        self.mean = mean
        self.stdev = stdev

    def sample(self):
        return rng.laplace(self.mean, self.stdev/SQRT_2)