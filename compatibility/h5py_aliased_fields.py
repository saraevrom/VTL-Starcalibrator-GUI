import h5py
import numpy as np
from tkinter.simpledialog import askinteger
from vtl_common.parameters import ALLOW_MAT_MODIFICATION
from .gigastats import get_median
import numba as nb


@nb.njit()
def generate_old(ngtu_global,length, mul):
    res = np.zeros(shape=(length,))
    for i in range(length):

        res[i] = (ngtu_global[i//128, 0] + (i%128)*mul)*2.5e-6

        #if i>0:
        #    assert res[i]>res[i-1]
    return res

def ut0_workaround(fp):
    if "ngtu_global" in fp.keys():
        # Dealing with old D1
        ngtu_global = np.array(fp["ngtu_global"])

        length = fp["pdm_2d_rot_global"].shape[0]
        mul = fp.dmul
        if mul is None:
            mul = askinteger("D1=1; D3=16384", "MUL=")
            if mul is None:
                mul = 1
            fp.dmul = mul
        assert ngtu_global.shape[0]*128==length
        return generate_old(ngtu_global, length,mul)

    return np.arange(fp["pdm_2d_rot_global"].shape[0])

SUBSTITUTIONS = {
    "data0":(["pdm_2d_rot_global",], (lambda x: x), None),
    "UT0": (["unixtime_dbl_global",], (lambda x: x[:,0]), ut0_workaround)
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
        self.dmul = None

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
                new_keys, transformation, workaround = SUBSTITUTIONS[item]
                retrieved = None
                found = False
                for k in new_keys:
                    succ = False
                    try:
                        retrieved = super().__getitem__(k)
                        succ = True
                        found = True
                    except KeyError:
                        pass
                    if succ:
                        break

                if found:
                    return transformation(retrieved)
                else:
                    return workaround(self)
            print(f"Key \"{item}\" is missing in substututions")
            raise err