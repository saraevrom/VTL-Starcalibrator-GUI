from multiprocessing import Process, Pipe
import tkinter as tk
import tkinter.ttk as ttk
import gc
import numpy as np
import time

import h5py

from vtl_common.localization import get_locale


def where_is_index(lengths, index):
    '''
    Get interval given index belongs to.
    :param lengths: interval length array.
    :param index: given index.
    :return: index of interval and truncated index.
    '''
    source_i = 0
    while index > lengths[source_i]:
        index -= lengths[source_i]
        source_i += 1
    return source_i, index

def where_is_index_inverse(lengths, index):
    '''
    Get interval given index belongs to (from end).
    :param lengths: interval length array.
    :param index: given index.
    :return: index of interval and truncated index.
    '''
    source_i = len(lengths)-1
    while index > lengths[source_i]:
        index -= lengths[source_i]
        source_i -= 1
    return source_i, index


def simplify_files(file_list, cutter, multiplier=1):
    '''
    Simplify representation of files for merging
    :param file_list: sit of files
    :param lcut: cut beginning
    :param rcut: cut ending
    :return: list of tuples with (filename, lcut, rcut)
    '''
    file_lengths = []
    full_len = 0
    for filename in file_list:
        with h5py.File(filename) as source_file:
            times = source_file['unixtime_dbl_global']
            file_len = times.shape[0]
            file_lengths.append(file_len)
            full_len += file_len
    lcut, rcut = cutter.cut(full_len)
    lcut *= multiplier
    rcut *= multiplier
    assert lcut < full_len
    assert rcut < full_len
    start_i,lcut1 = where_is_index(file_lengths, lcut)
    end_i,rcut1 = where_is_index_inverse(file_lengths, rcut)
    result = []
    for i in range(start_i, end_i+1):
        lcut_sub = 0
        rcut_sub = 0
        if i == start_i:
            lcut_sub = lcut1
        if i == end_i:
            rcut_sub = rcut1
        result.append((file_list[i], lcut_sub, rcut_sub))
    return result





class ParallelWorker(Process):
    def __init__(self, conn, filelist, output_filename, conf):
        super().__init__()
        self.conn = conn
        self.filelist = filelist
        self.output_filename = output_filename
        self.cutter = conf["cutter"]
        #self.lcut = conf["lcut"]
        #self.rcut = conf["rcut"]
        self.average_window = conf["average"]
        self.cut_units = conf["units"]

    def run(self):
        if self.cut_units == "Frames":
            multiplier = self.average_window
        else:
            multiplier = 1

        simplified_files = simplify_files(self.filelist, self.cutter, multiplier)
        start_time = time.time()

        with h5py.File(self.output_filename, "w") as output_file:
            data0 = output_file.create_dataset("data0", (1, 16, 16), dtype="f8", maxshape=(None, 16, 16))
            utc_time = output_file.create_dataset("UT0", (1,), dtype="f8", maxshape=(None,))
            dset_length = 0
            for file_index, file_data in enumerate(simplified_files):
                filename, lcut, rcut = file_data
                self.conn.send({
                    "msg":"FILE",
                    "name": filename,
                    "index": file_index+1,
                    "total": len(simplified_files),
                    "determinate": True
                })
                with h5py.File(filename, "r") as source_file:
                    times = source_file['unixtime_dbl_global']
                    signals = source_file["pdm_2d_rot_global"]
                    assert times.shape[0] == signals.shape[0]

                    if self.average_window == 1:
                        #Simple copy
                        self.conn.send({
                            "msg": "FRAME",
                            "determinate": False
                        })
                        appended_length = times.shape[0] - rcut - lcut  # Calculation here is simpler
                        write_pos = dset_length
                        dset_length += appended_length
                        data0.resize(dset_length, axis=0)
                        utc_time.resize(dset_length, axis=0)
                        if rcut == 0:
                            rcut = None   # We are not interested in cutting everything
                        else:
                            rcut = -rcut
                        data0[write_pos:] = signals[lcut:rcut]
                        utc_time[write_pos:] = times[lcut:rcut, 0]   # Matlab gives some shape magic  :D
                    else:
                        appended_length = len(range(lcut, times.shape[0] - rcut,
                                                    self.average_window))  # Calculate explicitly size of chunk
                        write_pos = dset_length
                        dset_length += appended_length
                        data0.resize(dset_length, axis=0)
                        utc_time.resize(dset_length, axis=0)
                        for progress, i in enumerate(range(lcut, times.shape[0] - rcut, self.average_window)):

                            data0[write_pos] = \
                                np.mean(signals[i:i+self.average_window], axis=0)
                            utc_time[write_pos] = times[i]
                            write_pos += 1

                            cur_time = time.time()
                            if cur_time > start_time+0.06:
                                start_time = cur_time
                                self.conn.send({
                                    "msg": "FRAME",
                                    "name": filename,
                                    "index": progress + 1,
                                    "total": appended_length,
                                    "determinate": True
                                })

                if self.conn.poll():
                    break
        self.conn.send({
            "msg": "STOP"
        })

class ConverterParallel(tk.Toplevel):
    def __init__(self, master, filelist, output_filename, conv_parameters):
        super().__init__(master)
        self.title(get_locale("mat_converter.title"))
        self.filelist = filelist
        self.output_filename = output_filename
        self.conv_parameters = conv_parameters
        self.current_file_display = tk.StringVar()
        tk.Label(self, textvariable=self.current_file_display).pack(side="top", fill="x")
        self.files_display = self._add_bar()
        self.frames_display = self._add_bar()
        parent_pipe, child_pipe = Pipe(duplex=True)
        self.conn = parent_pipe
        self.converter = ParallelWorker(child_pipe, filelist=filelist, output_filename=output_filename,
                                        conf=conv_parameters)
        gc.collect() # Free ram for our procedure
        self.converter.start()
        self.alive = True
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.after(10, self.monitor)

    def stop_process(self, force=False):
        self.conn.send(42)
        if force:
            self.converter.terminate()
            self.converter.kill()
        # Graceful exit
        self.converter.join()

    def __del__(self):
        if self.converter.is_alive():
            self.stop_process(True)
            print("Stopped process")

    def _add_bar(self):
        variable = tk.StringVar()
        frame = tk.Frame(self)
        frame.pack(side="top", fill="x")
        bar = ttk.Progressbar(frame, orient=tk.HORIZONTAL, length=100, mode="determinate")
        bar.pack(side="left", fill="x", expand=True)
        tk.Label(frame, textvariable=variable).pack(side="right")
        return variable, bar

    def set_bar(self, bar, pkg):
        if pkg["determinate"]:
            bar[1].stop()
            bar[1].configure(maximum=pkg['total'], value=pkg['index'], mode="determinate")
            bar[0].set(f"{pkg['index']}/{pkg['total']}")
        else:
            bar[1].configure(mode="indeterminate")
            bar[1].start()
            bar[0].set("---")


    def monitor(self):
        if self.conn.poll():
            pkg = self.conn.recv()
            if pkg["msg"] == "STOP":
                print("Process sent stop message")
                self.alive = False
            if pkg["msg"] == "FILE":
                self.current_file_display.set(pkg["name"])
                self.set_bar(self.files_display, pkg)
            if pkg["msg"] == "FRAME":
                self.set_bar(self.frames_display, pkg)
        if self.alive and self.converter.is_alive():
            self.after(10, self.monitor)
        else:

            self.converter.join()
            self.destroy()

    def on_closing(self):
        self.conn.send(42)
        print("Stopping process initiated")
