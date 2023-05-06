import h5py
import numpy as np

from .h5py_aliased_fields import AliasedDataFile
from friendliness import show_attention

def fix_minima(filename):
    with AliasedDataFile(filename, "a") as fp:
        if "means" not in fp.keys():
            d0 = fp["data0"]
            means = np.mean(d0, axis=0)
            fp.create_dataset("means",data=means)
            print("Minima fixed")
            show_attention("add_means")
        else:
            print("Mean data is present")