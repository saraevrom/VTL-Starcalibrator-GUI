#Parameters to simulate one track-like event
import os	#manage folders
import numpy as np	#handling arrays
import matplotlib.pyplot as plt	#to plot
import matplotlib.gridspec as gridspec	#subplots
from scipy.optimize import curve_fit    #fit curves
from scipy.special import erf   #error function
import Coordinates as cor
import Tracks_functions as Trf
import pixel_map as PxM

####################################################
# (1) KINEMATICS:
#Dk is full duration should be <= min(DURATION, T_boundary)
DURATION = 128; Nt = 10
par = [-4,-3,0.1,0.125,0]    #[X0,Y0,Phi0,U0,A]
Track = Trf.Gen_track('Linear',par,DURATION,Nt)
IDs = Track[0]; Rc = Track[1]; Dk = Track[2]

####################################################
# (2) LIGHT CURVE: 
LC_par = [50,1,0.75] #[T_peak,E_peak,E_min] 
L = Trf.Light_curve('Triangular',LC_par,Dk,Nt)

####################################################
# (3) Find simu pixels
IDs_simu = Trf.Simu_pxs(IDs)
xy = cor.id2xy(IDs_simu)

####################################################
# (4) Calculate energy distribution for all sub-samples
psf_par = [0.1,0.1]
EE = Trf.EnsEnergy(IDs_simu,Rc,'gauss',psf_par)

####################################################
# (5) Signal generation: here Duration should be equals to Dk 
Duration = Dk; dt_start = 0
S = Trf.Signals(Dk,Nt,dt_start,Duration,IDs_simu,L,EE)
IS = np.sum(S,axis=1)

####################################################
#plot pixel map and Light curve
#PxM.Px_mp(xy)

#plot simulated signals
fig = plt.figure(figsize = (12,7))
plt.plot(S)
#plt.plot(IS,color='indigo')
plt.show()
