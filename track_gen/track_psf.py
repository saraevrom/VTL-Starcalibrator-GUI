import numpy as np
import numba as nb
from scipy.special import erf
from .pdm_params import ij_to_xy, side_a, side_b

class TrackPSF(object):
    def generate(self, center):
        raise NotImplementedError("Cannot generate light curve")

@nb.njit(nb.float64[:](nb.float64[:], nb.float64))
def ee_gauss(dx, sigmax):
    ax = 1
    f = np.zeros(shape=dx.shape)
    # scipy.special.erf requires argument to be float64 when working in numba "nopython" mode
    # Using it with cycle. Since this code is compiled in numba "nopython" mode it will work fast.
    for i in range(dx.shape[0]):
        f[i] = 0.5*(erf((dx[i] + ax/2)/np.sqrt(2)/sigmax) - erf((dx[i] - ax/2)/np.sqrt(2)/sigmax))
    return f

@nb.njit(nb.float64[:,:,:](nb.float64[:,:], nb.float64, nb.float64))
def ens_energy_no_id_gauss(center, width, height):
    N = len(center)
    EEs = np.zeros((N, side_a, side_b))

    for i in range(side_a):
        for j in range(side_b):
            x,y = ij_to_xy((i,j))
            EEs[:, i, j] = ee_gauss(x - center[:, 0], width) * ee_gauss(y - center[:, 1], height)

    return EEs

class GaussianPSF(TrackPSF):
    def __init__(self, sigma_x, sigma_y):
        self.sigma_x = sigma_x
        self.sigma_y = sigma_y

    def generate(self, center):
        return ens_energy_no_id_gauss(center, self.sigma_x, self.sigma_y)
