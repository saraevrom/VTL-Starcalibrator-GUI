import matplotlib.pyplot as plt
from multiprocessing import cpu_count


MAIN_LATITUDE = 68.607279
MAIN_LONGITUDE = 31.803085

PIXEL_SIZE = 2.85
HALF_GAP_SIZE = 2.0
HALF_PIXELS = 8

PLOT_COLORMAP = plt.cm.viridis
PLOT_BROKEN_COLOR = "black"
PLOT_HIGHLIGHT_COLOR = "red"

NPROC = cpu_count()

LOCALE = "en"

SCALE_FLOATING_POINT_FORMAT = "{:.2f}"

DATETIME_FORMAT= '%Y-%m-%d %H:%M:%S'