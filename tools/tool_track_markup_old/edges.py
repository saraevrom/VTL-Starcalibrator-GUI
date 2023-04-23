import gc

import numba as nb
import numpy as np
from numpy.lib.stride_tricks import sliding_window_view


@nb.njit()
def edged_intervals(array):
    persistent_value = False
    ranges = []
    start_index = 0
    for i in range(len(array)):
        v = array[i]
        # rising edge
        if v and not persistent_value:
            end_index = i
            if start_index < end_index:
                ranges.append([start_index, end_index, False])
            start_index = i
            persistent_value = v

        #falling edge
        if persistent_value and not v:
            end_index = i
            if start_index < end_index:
                ranges.append([start_index, end_index, True])
            start_index = i
            persistent_value = v

    if len(ranges) == 0:
        ranges.append([start_index, len(array), bool(array[start_index])])
    elif start_index < len(array):
        ranges.append([start_index, len(array), not ranges[-1][2]])

    return ranges



@nb.njit()
def shift_positives_npy(array, left_shift, right_shift):
    res = []

    start, end, positive = array[0]
    if positive:
        start1 = start
        end1 = end+right_shift
    else:
        start1 = start
        end1 = end + left_shift
    res.append([start1, end1, positive])

    if len(array) <= 2:
        return res

    for i in range(1, len(array)-1):
        start, end, positive = array[i]
        if positive:
            start1 = start + left_shift
            end1 = end + right_shift
        else:
            start1 = start + right_shift
            end1 = end + left_shift
        res.append([start1, end1, positive])

    start, end, positive = array[len(array)-1]
    if positive:
        start1 = start + left_shift
        end1 = end
    else:
        start1 = start + right_shift
        end1 = end
    res.append([start1, end1, positive])
    return res


def shift_positives(array, left_shift, right_shift):
    if len(array)<=1:
        return array.tolist()
    else:
        return shift_positives_npy(array, left_shift, right_shift)

@nb.njit()
def split_intervals(array,offset=0):
    positive = []
    negative = []
    for v in array:
        if v[-1]:
            positive.append([v[0]+offset, v[1]+offset])
        else:
            negative.append([v[0]+offset, v[1]+offset])
    return positive, negative


def fix_ranges(ranges):
    # fix beginning
    while ranges and ranges[0][0] > ranges[0][1]:
        oldstart, oldend, oldpos = ranges.pop(0)
        ranges[0][0] = oldstart

    # fix ending
    while ranges and ranges[-1][0] > ranges[-1][1]:
        oldstart, oldend, oldpositive = ranges.pop(-1)
        ranges[-1][1] = oldend

    i = 1
    # fix middle
    while i < len(ranges) - 1:
        c_start, c_end, c_positive = ranges[i]
        if c_start < c_end:
            i += 1
        else:
            ranges.pop(i)  # already saved as c_<...>
            n_start, n_end, n_positive = ranges.pop(i)
            assert n_positive == ranges[i - 1][-1]  # ensure we are stitching same polarity
            ranges[i - 1][1] = n_end





class EdgeProcessor(object):
    def __init__(self,threshold, edge_shift=None, stabilize_slide=True, max_plot=5000):
        self.threshold = threshold
        self.edge_shift = edge_shift
        self.stabilize_slide=stabilize_slide
        self.max_plot = max_plot

    # DO NOT COMPLICATE
    # def _get_xdata(self, data_source):
    #     gc.collect()
    #     event_start, event_end = data_source.current_event
    #     # x_data_true = np.array(data_source.file["data0"][event_start:event_end])
    #     filt_obj = data_source.get_filter(True)
    #     x_data_true, xdatacut = filt_obj.prepare_array(data_source.file["data0"], event_start, event_end)
    #     #filt = data_source.get_filter_for_nn()
    #     #broken = data_source.get_broken()
    #     x_data = data_source.apply_filter(x_data_true, True)
    #     x_data = x_data[xdatacut]
    #     return x_data
    #
    # def get_prob(self, data_source, ax):
    #     event_start, event_end = data_source.current_event
    #     length = event_end-event_start
    #     if length > self.max_plot:
    #         return
    #     # x_data_true = np.array(data_source.file["data0"][event_start:event_end])
    #
    #     x_data_true = self._get_xdata(data_source)
    #     data_source.tf_model.plot_over_data(x_data_true,event_start, event_end, ax)
    #
    # def get_triggering(self, data_source, plot_data):
    #     data_source.tf_model.stabilize_slide = self.stabilize_slide
    #     res = data_source.tf_model.trigger_split(plot_data, self.threshold)
    #     # print("RES",res)
    #     return [obj.any() for obj in res]
    #
    # def apply(self, data_source):
    #     x_data = self._get_xdata(data_source)
    #     event_start, event_end = data_source.current_event
    #     booled_full = data_source.tf_model.trigger(x_data, self.threshold)
    #     print("R1", booled_full)
    #     ranges = edged_intervals(booled_full)
    #     print("R2", ranges)
    #
    #     # assert len(booled)>0
    #     # print(booled.shape)
    #     #
    #     # ranges = edged_intervals(booled)
    #     # print("R0", ranges)
    #     # if ranges[-1][2]:
    #     #     ranges.append([ranges[-1][1], len(x_data_true), False])
    #     # else:
    #     #     ranges[-1][1] = len(x_data_true)
    #     # print("R1", ranges)
    #     # fix_ranges(ranges)
    #     # print("R2", ranges)
    #     # # ranges = shift_positives(np.array(ranges), - self.edge_shift, 128 + self.edge_shift)
    #     # # print("R3", ranges)
    #     # fix_ranges(ranges)
    #     # print("R4", ranges)
    #     #
    #     return split_intervals(np.array(ranges), event_start)
