from common_GUI import Plotter
from ..tool_track_markup.denoising import reduce_noise, antiflash, moving_average_subtract
import numpy as np


class BgPickingEditor(Plotter):
    def __init__(self, master):
        super().__init__(master)

    def clear(self):
        for line in self.axes.lines:
            line.remove()

    def display_data(self,file, ff_model=None):
        ys = np.array(file["data0"])
        ys = ff_model.apply(ys)
        print(ys.shape)
        ys = moving_average_subtract(ys, 10)

        ys = reduce_noise(ys, 10)
        ys = antiflash(ys)

        if ff_model:
            ys[:, ff_model.get_broken()] = 0

        xs = np.arange(ys.shape[0])
        #self.axes.plot(xs, np.max(ys, axis=(1, 2)))
        # for i in range(HALF_PIXELS*2):
        #     for j in range(HALF_PIXELS * 2):
        maxes = np.max(ys, axis=0)
        maxes_argsorted = np.dstack(np.unravel_index(np.argsort(maxes.ravel()), maxes.shape))[0]
        maxed_indices = maxes_argsorted[-10:]
        print(maxed_indices.shape)
        for ij in maxed_indices:
                i,j = ij
                self.axes.plot(xs, ys[:, i, j])
