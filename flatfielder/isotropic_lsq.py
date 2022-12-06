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


def multidim_sphere(angles: np.ndarray):
    dim = angles.shape[0]
    sinerow = np.sin(angles)
    cosrow = np.cos(angles)
    startmat = np.tri(dim, k=-1)*np.repeat([sinerow],dim,axis=0)+np.diag(cosrow) + np.tri(dim, k=-1).T
    fullmatr = np.vstack([startmat, sinerow])
    return np.prod(fullmatr, axis=1)




def planar_rotation_matrix(a,b):
    assert a.shape == b.shape
    abT = np.vstack([a, b])
    ab = abT.T

    D = 1-np.dot(a,b)**2
    row1 = (a-np.dot(a,b)*b)/D
    row2 = (b-np.dot(a,b)*a)/D
    abT = np.vstack([row1,row2])

    R = np.array([
        [0, -1],
        [1, 2*np.dot(a, b)]
    ])
    return np.matmul(np.matmul(ab, R-np.identity(2)), abT) + np.identity(a.shape[0])

def mod_params_to_line(params,dims):
    angles, zero_coords = params[:dims - 1], params[dims - 1:]
    direction = multidim_sphere(angles)
    start_dir = np.zeros(dims)
    start_dir[-1] = 1
    rot_matrix = planar_rotation_matrix(start_dir, direction)
    multidim_displace = np.matmul(rot_matrix, np.append(zero_coords, 0))
    return direction, multidim_displace

def multidim_vec_score(params, signal_mat):
    dims = signal_mat.shape[1]
    direction, displace = mod_params_to_line(params, dims)
    modded_signals = signal_mat - displace
    direction_projections = np.dot(modded_signals, direction)
    direction_parts = np.dot(np.expand_dims(direction_projections, 1), np.expand_dims(direction, 0))
    modded_signals = modded_signals - direction_parts
    distances = np.sum(modded_signals**2, axis=1)
    return np.sum(distances**0.5)

def isotropic_lad_multidim(signal_mat):
    dims = signal_mat.shape[1]
    initial_guess = np.zeros(2*(dims-1))
    res = minimize(multidim_vec_score, np.array(initial_guess), args=(signal_mat,), method="Powell")
    assert res.success
    params = res.x
    return mod_params_to_line(params,dims)

def multidim_vec_score_no_bg(params, signal_mat):
    direction = multidim_sphere(params)
    modded_signals = signal_mat
    direction_projections = np.dot(modded_signals, direction)
    direction_parts = np.dot(np.expand_dims(direction_projections, 1), np.expand_dims(direction, 0))
    modded_signals = modded_signals - direction_parts
    distances = np.sum(modded_signals**2, axis=1)
    return np.sum(distances**0.5)

def isotropic_lad_multidim_no_bg(signal_mat):
    dims = signal_mat.shape[1]
    initial_guess = np.zeros(dims-1)
    res = minimize(multidim_vec_score_no_bg, np.array(initial_guess), args=(signal_mat,), method="Powell")
    assert res.success
    params = res.x
    return multidim_sphere(params)