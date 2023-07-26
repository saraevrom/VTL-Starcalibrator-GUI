import numpy as np
import numba as nb
from scipy.optimize import minimize
from .isotropic_lsq import multidim_sphere, get_sphere_angles

GR = (np.sqrt(5) + 1) / 2

@nb.njit()
def fwd_model(t, coeffs, dividers, r0):
    return np.sum((coeffs*t*np.exp(-coeffs*t/dividers)-r0)*(1-coeffs*t/dividers)*np.exp(-coeffs*t/dividers))


@nb.njit(nb.float64(nb.float64[:,:],nb.float64[:,:],nb.float64[:,:]))
def sqr_distanceto(coeffs, dividers, point):
    r0 = point

    a = 0.0
    b = np.max(dividers*np.e)
    c = b - (b - a) / GR
    d = a + (b - a) / GR
    while abs(b - a) > 1e-6:
        fc = fwd_model(c, coeffs, dividers, r0)
        fd = fwd_model(d, coeffs, dividers, r0)
        if fc < fd:  # f(c) > f(d) to find the maximum
            b = d
        else:
            a = c
        c = b - (b - a) / GR
        d = a + (b - a) / GR

    t = (a+b)/2

    delta = coeffs*t*np.exp(-coeffs*t/dividers) - r0
    return np.sum(delta * delta)


@nb.njit(nb.float64(nb.float64[:,:],nb.float64[:,:],nb.float64[:,:,:]))
def sqr_distance_sum(coeffs, dividers, points):
    sum = 0.0
    for k in nb.prange(points.shape[0]):
        sum += sqr_distanceto(coeffs, dividers, points[k])
    return sum/points.shape[0]


def fit_pileup(data0):
    k0 = np.median(data0, axis=0)
    k0_flat = k0.flatten()
    dividers = k0_flat*np.e*100
    ang0 = get_sphere_angles(k0_flat)
    anglen = ang0.shape[0]
    x0 = np.concatenate([ang0, dividers])

    def loss(pars):
        ang = pars[:anglen]
        dividers = pars[anglen:].reshape(k0.shape)
        k = multidim_sphere(ang).reshape(k0.shape)
        lossed = np.sqrt(sqr_distance_sum(k,dividers,data0))
        print("\r", lossed, end="")
        return lossed
    minimized = minimize(loss, x0, method="powell")
    print()
    assert minimized.success
    pars = minimized.x
    ang = pars[:anglen]
    dividers = pars[anglen:].reshape(k0.shape)
    k = multidim_sphere(ang).reshape(k0.shape)

    return k, dividers