#!/usr/bin/env python3

#Parameters to simulate one track-like event
import numpy as np	#handling arrays
import matplotlib.pyplot as plt	#to plot
import track_gen.unused.coordinates as cor
import track_gen.unused.tracks_functions as Trf
import track_gen.unused.pixel_map as PxM
from track_gen import LinearTrack
from track_gen import TriangularLightCurve
from track_gen import GaussianPSF
from track_gen import generate_track



if __name__=="__main__":
    ####################################################
    # (1) KINEMATICS:
    #Dk is full actual_time should be <= min(DURATION, T_boundary)
    DURATION = 128; Nt = 10
    trajectory = LinearTrack(-4.333,-3.5,0.0,0.125,0)
    #trajectory = [-4,-3,0.1,0.125,0]    #[X0,Y0,Phi0,U0,A]

    IDs, Rc, Dk = Trf.Gen_track(trajectory,DURATION,Nt)
    #IDs = Track[0]; Rc = Track[1]; Dk = Track[2]

    ####################################################
    # (2) LIGHT CURVE:
    #lc_par = [50,1,0.75] #[T_peak,E_peak,E_min]
    lc_par = TriangularLightCurve(50, 1, 0.25)
    L = Trf.Light_curve(lc_par, Dk, Nt)

    ####################################################
    # (3) Find simu pixels
    IDs_simu = Trf.Simu_pxs(IDs)
    print("ID_simu:", IDs_simu)
    xy = cor.id2xy(IDs_simu)

    ####################################################
    # (4) Calculate energy distribution for all sub-samples
    psf_par = (0.25,0.25)
    psf_par_obj = GaussianPSF(*psf_par)
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
    #fig = plt.figure(figsize = (12,7))
    fig, (ax1,ax2) = plt.subplots(1,2)
    ax1.plot(S)
    ax1.plot(IS,color='indigo')


    #OK now my turn
    track_data = generate_track(trajectory, lc_par, psf_par_obj,DURATION, 10)
    for i in range(8):
        for j in range(8):
            ax2.plot(track_data[:, i, j])
    ax2.plot(np.sum(track_data,axis=(1,2)), "--")
    plt.show()

    fig, ax = plt.subplots()
    PxM.plot_ij(track_data, ax)