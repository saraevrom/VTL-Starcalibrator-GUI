import numpy as np
import numba as nb

from .track_dynamics import LinearTrackTrajectory, TrackTrajectory
from .track_lightcurves import TriangularLightCurve, LightCurve
from .track_psf import GaussianPSF, TrackPSF
from .pdm_params import SIDE_A, SIDE_B


@nb.njit()
def signals_2d(subframes, actual_time, duration, lc, energies):
    SGNs = np.zeros((duration, SIDE_A, SIDE_B))
    for k in range(actual_time):
        # SGNs[k] == 0 from start
        for k1 in range(k*subframes,subframes*(k+1)):
            SGNs[k] += lc[k1]*energies[k1]

    return SGNs

def generate_track(trajectory:TrackTrajectory, light_curve:LightCurve, psf:TrackPSF, duration, subframes, time_cap=None):
    if time_cap is None:
        time_cap = duration
    else:
        time_cap = min(time_cap, duration)
    track_trajectory = trajectory.generate(time_cap, subframes)
    t_bound = trajectory.get_time_bound()
    actual_time = int(np.amin([time_cap, t_bound]))
    track_light_curve = light_curve.get_curve(actual_time, subframes)
    ensquared_energy = psf.generate(track_trajectory)
    return signals_2d(subframes, actual_time, duration, track_light_curve, ensquared_energy), actual_time

