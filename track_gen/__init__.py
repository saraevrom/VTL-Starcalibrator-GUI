import numpy as np
import numba as nb

from .track_dynamics import LinearTrack, Track
from .track_lightcurves import TriangularLightCurve, LightCurve
from .track_psf import GaussianPSF, TrackPSF
from track_gen.unused.coordinates import side_a, side_b


@nb.njit()
def signals_2d(subframes, actual_time, duration, lc, energies):
    SGNs = np.zeros((duration, side_a, side_b))
    #print("ENERGY TEST", energies[0])
    #print("LC TEST", lc[0])
    for k in range(actual_time):
        # SGNs[k] == 0 from start
        for k1 in range(k*subframes,subframes*(k+1)):
            SGNs[k] += lc[k1]*energies[k1]

    return SGNs

def generate_track(trajectory:Track, light_curve:LightCurve, psf:TrackPSF, duration, subframes):
    track_trajectory = trajectory.generate(duration, subframes)
    t_bound = trajectory.get_time_bound()
    actual_time = int(np.amin([duration, t_bound]))
    track_light_curve = light_curve.generate(actual_time, subframes)
    ensquared_energy = psf.generate(track_trajectory)
    return signals_2d(subframes, actual_time, duration, track_light_curve, ensquared_energy), actual_time

