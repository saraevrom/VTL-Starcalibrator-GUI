import h5py
import numpy as np
import psutil, os

from .h5py_aliased_fields import AliasedDataFile
from friendliness import show_attention


def get_mean_image(f:h5py.File):
    """
    Returns the mean_image of a xs dataset.
    :param str filepath: Filepath of the data upon which the mean_image should be calculated.
    :return: ndarray xs_mean: mean_image of the x dataset.
    """
    filepath = f.filename

    # check available memory and divide the mean calculation in steps
    total_memory = 0.5 * psutil.virtual_memory().available # In bytes. Take 1/2 of what is available, just to make sure.
    filesize = os.path.getsize(filepath)
    steps = int(np.ceil(filesize/total_memory))
    n_rows = f['data0'].shape[0]
    stepsize = int(n_rows / float(steps))

    xs_mean_arr = np.zeros((steps, ) + f['data0'].shape[1:], dtype=np.float64)
    for i in range(steps):
        # if xs_mean_arr is None: # create xs_mean_arr that stores intermediate mean_temp results
        #     xs_mean_arr = np.zeros((steps, ) + f['data0'].shape[1:], dtype=np.float64)

        if i == steps-1: # for the last step, calculate mean till the end of the file
            src = f['data0'][i * stepsize: n_rows]
            xs_mean_temp = np.median(src, axis=0)
        else:
            src = f['data0'][i*stepsize : (i+1) * stepsize]
            xs_mean_temp = np.median(src, axis=0)
        xs_mean_arr[i] = xs_mean_temp

    xs_mean = np.median(xs_mean_arr, axis=0, dtype=np.float64).astype(np.float64)

    return xs_mean


def fix_minima(filename):
    with AliasedDataFile(filename, "a") as fp:
        if "means" not in fp.keys():
            means = np.median(fp["data0"], axis=0)
            fp.create_dataset("means",data=means, dtype=np.float64)
            print("Minima fixed")
            show_attention("add_means")
        else:
            print("Mean data is present")