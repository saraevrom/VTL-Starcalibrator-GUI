import h5py
import numpy as np
from vtl_common.parameters import ALLOW_MAT_MODIFICATION
from .gigastats import get_median


SUBSTITUTIONS = {
    "data0":("pdm_2d_rot_global", lambda x: x),
    "UT0": ("unixtime_dbl_global", lambda x: x[:,0])
}

class MatViolationError(Exception):
    def __init__(self, filename):
        super().__init__(f"Attempted to modify {filename}")


class SafeMatHDF5(h5py.File):
    def __init__(self, *args,**kwargs):
        if args:
            filename = args[0]
        elif "name" in kwargs.keys():
            filename = kwargs["name"]
        else:
            filename = None

        if (filename is not None) and isinstance(filename, str):
            is_mat = filename.endswith(".mat")
        else:
            is_mat = False

        if len(args)>=2:
            rmode = args[1]
        elif "mode" in kwargs.keys():
            rmode = kwargs["mode"]
        else:
            rmode = None

        if rmode is not None:
            if rmode!="r" and not ALLOW_MAT_MODIFICATION and is_mat:
                raise MatViolationError(filename)
        super().__init__(*args,**kwargs)

class AliasedDataFile(SafeMatHDF5):
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)
        self._means = None

    def __getitem__(self, item):
        if item == "means":
            try:
                return super().__getitem__("means")
            except KeyError:
                if self._means is None:
                    print("Creating temporary mean values")
                    self._means = get_median(self)
                return self._means.copy()

        try:
            got_item = super().__getitem__(item)
            return got_item
        except KeyError as err:
            if item in SUBSTITUTIONS.keys():
                new_key, transformation = SUBSTITUTIONS[item]
                retrieved = super().__getitem__(new_key)
                return transformation(retrieved)
            print(f"Key \"{item}\" is missing in substututions")
            raise err