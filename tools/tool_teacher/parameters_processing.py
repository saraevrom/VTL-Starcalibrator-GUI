import numpy.random as rng
import numpy as np

class Appliance(object):
    def apply(self, data):
        raise NotImplementedError()


class SignalModifier(Appliance):
    def __init__(self, multiplier):
        self.multiplier = multiplier

    def apply(self, data):
        return self.multiplier.sample()*data

class Augmenter(Appliance):
    def __init__(self, use_transpose, use_reverse):
        self.use_transpose = use_transpose
        self.use_reverse = use_reverse

    def apply(self, data):
        data1 = data
        if self.use_transpose and rng.random()<0.5:
            data1 = np.swapaxes(data, 1, 2)
        if self.use_reverse and rng.random()<0.5:
            data1 = np.flip(data1, axis=0)
        return data1
class DualProcessing(object):
    def __init__(self, primary, secondary):
        self.primary = primary
        self.secondary = secondary

    def get_secondary(self):
        if self.secondary is None:
            return self.primary
        else:
            return self.secondary

    def apply_primary(self, data):
        return self.primary.apply(data)

    def apply_secondary(self, data):
        return self.get_secondary().apply(data)

    def sample_primary(self):
        return self.primary.sample()

    def sample_secondary(self):
        return self.get_secondary().sample()


class LearnParameters(object):
    def __init__(self,config):
        self.config = config

    def get_fit_parameters(self):
        return {k: self.config[k] for k in ["epochs", "steps_per_epoch", "workers"]}

    def generator_params(self):
        return {k: self.config[k] for k in ["batch_size", ]}


    def process_fg(self, data):
        modifier = self.config["modification"]
        augmenter = self.config["augment"]
        data1 = modifier.apply_primary(data)
        data1 = augmenter.apply_primary(data1)
        return data1

    def process_it(self, data):
        modifier = self.config["modification"]
        augmenter = self.config["augment"]
        data1 = modifier.apply_secondary(data)
        data1 = augmenter.apply_secondary(data1)
        return data1