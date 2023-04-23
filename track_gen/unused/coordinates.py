#function of coordinates
import numpy as np
import  numba as nb
#side "a" means along X axis
#side "b" means along Y axis
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


@nb.njit(cache=True)
def ij2id(ij):
    N = len(ij[0])
    id_ = np.zeros((N))
    for i in range(N):
        if ij[0,i] >= 1 and ij[0,i] <= side_a and \
            ij[1,i] >= 1 and ij[1,i] <= side_b:
                id_[i] = (ij[0,i] - 1)*side_b + \
                ij[1,i]
    return id_[np.nonzero(id_ != 0)]

@nb.njit(cache=True)
def id2ij(id_):
    N = len(id_)
    ij = np.zeros((2,N))
    ij[1] = 1 + np.remainder(id_-1,side_b)
    ij[0] = 1 + (id_ - ij[1])/side_b
    return ij

@nb.njit(cache=True)
def id2xy(id_):
    N = len(id_)
    ij = id2ij(id_)
    xy = np.zeros((N,2))
    xy[:,0] = (side_a/2 + 0.5 - ij[0])*pixel_size_a
    xy[:,1] = (side_b/2 + 0.5 - ij[1])*pixel_size_b
    return xy

@nb.njit(cache=True)
def xy2id(xy):
    N = len(xy)
    ij = np.zeros((2,N))
    ij[0] = np.ceil(side_a/2 - xy[:,0]/pixel_size_a)
    ij[1] = np.ceil(side_b/2 - xy[:,1]/pixel_size_b)
    id = ij2id(ij)
    return id

@nb.njit(cache=True)
def ij2xy(ij):
    id_ = ij2id(ij)
    xy = id2xy(id_)
    return xy

@nb.njit(cache=True)
def xy2ij(xy):
    id_ = xy2id(xy)
    ij = id2ij(id_)
    return ij


@nb.njit()
def ij2xy_simple(ij):
    i,j = ij
    x = (-side_a / 2 + 0.5 + i) * pixel_size_a
    y = (-side_b / 2 + 0.5 + j) * pixel_size_b
    return x,y

#A = np.array([np.arange(-1,5),np.arange(-1,5)])
#print(A)
#B = ij2id(A)
#print(B)
#C = id2xy(B)
#print(C)
#D = xy2id(C)
#print(D)