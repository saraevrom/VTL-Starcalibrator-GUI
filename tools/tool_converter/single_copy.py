#import h5py
import numpy as np
import tqdm
from compatibility.h5py_aliased_fields import SafeMatHDF5


def average_single_file(src, dst, lcut, rcut, average_window):
    with SafeMatHDF5(src, "r") as input_file:
        file_len = len(input_file['unixtime_dbl_global'])
        frames = len(range(lcut, file_len-rcut, average_window))
        pointer = 0
        with SafeMatHDF5(dst, "w") as output_file:
            data0 = output_file.create_dataset("data0", (frames, 16, 16), dtype="f8")
            utc_time = output_file.create_dataset("UT0", (frames,), dtype="f8")
            print("FROM", lcut, "TO", file_len-rcut, "STEP", average_window)
            for i in tqdm.tqdm(range(lcut, file_len-rcut, average_window)):
                data0[pointer] = np.mean(input_file["pdm_2d_rot_global"][i:i + average_window], axis=0)
                utc_time[pointer] = input_file['unixtime_dbl_global'][i][0]
                pointer += 1