import h5py
import numpy as np


def overwrite_with_numpy(file, field, new_data):
    if field in file:
        del file[field]
    dset = file.create_dataset(field, data=np.array(new_data))
    return dset
