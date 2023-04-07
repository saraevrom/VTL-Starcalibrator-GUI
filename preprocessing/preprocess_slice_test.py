import unittest
from denoising import slice_for_preprocess
import numpy as np

class SliceTest(unittest.TestCase):
    def test_consistency(self):
        arr = np.arange(20)
        start = 5
        end = 10
        margin = 4
        trunc, slicer = slice_for_preprocess(arr, start, end, margin)
        self.assertTrue((trunc[slicer]==arr[start:end]).all())

    def test_odd_margin(self):
        arr = np.arange(20)
        start = 5
        end = 10
        margin = 5
        trunc, slicer = slice_for_preprocess(arr, start, end, margin)
        self.assertTrue((trunc[slicer]==arr[start:end]).all())

    def test_consistency_low_bound(self):
        arr = np.arange(20)
        start = 2
        end = 10
        margin = 6
        trunc, slicer = slice_for_preprocess(arr, start, end, margin)
        self.assertTrue((trunc[slicer] == arr[start:end]).all())

    def test_consistency_high_bound(self):
        arr = np.arange(20)
        start = 2
        end = 17
        margin = 7
        trunc, slicer = slice_for_preprocess(arr, start, end, margin)
        self.assertTrue((trunc[slicer] == arr[start:end]).all())

