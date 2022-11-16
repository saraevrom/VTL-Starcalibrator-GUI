import numpy as np
from scipy.optimize import minimize

def dispersion(x):
    return np.mean(x**2) - np.mean(x)**2

def cov(x,y):
    return np.mean(x*y) - np.mean(x)*np.mean(y)

def displacement(x,y,phi):
    return np.mean(y)*np.cos(phi) - np.mean(x)*np.sin(phi)

def lsq_error(xs,ys,phi,r0):
    return np.sum((xs*np.sin(phi)-ys*np.cos(phi)+r0)**2)

def isotropic_lsq_line(xs, ys):
    dx = dispersion(xs)
    dy = dispersion(ys)
    cov_xy = cov(xs, ys)
    phi_1 = np.arctan2(2*cov_xy, (dx-dy))/2
    r_1 = displacement(xs, ys, phi_1)
    phi_2 = phi_1 + np.pi/2
    if phi_1 > 0:
        phi_2 = phi_1 - np.pi/2
    r_2 = displacement(xs, ys, phi_2)
    if lsq_error(xs, ys, phi_1, r_1) < lsq_error(xs, ys, phi_2, r_2):
        return phi_1, r_1
    else:
        return phi_2, r_2


def lad_line_score(params, xs, ys):
    phi, r0 = params
    return np.sum(np.abs(xs*np.sin(phi)-ys*np.cos(phi) + r0))


def isotropic_lad_line(xs, ys):
    initial_guess = isotropic_lsq_line(xs, ys)
    res = minimize(lad_line_score, np.array(initial_guess), args=(xs, ys), method="Powell")
    assert res.success
    return res.x


def phir0_to_kb(phi, r0):
    k = np.tan(phi)
    b = r0/np.cos(phi)
    return k, b


def phir0_to_kb_inv(phi, r0):
    k = 1/np.tan(phi)
    b = - r0/np.sin(phi)
    return k, b
