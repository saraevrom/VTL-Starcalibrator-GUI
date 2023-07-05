import os, psutil
from multiprocessing import Pool

import h5py
import numpy as np
import tqdm
from vtl_common.parameters import NPROC



class FileTarget(object):
    def __init__(self, filename, skip=1):
        self.filename = filename
        self.skip = skip

    def __call__(self, range_):
        start, end = range_
        with h5py.File(self.filename, "r") as fp:
            try:
                return fp["data0"][start:end:self.skip]
            except KeyError:
                return fp["pdm_2d_rot_global"][start:end:self.skip].astype(float)

def create_intervals(start, end, step):
    index = start
    while index<end:
        l_start = index
        l_end = index+step
        if l_end>end:
            l_end = end
        if l_end-l_start>0:
            yield l_start, l_end

        index += step


def get_median(srcf: h5py.File):
    total_memory = psutil.virtual_memory().available/16  # In bytes. Take 1/8 of what is available, just to make sure.
    filepath = srcf.filename
    filesize = os.path.getsize(filepath)
    parts = int(np.ceil(filesize/total_memory))
    print(f"Splitting in {parts} parts")
    frames = srcf["data0"].shape[0]//parts
    #print(f"Will take {frames} frames")
    if frames >= srcf["data0"].shape[0]:
        print("Using direct median")
        return np.median(srcf["data0"], axis=0)
    else:
        chunk_len = srcf["data0"].chunks[0]
        #assert srcf["data0"].shape[0]%chunk_len == 0
        assert srcf["data0"].chunks[1] == 16
        assert srcf["data0"].chunks[2] == 16
        dset = srcf["data0"]

        #start = (srcf["data0"].shape[0]-frames)//2
        #start = start//chunk_len*chunk_len # align with chunks
        #frames = frames//chunk_len*chunk_len # align with chunks
        end = srcf["data0"].shape[0]//chunk_len*chunk_len

        callable_ = FileTarget(filepath, parts)

        pool = Pool(NPROC)
        with pool:
            #sources = pool.map(callable_, create_intervals(start, start+frames, frames//NPROC))
            sources = pool.map(callable_, create_intervals(0, end, end//NPROC))
        print("Loaded data")
        source = np.concatenate(sources)

        return np.median(source, axis=0)
