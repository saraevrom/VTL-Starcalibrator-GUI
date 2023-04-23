#Draw the pixel map of active pixels
import os	#manage folders
import numpy as np	#handling arrays
import matplotlib.pyplot as plt	#to plot
import matplotlib.gridspec as gridspec	#subplots
from scipy.optimize import curve_fit    #fit curves
from scipy.special import erf   #error function
from .coordinates import Xmin, Xmax, Ymin, Ymax

###################################################################
#colors
colors = ['b','r','g','m','y','c','orangered','lime','royalblue', \
'darkviolet','crimson','orange','sienna','purple','firebrick','gold', \
'lawngreen','slateblue','turquoise','blueviolet','yellow','green', \
'paleturquoise','dodgerblue','indigo','darkorchid','magenta', \
'gainsboro','maroon','chocolate','peru','darkkhaki','yellowgreen', \
'greenyellow','forestgreen','aqua','palevioletred','springgreen', \
'teal','deepskyblue','violet','steelblue','pink','blue','mediumblue', \
'fuchsia','dimgrey','darkorange','darkgoldenrod','olive','aquamarine', \
'rebeccapurple','plum','orchid','deeppink','grey','red','tan', \
'chartreuse','palegreen','navy','mediumvioletred','hotpink','silver', \
'tomato','beige']

####################################################
#plot pixel map
def Px_mp(xy):
    fig = plt.figure(figsize = (6,6))
    for i in range(len(xy)):
        plt.plot(xy[i,0],xy[i,1],marker='s',markersize=40,color=colors[i])
    plt.grid(True, which = 'both', alpha = 1)
    plt.axis([Xmin(),Xmax(),Ymin(),Ymax()])
    plt.show()


def plot_ij(plot_data_3d,ax):
    dat = np.max(plot_data_3d, axis=0)
    ax.matshow(dat)