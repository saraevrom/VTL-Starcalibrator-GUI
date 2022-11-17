import numpy as np
import numpy.random as rng
from scipy.optimize import minimize

class RandomRoaming(object):
    def __init__(self, params_getter, params_setter, score_func, delta_getter):
        self.score = 0
        self.max_delta = None
        self.params = None
        self.params_getter = params_getter
        self.params_setter = params_setter
        self.score_func = score_func
        self.delta_getter = delta_getter
        #self.sync_params()

    def sync_params(self):
        self.max_delta = np.array(self.delta_getter())
        self.params = np.array(self.params_getter())
        self.score = self.score_func(*self.params)
        assert len(self.max_delta) == len(self.params)
        print("Synced params", self.params)

    def step(self):
        delta = (rng.random(len(self.max_delta))*2-1)*self.max_delta
        new_params = self.params + delta
        new_score = self.score_func(*new_params)
        print("new Score:",new_score)
        if new_score > self.score:
            self.params = new_params
            self.score = new_score
            print("FOUND BETTER VALUES", self.params)
            self.params_setter(*self.params)
        print("Score:",self.score)


def maximize(score, initial_params):
    def antiscore(params):
        return -score(*params)

    res = minimize(antiscore, initial_params, method="nelder-mead")
    return res.x, res.success