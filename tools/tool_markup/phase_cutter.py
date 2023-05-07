import numpy as np
from .storage import Interval


class PhaseCutter(object):
    def __init__(self, lower_duration, upper_duration, lower_intensity):
        self.lower_duration = lower_duration
        self.upper_duration = upper_duration
        self.lower_intensity = lower_intensity

    def draw_on_plot(self, axes, max_y):
        traj_x = [self.lower_duration, self.lower_duration, self.upper_duration, self.upper_duration]
        traj_y = [max_y, self.lower_intensity, self.lower_intensity, max_y]
        axes.plot(traj_x, traj_y, "--", color="black")

    def test_tp(self, data, interval:Interval):
        intensity = np.max(data)
        length = interval.length()
        print("FALSE POSITIVE FILTERING:")
        print("Intensity:", intensity)
        print("(lower pass)", self.lower_intensity)
        print("DURATION:", length)
        return (self.lower_intensity<=intensity) and (self.lower_duration<=length<=self.upper_duration)