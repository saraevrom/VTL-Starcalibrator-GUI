import matplotlib.pyplot as plt
import numpy as np

try:
    from robustats import weighted_median
except ImportError:
    weighted_median = None

try:
    import pymc as pm
    import arviz as az
    try:
        import aesara.tensor as pt
    except ImportError:
        import pytensor.tensor as pt
except ImportError:
    pm = None
    pt = None
    az = None

from scipy.special import lambertw
from scipy.optimize import minimize, Bounds, LinearConstraint
import numpy.random as rng
import numba as nb

from .isotropic_lsq import isotropic_lsq_line, phir0_to_kb, phir0_to_kb_inv, isotropic_lsq_multidim
from .isotropic_lsq import isotropic_lad_multidim_no_bg, multidim_sphere, get_sphere_angles
from multiprocessing import Pool

from vtl_common.parameters import NPROC
from .models import Linear, NonlinearPileup, Interpolative
from .pileup_math import fit_pileup
from vtl_common.localization import get_locale
from vtl_common.workspace_manager import Workspace

CALIBRATION_WORKSPACE = Workspace("calibration")




def pile_up_manual(requested_data0):
    '''
    Load coefficients provided by Daniel
    requested_data0 is not used
    '''
    filename_k = CALIBRATION_WORKSPACE.askopenfilename(
                                            title=get_locale("flatfielder.filedialog.open_k.title"),
                                            filetypes=[
                                                (get_locale("app.filedialog_formats.txt"), "*.txt")
                                            ],
                                            initialfile="k_eff.txt"
                                            )
    if filename_k:
        filename_tau = CALIBRATION_WORKSPACE.askopenfilename(
            title=get_locale("flatfielder.filedialog.open_tau.title"),
            filetypes=[
                (get_locale("app.filedialog_formats.txt"), "*.txt")
            ],
            initialfile="tau.txt"
        )
        if filename_tau:
            k = np.genfromtxt(filename_k, delimiter=",").T  # Original format is transposed
            tau = np.genfromtxt(filename_tau, delimiter=",").T * 1e-6 # ns->ms
            gtu = 1 # ms
            return NonlinearPileup(sensitivity=k*gtu, divider=gtu / tau, prescaler=1.0, offset=0.0)
            # Device is outputting integrated signal
            # Converting to mean by dividing by number of gtu per 1e-3 s
    return None


@nb.njit(nb.float64[:,:,:](nb.float64[:,:,:],nb.float64[:,:]))
def spacetime_outer_div(st_arr, s_arr):
    res = np.zeros(st_arr.shape)
    for k in range(st_arr.shape[0]):
        for i in range(st_arr.shape[1]):
            for j in range(st_arr.shape[2]):
                if s_arr[i,j] != 0:
                    res[k,i,j] = st_arr[k,i,j]/s_arr[i, j]
    return res

@nb.njit(nb.float64[:,:,:](nb.float64[:,:],nb.float64[:,:,:]))
def sweep_product(s_arr, st_arr):
    res = np.zeros(st_arr.shape)
    for k in range(st_arr.shape[0]):
        for i in range(st_arr.shape[1]):
            for j in range(st_arr.shape[2]):
                res[k,i,j] = s_arr[i,j]*st_arr[k, i, j]
    return res

@nb.njit(nb.float64[:,:,:](nb.float64[:],nb.float64[:,:,:]))
def mae_sub(a,b):
    res = np.zeros(b.shape)
    for k in range(b.shape[0]):
        for i in range(b.shape[1]):
            for j in range(b.shape[2]):
                res[k,i,j] = b[k,i,j] - a[k]
    return res



def parametrization_matrix(shape_len):
    basis_projected = np.identity(shape_len) - 1/shape_len
    basis_planar = basis_projected[:,:-1]
    basis = []
    for i in range(shape_len-1):
        new_element = basis_planar[:,i]
        for in_basis in basis:
            new_element = new_element - in_basis*(in_basis@new_element)
        new_element = new_element/(new_element@new_element)**0.5
        basis.append(new_element)
    basis = np.vstack(basis)
    return basis.T

def parametrize(basis, coeffs_flat):
    l = coeffs_flat.shape[0]
    projected = coeffs_flat*(l**0.5)/np.sum(coeffs_flat) - 1/l**0.5
    print("PROJECTION SUM", np.sum(projected))
    return basis.T @ projected

def pile_up_auto(requested_data0):
    k,div = fit_pileup(requested_data0)
    return NonlinearPileup(sensitivity=k, divider=div, prescaler=1.0, offset=0.0 )


LEARN_SW = [
    #(1000.0, 0.1),
    (30000, 500.0),
    (25000, 200.0),
    (1000, 100.0),
    (100,10.0)
]

def medians_44(requested_data0):
    medians = np.median(requested_data0,axis=0)
    med44 = medians[3,3]  #A[3,3] is pixel 4,4
    coeffs = medians/med44
    return Linear(coeffs, np.zeros(coeffs.shape))


def median_offset(requested_data0):
    medians = np.median(requested_data0,axis=0)
    true_median = np.median(requested_data0)
    offsets = medians-true_median
    return Linear(np.ones(offsets.shape), offsets)


def get_model(requested_data0):
    median_frame = np.median(requested_data0, axis=0)
    min_frame = np.min(requested_data0, axis=0)
    max_frame = np.max(requested_data0, axis=0)
    pixels_amount = sum(median_frame.shape)
    print("Building model")

    with pm.Model() as model:
        # off0 = pm.Normal("OFF",sigma=1.0, shape=min_frame.shape)
        # offset = pt.expand_dims(off0, (0,))

        intensity = pm.Uniform("I", lower=0.0, upper=100.0, shape=(requested_data0.shape[0],))
        intens1 = pt.expand_dims(intensity, (1, 2))

        D = pm.TruncatedNormal("D_P", mu=1, lower=1, sigma=1, shape=min_frame.shape) * max_frame
        div_norm = pm.TruncatedNormal("DIVN_P", sigma=10.0, mu=1.0, lower=1.0, shape=min_frame.shape) * 100.0

        div = pm.Deterministic("DIV", D * np.e)
        pm.Deterministic("EFF", div / div_norm)

        D1 = pt.expand_dims(D, (0,))
        divnorm1 = pt.expand_dims(div_norm, (0))
        # signal = np.e*D1/divnorm1 * (intens1-offset)*pt.exp(-(intens1-offset)/divnorm1)
        signal = np.e * D1 / divnorm1 * intens1 * pt.exp(-intens1 / divnorm1)
        sigma = pm.Exponential("σ", lam=1e4, shape=min_frame.shape)
        # b = pm.Exponential("b",lam=1e3, shape=min_frame.shape)
        posterior = pm.Normal("POST", mu=signal, sigma=sigma, observed=requested_data0)
        print("Model ready")
    return model

def pile_up_prob(requested_data0):
    model = get_model(requested_data0)
    with model:
        idata = pm.sample(draws=2000,tune=4000, chains=4, target_accept=0.95)
    #print(az.summary(idata))
    print("Getting efficiency")
    efficiency = idata.posterior["EFF"].median(dim=["draw", "chain"]).to_numpy()
    print("Getting divider")
    divider = idata.posterior["DIV"].median(dim=["draw", "chain"]).to_numpy()
    print("Getting stdev")
    sigma0 = idata.posterior["σ"].median(dim=["draw", "chain"]).to_numpy()
    #b0 = idata.posterior["b"].median(dim=["draw", "chain"]).to_numpy()
    #offset = idata.posterior["OFF"].median(dim=["draw", "chain"]).to_numpy()
    print("Calculation stdev:", sigma0)
    return NonlinearPileup(sensitivity=efficiency, divider=divider, prescaler=1.0, offset=0.0)

def interpolative_median(requested_data0):
    zero_frame = np.zeros(shape=(1,requested_data0.shape[1], requested_data0.shape[2]))
    data0 = np.concatenate([zero_frame, requested_data0], axis=0)
    intensities = np.median(data0, axis=(1,2))
    indices = np.argsort(intensities)

    x_frames = data0[indices]
    y_frames = intensities[indices]

    return Interpolative(x_frames=x_frames, y_frames=y_frames)

def interpolative_mean(requested_data0):
    zero_frame = np.zeros(shape=(1,requested_data0.shape[1], requested_data0.shape[2]))
    data0 = np.concatenate([zero_frame, requested_data0], axis=0)
    intensities = np.mean(data0, axis=(1,2))
    indices = np.argsort(intensities)

    x_frames = data0[indices]
    y_frames = intensities[indices]

    return Interpolative(x_frames=x_frames, y_frames=y_frames)

def interpolative_probabilistic(requested_data0):
    model = get_model(requested_data0)
    with model:
        idata = pm.sample(draws=2000, tune=4000, chains=4, target_accept=0.95)
    intensities = idata.posterior["I"].median(dim=["draw", "chain"]).to_numpy()
    #print(intensities)

    zero_frame = np.zeros(shape=(1,requested_data0.shape[1], requested_data0.shape[2]))
    data0 = np.concatenate([zero_frame, requested_data0], axis=0)
    intensities = np.concatenate([[0],intensities])
    indices = np.argsort(intensities)

    x_frames = data0[indices]
    y_frames = intensities[indices]

    return Interpolative(x_frames=x_frames, y_frames=y_frames)



ALGO_MAP = {
    # "linear_correlation": (isotropic_lsq_corr_flatfield_parallel, "LC"),
    # "isotropic_lad_multidim_no_bg": (multidim_lad_corr_flatfield_no_bg, "LMSCNBG"),
    # "nonlinear_saturated_response": (isotropic_lsq_corr_flatfield_nonlinear, "NSR"),
    "pileup_manual": (pile_up_manual, "PUM"),
    "pileup_heuristic": (pile_up_auto, "PUH"),
    "medians_44":(medians_44, "M44"),
    "align_offset":(median_offset, "MAL"),
    "interpolative_median":(interpolative_median, "INTPM"),
    "interpolative_average":(interpolative_mean, "INTPA")
}

if pm is not None:
    ALGO_MAP["pileup_probabilistic"] = (pile_up_prob, "PUP")
    ALGO_MAP["interpolative_probabilistic"] = (interpolative_probabilistic, "IPP")

# if weighted_median is not None:
#     ALGO_MAP["proportional_correlation"] = (median_corr_flatfield, "PC")