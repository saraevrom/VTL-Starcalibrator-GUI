import psutil, os
import h5py
import numpy as np
from scipy.optimize import minimize

import tqdm
import numba as nb

from .h5py_aliased_fields import AliasedDataFile
from friendliness import show_attention, check_mat
from .gigastats import get_median
from vtl_common.parameters import USE_MANDATORY_FLATFIELDING



def fix_minima(filename):
    if USE_MANDATORY_FLATFIELDING:
        if check_mat(filename, False):
            with AliasedDataFile(filename, "a") as fp:
                if "means" not in fp.keys():
                    means = get_median(fp)
                    fp.create_dataset("means",data=means, dtype=np.float64)
                    print("Minima fixed")
                    show_attention("add_means",0)
                else:
                    print("Mean data is present")
        else:
            print("Skipped mean test")
    else:
        print("Mandatory FF is disabled")