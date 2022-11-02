import numpy as np
import pandas as pd
from astropy.time import Time
from astropy.coordinates import EarthLocation
from plotter import HALF_GAP_SIZE, HALF_PIXELS, PIXEL_SIZE

def name_a_star(row):
    data = []
    if not pd.isnull(row["name_IAU"]):
        data.append(row["name_IAU"])
    if not pd.isnull(row["BayerFlamsteed"]):
        data.append(row["BayerFlamsteed"])
    if not pd.isnull(row["Hip"]) and row["Hip"]!=0:
        data.append(f"HIP {int(row['Hip'])}")
    if not pd.isnull(row["HR"]):
        data.append(f"HR {int(row['HR'])}")
    if not pd.isnull(row["Gliese"]):
        data.append(f"Gliese {row['Gliese']}")
    if data:
        if len(data) > 1:
            return f"{data[0]} ({', '.join(data[1:])})"
        else:
            return data[0]
    else:
        return f"UNKNOWN (StarID {row['StarID']})"

class Star(object):

    # ra, dec in radians
    def __init__(self, ra, dec, name):
        self.ra = ra
        self.dec = dec
        self.name = name

    @staticmethod
    def from_row(row):
        ra = row["RA"]*np.pi/12
        dec = row["Dec"]*np.pi/180
        return Star(ra, dec, name_a_star(row))

    def get_local_coords(self, era, dec, ra0, psi, f):
        phase = era + ra0 - self.ra
        z = np.sin(dec) * np.sin(self.dec) + np.cos(dec) * np.cos(self.dec) * np.cos(phase)
        x = np.sin(dec) * np.cos(self.dec) * np.sin(psi) * np.cos(phase) - \
            np.cos(dec) * np.sin(self.dec) * np.sin(psi) - \
            np.cos(psi) * np.sin(phase) * np.cos(self.dec)
        y = -np.sin(dec) * np.cos(self.dec) * np.cos(psi) * np.cos(phase) + \
            np.cos(dec) * np.sin(self.dec) * np.cos(psi) - \
            np.sin(psi) * np.sin(phase) * np.cos(self.dec)
        x1 = -x*f/z
        y1 = y*f/z
        return x1, y1, z > 0


def range_calculate(params:dict, t1: Time, t2:Time):
    ra0 = params["ra0"] * np.pi / 180
    dec0 = params["dec0"] * np.pi / 180

    half_size = HALF_GAP_SIZE+HALF_PIXELS*PIXEL_SIZE
    half_fov = np.arctan(half_size*2**0.5/params["f"])
    print(t1.to_datetime(), t2.to_datetime())
    era1 = t1.earth_rotation_angle(0).radian
    era2 = t2.earth_rotation_angle(0).radian

    print(era1, era2)
    print(ra0)
    ra_low = era1 + ra0 - half_fov
    ra_high = era2 + ra0 + half_fov
    dec_low = dec0 - half_fov
    dec_high = dec0 + half_fov
    return ra_low, ra_high, dec_low, dec_high
