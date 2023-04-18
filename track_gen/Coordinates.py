#function of coordinates
import numpy as np
#side "a" means along X axis
#side "b" means along Y axis
side_a = 8
side_b = 8
pixel_size_a = 1
pixel_size_b = 1

def Xmax():
    return (side_a/2)*pixel_size_a
def Xmin():
    return -(side_a/2)*pixel_size_a
def Ymax():
    return (side_b/2)*pixel_size_b
def Ymin():
    return -(side_b/2)*pixel_size_b
    
def ij2id(ij):
    N = len(ij[0])
    id = np.zeros((N))
    for i in range(N):
        if ij[0,i] >= 1 and ij[0,i] <= side_a and \
            ij[1,i] >= 1 and ij[1,i] <= side_b:
                id[i] = (ij[0,i] - 1)*side_b + \
                ij[1,i]
    return id[np.nonzero(id != 0)]

def id2ij(id):
    N = len(id)
    ij = np.zeros((2,N))
    ij[1] = 1 + np.remainder(id-1,side_b)
    ij[0] = 1 + (id - ij[1])/side_b
    return ij

def id2xy(id):
    N = len(id)
    ij = id2ij(id)
    xy = np.zeros((N,2))
    xy[:,0] = (side_a/2 + 0.5 - ij[0])*pixel_size_a
    xy[:,1] = (side_b/2 + 0.5 - ij[1])*pixel_size_b
    return xy

def xy2id(xy):
    N = len(xy)
    ij = np.zeros((2,N))
    ij[0] = np.ceil(side_a/2 - xy[:,0]/pixel_size_a)
    ij[1] = np.ceil(side_b/2 - xy[:,1]/pixel_size_b)
    id = ij2id(ij)
    return id
    
def ij2xy(ij):
    id = ij2id(ij)
    xy = id2xy(id)
    return xy
    
def xy2ij(xy):
    id = xy2id(xy)
    ij = id2ij(id)
    return ij

#A = np.array([np.arange(-1,5),np.arange(-1,5)])
#print(A)
#B = ij2id(A)
#print(B)
#C = id2xy(B)
#print(C)
#D = xy2id(C)
#print(D)