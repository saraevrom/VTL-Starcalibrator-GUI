import matplotlib.pyplot as plt
import numpy as np
from robustats import weighted_median
from flatfielder.isotropic_lsq import isotropic_lad_line, phir0_to_kb, phir0_to_kb_inv, isotropic_lad_multidim
from flatfielder.isotropic_lsq import isotropic_lad_multidim_no_bg
from multiprocessing import Pool
from parameters import NPROC
from .models import Linear

def line_fit_robust(xs, ys):
    k = np.float(weighted_median(ys/xs, xs))
    return k

def get_working_pixels(coeffs, x_len, y_len):
    return np.where((coeffs <= 0).sum(axis=0) < x_len * y_len - 1)[0]

def get_pivot(reduced_coeff_matrix):
    sample_row = reduced_coeff_matrix[0]
    print(len(sample_row))
    sample_median = np.median(sample_row[sample_row != 0])
    sample_distances = np.abs(sample_row - sample_median)
    pivot = np.argmin(sample_distances)
    return pivot

def median_corr_flatfield(requested_data_0):
    tim_len, x_len, y_len = requested_data_0.shape
    requested_data = requested_data_0.reshape((tim_len, x_len * y_len))
    coeff_matrix = np.zeros([x_len * y_len, x_len * y_len])
    for i in range(x_len * y_len):
        i_data = requested_data[:, i]
        for j in range(x_len * y_len):
            j_data = requested_data[:, j]

            k_ij = line_fit_robust(i_data, j_data)
            if k_ij != 0:
                coeff_matrix[i, j] = k_ij
    coeff_matrix = np.nan_to_num(coeff_matrix, nan=0)
    print(coeff_matrix.shape)
    #bad_indices, = np.where((coeff_matrix == 0).sum(axis=0) >= x_len * y_len - 1)
    good_indices = get_working_pixels(coeff_matrix, x_len, y_len)
    #coeff_matrix[bad_indices] = np.zeros(x_len * y_len)



    coeff_matrix_reduced = coeff_matrix[good_indices]
    pivot = get_pivot(coeff_matrix_reduced)
    print("Chosen pivot:", pivot)
    coeff_matrix_reduced = (coeff_matrix_reduced.T / coeff_matrix_reduced[:, pivot]).T

    # good_indices = np.where((coeff_matrix != 0).any(axis=0))
    # assert len(good_indices) > 0
    # correct_row = 0
    # correct_row = np.argmax(coeff_matrix) // coeff_matrix.shape[0]
    # coeff_array = coeff_matrix[correct_row]
    coeff_array = np.median(coeff_matrix_reduced, axis=0)
    draw_coeff_matrix = coeff_array.reshape(x_len, y_len)
    return Linear(draw_coeff_matrix, np.zeros([x_len, y_len]))


def isotropic_lsq_corr_flatfield(requested_data_0):
    tim_len, x_len, y_len = requested_data_0.shape
    requested_data = requested_data_0.reshape((tim_len, x_len * y_len))
    coeff_matrix = np.zeros([x_len * y_len, x_len * y_len])
    bg_matrix = np.zeros([x_len * y_len, x_len * y_len])

    for i in range(x_len * y_len):
        i_data = requested_data[:, i]
        coeff_matrix[i, i] = 1
        bg_matrix[i, i] = 0
        # results = []
        for j in range(i + 1, x_len * y_len):
            j_data = requested_data[:, j]
            # result_promise = pool.apply_async(pool_worker, args=(i, j, i_data, j_data), callback=pool_callback)
            # results.append(result_promise)
            phi_ij, r0_ij = isotropic_lad_line(i_data, j_data)

            if phi_ij != 0 and np.abs(phi_ij) != np.pi / 2:
                k_ij, b_ij = phir0_to_kb(phi_ij, r0_ij)
                k_ji, b_ji = phir0_to_kb_inv(phi_ij, r0_ij)
                coeff_matrix[i, j] = k_ij
                coeff_matrix[j, i] = k_ji
                bg_matrix[i, j] = b_ij
                bg_matrix[j, i] = b_ji

    coeff_matrix = np.nan_to_num(coeff_matrix, nan=0)
    bg_matrix = np.nan_to_num(bg_matrix, nan=0)
    good_indices = get_working_pixels(coeff_matrix, x_len, y_len)
    coeff_matrix_reduced = coeff_matrix[good_indices]
    bg_matrix_reduced = bg_matrix[good_indices]
    pivot = get_pivot(coeff_matrix_reduced)
    coeff_matrix_normalized = (coeff_matrix_reduced.T / coeff_matrix_reduced[:, pivot]).T
    bg_matrix_normalized = ((bg_matrix_reduced.T - bg_matrix_reduced[:, pivot]) / coeff_matrix_reduced[:, pivot]).T
    coeff_array = np.median(coeff_matrix_normalized, axis=0)
    bg_array = np.median(bg_matrix_normalized, axis=0)
    draw_coeff_matrix = coeff_array.reshape(x_len, y_len)
    draw_bg_matrix = bg_array.reshape(x_len, y_len)
    return Linear(draw_coeff_matrix, draw_bg_matrix)


class PoolWorker(object):
    def __init__(self,requested_data):
        self.requested_data = requested_data

    def __call__(self, index_pair):
        i, j = index_pair
        # if j > i:
        i_data = self.requested_data[:, i]
        j_data = self.requested_data[:, j]
        phi_ij, r0_ij = isotropic_lad_line(i_data, j_data)
        return phi_ij, r0_ij
        #else:
        #    return 0, 0
def isotropic_lsq_corr_flatfield_parallel(requested_data_0):
    tim_len, x_len, y_len = requested_data_0.shape
    requested_data = requested_data_0.reshape((tim_len, x_len * y_len))
    #coeff_matrix = np.zeros([x_len * y_len, x_len * y_len])
    #bg_matrix = np.zeros([x_len * y_len, x_len * y_len])
    indices_raw_i, indices_raw_j = np.meshgrid(np.arange(x_len * y_len), np.arange(x_len * y_len), indexing="ij")
    indices_raw_i = indices_raw_i.flatten()
    indices_raw_j = indices_raw_j.flatten()
    indices = np.vstack([indices_raw_i, indices_raw_j]).T
    print(indices)
    poolworker = PoolWorker(requested_data)
    with Pool(NPROC) as pool:
        parallel_result = pool.map(poolworker, indices)
        flat_angles, flat_distances = np.array(parallel_result).T
        angle_matrix = flat_angles.reshape(x_len * y_len, x_len * y_len)
        distance_matrix = flat_distances.reshape(x_len * y_len, x_len * y_len)
        coeff_matrix, bg_matrix = phir0_to_kb(angle_matrix, distance_matrix)
        coeff_matrix[angle_matrix == 0] = 0
        # upper_coeffs, upper_bg = phir0_to_kb(angle_matrix, distance_matrix)
        # lower_coeffs, lower_bg = phir0_to_kb_inv(angle_matrix.T, distance_matrix.T)
        # upper_coeffs[angle_matrix == 0] = 0
        # upper_coeffs[np.abs(angle_matrix) == np.pi/2] = 0
        # lower_coeffs[(angle_matrix == 0).T] = 0
        # lower_coeffs[(np.abs(angle_matrix) == np.pi/2).T] = 0
        # coeff_matrix = upper_coeffs + lower_coeffs + np.identity(x_len * y_len)
        # bg_matrix = upper_bg + lower_bg
    coeff_matrix = np.nan_to_num(coeff_matrix, nan=0)
    bg_matrix = np.nan_to_num(bg_matrix, nan=0)
    plt.matshow(coeff_matrix)
    plt.show()
    plt.matshow(bg_matrix)
    plt.show()
    good_indices = get_working_pixels(coeff_matrix, x_len, y_len)
    coeff_matrix_reduced = coeff_matrix[good_indices]
    bg_matrix_reduced = bg_matrix[good_indices]

    pivot = get_pivot(coeff_matrix_reduced)
    #coeff_matrix_normalized = (coeff_matrix_reduced.T / coeff_matrix_reduced[:, pivot]).T
    #coeff_matrix_normalized = np.nan_to_num(coeff_matrix_normalized)
    #bg_matrix_normalized = ((bg_matrix_reduced.T - bg_matrix_reduced[:, pivot]) / coeff_matrix_reduced[:, pivot]).T
    #bg_matrix_normalized = np.nan_to_num(bg_matrix_normalized)
    #coeff_array = np.median(coeff_matrix_normalized, axis=0)
    #bg_array = np.median(bg_matrix_normalized, axis=0)
    coeff_array = coeff_matrix_reduced[pivot]
    bg_array = bg_matrix_reduced[pivot]
    draw_coeff_matrix = coeff_array.reshape(x_len, y_len)
    draw_bg_matrix = bg_array.reshape(x_len, y_len)
    return Linear(draw_coeff_matrix, draw_bg_matrix)

def multidim_lad_corr_flatfield(requested_data_0):
    tim_len, x_len, y_len = requested_data_0.shape
    requested_data = requested_data_0.reshape((tim_len, x_len * y_len))
    coeff_vector, bg_vector = isotropic_lad_multidim(requested_data)
    draw_coeff_matrix = coeff_vector.reshape(x_len, y_len)
    draw_bg_matrix = bg_vector.reshape(x_len, y_len)
    return Linear(draw_coeff_matrix, draw_bg_matrix)

def multidim_lad_corr_flatfield_no_bg(requested_data_0):
    tim_len, x_len, y_len = requested_data_0.shape
    requested_data = requested_data_0.reshape((tim_len, x_len * y_len))
    coeff_vector = isotropic_lad_multidim_no_bg(requested_data)
    draw_coeff_matrix = coeff_vector.reshape(x_len, y_len)
    draw_bg_matrix = np.zeros((x_len, y_len))
    return Linear(draw_coeff_matrix, draw_bg_matrix)

