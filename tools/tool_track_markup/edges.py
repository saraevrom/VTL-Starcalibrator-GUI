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
        ranges.append([start_index, len(array), False])
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


nb.njit()
def splat_select(bool_arg, window):
    result_arr = np.full(bool_arg.shape[0]+window-1, False)
    for i in range(bool_arg.shape[0]):
        result_arr[i:i+window] = np.logical_or(bool_arg[i], result_arr[i:i+window])
    return result_arr


class EdgeProcessor(object):
    def __init__(self,threshold, edge_shift):
        self.threshold = threshold
        self.edge_shift = edge_shift


    def get_prob(self, data_source, ax):
        event_start, event_end = data_source.current_event
        x_data_true = data_source.file["data0"][event_start:event_end]
        x_data = data_source.apply_filter(x_data_true)
        # x_data = sliding_window_view(x_data, 128, axis=0)
        # x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        # y_data: np.ndarray = data_source.tf_model.predict(x_data)[:, 1]
        # xs = np.arange(event_start, event_end-127)
        data_source.tf_model.plot_over_data(x_data, ax)

    def apply(self, data_source):
        event_start, event_end = data_source.current_event
        x_data_true = data_source.file["data0"][event_start:event_end]
        x_data = data_source.apply_filter(x_data_true)
        booled = data_source.tf_model.trigger(x_data, self.threshold)
        # x_data = sliding_window_view(x_data, 128, axis=0)
        # x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        # y_data: np.ndarray = data_source.tf_model.predict(x_data)[:, 1]
        #
        # booled = y_data > self.threshold
        print("R0", booled)
        booled_full = splat_select(booled, 128)
        print("R1", booled_full)
        ranges = edged_intervals(booled_full)
        print("R2", ranges)

        # assert len(booled)>0
        # print(booled.shape)
        #
        # ranges = edged_intervals(booled)
        # print("R0", ranges)
        # if ranges[-1][2]:
        #     ranges.append([ranges[-1][1], len(x_data_true), False])
        # else:
        #     ranges[-1][1] = len(x_data_true)
        # print("R1", ranges)
        # fix_ranges(ranges)
        # print("R2", ranges)
        # # ranges = shift_positives(np.array(ranges), - self.edge_shift, 128 + self.edge_shift)
        # # print("R3", ranges)
        # fix_ranges(ranges)
        # print("R4", ranges)
        #
        return split_intervals(np.array(ranges), event_start)
