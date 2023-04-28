import numpy as np
import numba as nb

SIDE_A = 8
SIDE_B = 8
PIXEL_SIZE_A = 1
PIXEL_SIZE_B = 1


@nb.njit()
def Xmax():
    return (SIDE_A / 2)*PIXEL_SIZE_A

@nb.njit()
def Xmin():
    return -(SIDE_A / 2)*PIXEL_SIZE_A

@nb.njit()
def Ymax():
    return (SIDE_B / 2)*PIXEL_SIZE_B

@nb.njit()
def Ymin():
    return -(SIDE_B / 2)*PIXEL_SIZE_B


@nb.njit()
def ij_to_xy(ij):
    i,j = ij
    x = (-SIDE_A / 2 + 0.5 + i) * PIXEL_SIZE_A
    y = (-SIDE_B / 2 + 0.5 + j) * PIXEL_SIZE_B
    return x,y