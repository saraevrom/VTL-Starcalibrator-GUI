from common_GUI.plotter import GridPlotter
import numpy as np
import colorsys

def star_id_to_rgb(i):
    hue = (2/3+np.pi/12*i) % 1
    r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
    r = min(int(r*255), 255)
    g = min(int(g * 255), 255)
    b = min(int(b * 255), 255)

    print(r,g,b)
    return '#%02x%02x%02x' % (r,g,b)
class StarGridPlotter(GridPlotter):
    def __init__(self, master, norm=None, *args, **kwargs):
        super(StarGridPlotter, self).__init__(master, norm, *args, **kwargs)
        self.lines = dict()

    def set_line(self, key, xs, ys, label=""):
        if key in self.lines.keys():
            line = self.lines[key]
            line.set_xdata(xs)
            line.set_ydata(ys)
        else:
            line, = self.axes.plot(xs, ys, "-o", label=label, color= star_id_to_rgb(key))
            self.lines[key] = line


    def remove_line(self, key):
        if key in self.lines.keys():
            self.lines[key].remove()
            del self.lines[key]

    def delete_lines(self):
        for key in self.lines.keys():
            self.lines[key].remove()
        self.lines.clear()
        self.axes.set_prop_cycle(None)

    def draw(self):
        self.axes.legend()
        super(StarGridPlotter, self).draw()