import numpy as np
import numba as nb

side_a = 8
side_b = 8
pixel_size_a = 1
pixel_size_b = 1


@nb.njit()
def Xmax():
    return (side_a/2)*pixel_size_a

@nb.njit()
def Xmin():
    return -(side_a/2)*pixel_size_a

@nb.njit()
def Ymax():
    return (side_b/2)*pixel_size_b

@nb.njit()
def Ymin():
    return -(side_b/2)*pixel_size_b


@nb.njit()
def ij_to_xy(ij):
    i,j = ij
    x = (-side_a / 2 + 0.5 + i) * pixel_size_a
    y = (-side_b / 2 + 0.5 + j) * pixel_size_b
    return x,y