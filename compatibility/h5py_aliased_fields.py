import h5py
import numpy as np

SUBSTITUTIONS = {
    "data0":("pdm_2d_rot_global",False, float),
    "UT0": ("unixtime_dbl_global",True, float)
}

class AliasedDataFile(h5py.File):
    def __init__(self, *args,**kwargs):
        super().__init__(*args,**kwargs)

    def __getitem__(self, item):
        try:
            got_item = super().__getitem__(item)
            return got_item
        except KeyError as err:
            if item in SUBSTITUTIONS.keys():
                new_key, flatten, dtype = SUBSTITUTIONS[item]
                retrieved = super().__getitem__(new_key)
                if flatten:
                    return np.array(retrieved, dtype=dtype).flatten()
                else:
                    return np.array(retrieved, dtype=dtype)
            raise err