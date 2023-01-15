from common_GUI.plotter import Plotter
import numpy as np


class SignalPlotter(Plotter):
    def __init__(self, master, *args, **kwargs):
        super(SignalPlotter, self).__init__(master, *args, **kwargs)
        self.axes.grid()
        self.left_line, = self.axes.plot([0, 0], [0, 1000], "-", color="black")
        self.right_line, = self.axes.plot([0, 0], [0, 1000], "-", color="black")
        self.left_cut = 0
        self.right_cut = 0
        self.remembered_length = 0
        self.plots = []

    def view_x(self, left, right):
        self.axes.set_xlim(left, right)

    def view_y(self, bottom, top):
        self.axes.set_ylim(bottom, top)

    def set_xrange(self, left, right):
        if left > right:
            left, right = right, left
        # print(left, right)
        self.left_line.set_xdata([left, left])
        self.right_line.set_xdata([right, right])
        self.left_cut = left
        self.right_cut = right

    def set_yrange(self, bottom, top):
        if bottom > top:
            bottom, top = top, bottom
        # print(bottom, top)
        self.left_line.set_ydata([bottom, top])
        self.right_line.set_ydata([bottom, top])

    def plot_data(self,drawing_data):
        datalen = drawing_data.shape[0]
        if datalen == self.remembered_length:
            assert len(self.plots)>0
            self._plot_data(drawing_data, True)
        else:
            self._plot_data(drawing_data, False)
            self.remembered_length = datalen

    def _plot_data(self, drawing_data, fastplot=False):
        xs = np.arange(0,drawing_data.shape[0],1)
        if not fastplot:
            for l in self.plots:
                l.remove()
            self.axes.set_prop_cycle(None)
            self.plots.clear()
        for i in range(16):
            for j in range(16):
                ys = drawing_data[:, i, j]
                if fastplot:
                    self.plots[i*16+j].set_ydata(ys)
                else:
                    line, = self.axes.plot(xs, ys)
                    self.plots.append(line)