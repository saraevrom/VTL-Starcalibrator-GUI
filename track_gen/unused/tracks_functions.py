#Compilation of functions to simulate track-like events
import os	#manage folders
import numpy as np	#handling arrays
import numba as nb
import matplotlib.pyplot as plt	#to plot
import matplotlib.gridspec as gridspec	#subplots
from scipy.optimize import curve_fit    #fit curves
from scipy.special import erf   #error function
from .coordinates import xy2id, ij2id, id2xy, id2ij, ij2xy_simple
from track_gen.track_dynamics import Track
from track_gen.track_lightcurves import LightCurve
from .coordinates import side_a, side_b

####################################################
#Light curve
# The parameters are:
# LC_type -> type of LC, 
# par -> parameters [Tmax,Emax,Emin],
# Dk -> frames actual_time,
# Nt -> division for each frame
def Light_curve(par:LightCurve, Dk, Nt):
    return par.generate(Dk, Nt)
        
#par = [80,100,50]; Dk = 128; Nt = 100
#L = Light_curve('Triangular',par,Dk,Nt)
#dT = 1/Nt; T = np.arange(dT,Dk+dT,dT)

#plt.plot(T,L)
#plt.show()

####################################################
#Generation of Track
# For Linear track the parameters should be:
# X0, Y0 -> initial points of the track
# Phi0 -> direction of the track (constant)
# U0 -> magnitud of initial velocity
# A -> magnitude of linear acceleration (constant)
def Gen_track(par:Track, DURATION, Nt):

    Rs_track = par.generate(DURATION, Nt)
    t_bound = par.get_time_bound()
    Dk = int(np.amin([DURATION,t_bound]))
    IDs_track = np.unique(xy2id(Rs_track))
    return IDs_track, Rs_track, Dk
    
#par = [-4,0,0.1,1,0]
#A = Gen_track('Linear',par,128,10)
#print(A[0])
#print(A[1])
#print(A[2])

####################################################
#Simulation of pixels
# IDs of pixels around the track

def Simu_pxs(IDs_track):
    N = len(IDs_track)
    Pxs = id2ij(IDs_track)
    IDs_simu = []
    for i in range(N):
        mds, chs = np.mgrid[Pxs[0,i]-1:Pxs[0,i]+2, Pxs[1,i]-1:Pxs[1,i]+2]


        pxs = np.array([mds.flatten('F'),chs.flatten('F')])
        IDs_simu = np.append(IDs_simu,ij2id(pxs))
    
    IDs_simu = np.unique(IDs_simu)
    return IDs_simu
    
#B = Simu_pxs(A[0])
#print(B)

####################################################
#Point Spread Function (PSF)

def PSF_gauss(R_c,psf_par):
    N_rays = psf_par[2]
    sigma2 = np.array([[psf_par[0]**2,0],[0,psf_par[1]**2]])
    
    Rs = R_c + np.random.normal(0,1,256,size=(N_rays,2))*np.linalg.cholesky(sigma2)
    
    return Rs

@nb.njit(nb.float64[:](nb.float64[:], nb.float64))
def EE_gauss(dx, sigmax):
    ax = 1
    f = np.zeros(shape=dx.shape)
    # scipy.special.erf requires argument to be float64 when working in numba
    # Using it with cycle. Since this code is compiled in numba "nopython" mode it will work fast.
    for i in range(dx.shape[0]):
        f[i] = 0.5*(erf((dx[i] + ax/2)/np.sqrt(2)/sigmax) - erf((dx[i] - ax/2)/np.sqrt(2)/sigmax))
    return f

####################################################
#Ensquared Energy

def EnsEnergy(IDs,center,psf_mode,psf_par):
    N = len(center)
    EEs = np.zeros((N,np.size(IDs)))
    
    # if psf_mode == 'gauss_MC':  #this option is still not available
    #     for i in range(1,N):
    #         IDs_ray = cor.xy2id(PSF_gauss(center[i,:],psf_par))
    #         EEs[i,:] = EE_MC(IDs,IDs_ray)
            
    if psf_mode == 'gauss':
        Rs = id2xy(IDs)
        for i in range(N):
            EEs[i,:] = EE_gauss(Rs[:,0]-center[i,0],psf_par[0]) \
                * EE_gauss(Rs[:,1]-center[i,1],psf_par[1])
    
    return EEs

    
#psf_par = [0.25,0.25]
#EE = EnsEnergy(A[0],A[1],'gauss',psf_par)
#print(EE[:,0])

####################################################
#Signals
def Signals(Dk,Nt,dk_start,Duration,IDs,LC,EE):
    SGNs = np.zeros((Duration,np.size(IDs)))
    for i in range(1,Dk):
        ms = np.arange(((i-1)*Nt + 1),(i*Nt)+1)
        k1 = i - dk_start
        if k1 >= 1 and k1 <= Duration:
            SGNs[k1,:] = LC[ms] @ EE[ms,:]

    # Change cycle to this to match my view

    # for i in range(Dk):
    #     ms = np.arange((i*Nt),((1+i)*Nt))
    #     k1 = i - dk_start
    #     if k1 >= 0 and k1 <= Duration:
    #         SGNs[k1,:] = LC[ms] @ EE[ms,:]
    
    return SGNs



    
#S = Signals(Dk,Nt,0,128,A[0],L,EE)
#print(S)

#plt.plot(S)
#plt.show()