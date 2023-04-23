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

