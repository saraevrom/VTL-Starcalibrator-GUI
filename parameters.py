import matplotlib.pyplot as plt
from multiprocessing import cpu_count

PIXEL_SIZE = 2.85
HALF_GAP_SIZE = 2.0
HALF_PIXELS = 8
PLOT_COLORMAP = plt.cm.viridis
PLOT_BROKEN_COLOR = "black"

NPROC = cpu_count()