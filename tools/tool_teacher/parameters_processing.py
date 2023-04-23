import numpy as np
from trigger_ai.models.model_wrapper import TargetParameters

class Appliance(object):
    def apply(self, data, rng):
        raise NotImplementedError()




class Augmenter(Appliance):
    def __init__(self, use_transpose, use_reverse):
        self.use_transpose = use_transpose
        self.use_reverse = use_reverse

    def apply(self, data, rng):
        data1 = data
        if self.use_transpose and rng.random()<0.5:
            data1 = np.swapaxes(data, 1, 2)
        if self.use_reverse:
            if rng.random() < 0.5:
                data1 = np.flip(data1, axis=0)
            if rng.random() < 0.5:
                data1 = np.flip(data1, axis=1)
            if rng.random() < 0.5:
                data1 = np.flip(data1, axis=2)
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

    def apply_primary(self, data, rng):
        return self.primary.apply(data, rng)

    def apply_secondary(self, data, rng):
        return self.get_secondary().apply(data, rng)


class ProbeParameters(object):
    def __init__(self, conf):
        self.conf = conf


class LearnParameters(object):
    def __init__(self, config):
        self.config = config

    def __getattr__(self, item):
        if item in self.config.keys():
            return self.config[item]
        else:
            raise AttributeError(f" '{type(self).__name__}' object has no attribute '{item}' even in config")

    def get_fit_parameters(self):
        return {k: self.config[k] for k in ["epochs", "steps_per_epoch", "workers"]}

    def get_fit_parameters_finite(self):
        return {k: self.config[k] for k in ["epochs", "workers", "batch_size"]}

    def generator_params(self):
        return {k: self.config[k] for k in ["batch_size", ]}

    def intergerence_artificial(self):
        return self.config["artificial_interference"]

    def get_preprocessor(self):
        return self.config["preprocessing"]

    def get_trackgen(self):
        return self.config["trackgen"]

    def process_fg(self, data, rng):
        modifier = self.config["modification"]
        augmenter = self.config["augment"]
        data1 = modifier.apply_primary(data, rng)
        data1 = augmenter.apply_primary(data1, rng)
        return data1

    def process_it(self, data, rng):
        modifier = self.config["modification"]
        augmenter = self.config["augment"]
        data1 = modifier.apply_secondary(data, rng)
        data1 = augmenter.apply_secondary(data1, rng)
        return data1

    def process_bg(self, x_data, y_info, rng):
        bg_mod = self.postprocess.apply(x_data, rng)
        return bg_mod

