import numpy.random as rng

class Sampler(object):
    def sample(self):
        raise NotImplementedError()


class SamplerConstant(Sampler):
    def __init__(self, value):
        self.value = value

    def sample(self):
        return self.value

class SamplerRange(Sampler):
    def __init__(self,low,high):
        self.low = low
        self.high = high

    def sample(self):
        return rng.random()*(self.high-self.low)+self.low
