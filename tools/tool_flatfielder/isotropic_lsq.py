import numpy as np
from scipy.optimize import minimize
import numba as nb
from numba import prange

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


def multidim_sphere_vectored(angles: np.ndarray):
    dim = angles.shape[0]
    sinerow = np.sin(angles)
    cosrow = np.cos(angles)
    startmat = np.tri(dim, k=-1)*np.repeat([sinerow],dim,axis=0)+np.diag(cosrow) + np.tri(dim, k=-1).T
    fullmatr = np.vstack([startmat, sinerow])
    return np.prod(fullmatr, axis=1)


@nb.njit(parallel=True)
def multidim_sphere(angles):
    N = angles.shape[0]+1
    result = np.zeros(N)
    for i in prange(N):
        accum = 1
        for j in range(i+1):
            if j < i:
                accum = accum * np.sin(angles[j])
            else:
                accum = accum * np.cos(angles[j])
        result[i] = accum
    return result


@nb.njit()
def get_sphere_angles(direction):
    #direction = direction/(np.dot(direction, direction))**0.5
    N = direction.shape[0]
    result = np.zeros(N-1)
    i = N-1
    y = direction[i]
    x = direction[i-1]
    while i >= 1:
        result[i - 1] = np.arctan2(y, x)
        i -= 1
        if i > 0:
            y = (x**2+y**2)**0.5
            x = direction[i-1]
    return result

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


def line_to_mod_params(direction: np.ndarray, multidim_displace: np.ndarray):
    direction = direction/np.dot(direction,direction)**0.5
    dims = direction.shape[0]
    start_dir = np.zeros(dims)
    start_dir[-1] = 1
    rot_matrix_inv = planar_rotation_matrix(direction, start_dir)
    zero_coords = np.matmul(rot_matrix_inv, multidim_displace)[:-1]
    angles = get_sphere_angles(direction)
    return np.concatenate([angles, zero_coords])


def twodot_line_params(p1, p2):
    direction = p2-p1
    direction = direction/np.sum(direction*direction)**0.5
    assert (direction>=0).all()
    dims = direction.shape[0]
    start_dir = np.zeros(dims)
    start_dir[-1] = 1
    rot_matrix_inv = planar_rotation_matrix(direction, start_dir)
    zero_coords = np.matmul(rot_matrix_inv, p1)[:-1]
    angles = get_sphere_angles(direction)
    return np.concatenate([angles, zero_coords])


@nb.njit(parallel=True)
def calculate_distances(points, direction):
    N, dims = points.shape
    assert dims == 256
    result = np.zeros(N)
    for i in prange(N):
        point = points[i]
        point = point - direction*np.sum(direction*point)
        result[i] = np.sqrt(np.sum(point * point))
    return result


def multidim_vec_score(params, signal_mat):
    dims = signal_mat.shape[1]
    direction, displace = mod_params_to_line(params, dims)
    modded_signals = signal_mat - displace

    distances = calculate_distances(modded_signals, direction)
    res = np.sum(distances)
    print("\r", res/distances.shape[0], end="")
    return res

def isotropic_lad_multidim(signal_mat):
    dims = signal_mat.shape[1]
    #initial_guess = np.zeros(2*(dims-1))
    distances_from_origin = np.sum(signal_mat * signal_mat, axis=1)
    closest = np.argmin(distances_from_origin)
    furthest = np.argmax(distances_from_origin)

    initial_guess = twodot_line_params(signal_mat[closest], signal_mat[furthest])
    #params = initial_guess
    print("")
    res = minimize(multidim_vec_score, np.array(initial_guess), args=(signal_mat,), method="Powell")
    print("")
    assert res.success
    params = res.x
    return mod_params_to_line(params, dims)

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