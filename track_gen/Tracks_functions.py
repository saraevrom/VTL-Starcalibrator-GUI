#Compilation of functions to simulate track-like events
import os	#manage folders
import numpy as np	#handling arrays
import matplotlib.pyplot as plt	#to plot
import matplotlib.gridspec as gridspec	#subplots
from scipy.optimize import curve_fit    #fit curves
from scipy.special import erf   #error function
import Coordinates as cor

####################################################
#Light curve
# The parameters are:
# LC_type -> type of LC, 
# par -> parameters [Tmax,Emax,Emin],
# Dk -> frames duration, 
# Nt -> division for each frame
def Light_curve(LC_type,par,Dk,Nt):
    dT = 1/Nt; T = np.arange(dT,Dk+dT,dT)
    
    Tmax = dT*np.floor(par[0]/dT)
    Emax = par[1]
    if LC_type == 'Triangular':
        if np.size(par) != 3:
            print('The parameters for Triangular \
            LC should be 3!')
        Emin = par[2]
        if Tmax < Dk:
            T1 = np.arange(dT,Tmax+dT,dT)
            T2 = np.arange(dT+Tmax,Dk+dT,dT)
            LC1 = Emin/Nt + ((Emax-Emin)/Nt) * (T1-dT)/(Tmax-dT)
            LC2 = Emin/Nt + ((Emax-Emin)/Nt) * (Dk-T2)/(Dk-dT-Tmax)
            LC = np.append(LC1,LC2)
        else:
            LC = Emin/Nt + ((Emax-Emin)/Nt) * (T-dT)/(Tmax-dT)
        return LC
        
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
def Gen_track(track_type,par,DURATION,Nt):
    X0 = par[0]; Y0 = par[1]; Phi0 = par[2]*np.pi/180
    U0 = par[3]; A = par[4]
    t = np.arange(1/Nt,DURATION,1/Nt)
    N = len(t)
    Rs_track = np.zeros((N,2))
    if track_type == 'Linear':
        if np.size(par) != 5:
            print('The parameters for Linear \
            track should be 5!')
        Rs_track[:,0] = X0 + (U0*t + (A/2)*t**2)*np.cos(Phi0)
        Rs_track[:,1] = Y0 + (U0*t + (A/2)*t**2)*np.sin(Phi0)

    if np.cos(Phi0) > 0:
        X_bound = cor.Xmax()
    else:
        X_bound = cor.Xmin()
    
    if np.sin(Phi0) > 0:
        Y_bound = cor.Ymax()
    else:
        Y_bound = cor.Ymin()
        
    kappa_X = 2*(X_bound - X0)/(U0*np.cos(Phi0))
    kappa_Y = 2*(Y_bound - Y0)/(U0*np.sin(Phi0))

    T_bound = np.amin([kappa_X/(1+np.sqrt(1 + kappa_X*A/U0)), \
        kappa_Y/(1 + np.sqrt(1 + kappa_Y*A/U0))])
    T_bound = np.floor(T_bound)
    
    Dk = int(np.amin([DURATION,T_bound]))
    IDs_track = np.unique(cor.xy2id(Rs_track))
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
    Pxs = cor.id2ij(IDs_track)
    IDs_simu = []
    for i in range(N):
        [mds, chs] = np.mgrid[Pxs[0,i]-1:Pxs[0,i]+2, \
            Pxs[1,i]-1:Pxs[1,i]+2]
        pxs = np.array([mds.flatten('F'),chs.flatten('F')])
        IDs_simu = np.append(IDs_simu,cor.ij2id(pxs))
    
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

def EE_gauss(dx,sigmax):
    ax = 1
    f = 0.5*(erf((dx + ax/2)/np.sqrt(2)/sigmax) - \
        erf((dx - ax/2)/np.sqrt(2)/sigmax))
        
    return f

####################################################
#Ensquared Energy
def EnsEnergy(IDs,center,psf_mode,psf_par):
    N = len(center)
    EEs = np.zeros((N,np.size(IDs)))
    
    if psf_mode == 'gauss_MC':  #this option is still not available 
        for i in range(1,N):
            IDs_ray = cor.xy2id(PSF_gauss(center[i,:],psf_par))
            EEs[i,:] = EE_MC(IDs,IDs_ray)
            
    if psf_mode == 'gauss':
        Rs = cor.id2xy(IDs)
        for i in range(N):
            EEs[i,:] = EE_gauss(Rs[:,0]-center[i,0],psf_par[0]) \
                *EE_gauss(Rs[:,1]-center[i,1],psf_par[1])
    
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
            SGNs[k1,:] = LC[ms]@EE[ms,:]
    
    return SGNs
    
#S = Signals(Dk,Nt,0,128,A[0],L,EE)
#print(S)

#plt.plot(S)
#plt.show()