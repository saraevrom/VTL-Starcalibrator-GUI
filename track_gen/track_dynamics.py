import numpy as np
from .pdm_params import Xmin, Xmax, Ymin, Ymax

class TrackTrajectory(object):
    '''
    Base class for track trajectory
    '''

    def generate(self, duration, nt):
        '''
        Create trajectory
        :param duration: Duration of event
        :param nt: Simulation subframes
        :return: Array with shape=(duration*nt,2). Coordinates of center
        '''
        raise NotImplementedError("Cannot generate track")

    def offset(self, dx, dy):
        '''
        Create new trajectory with offset
        :param dx: X offset.
        :param dy: Y offset.
        :return: New trajectory with offset origin
        '''
        raise NotImplementedError("Cannot offset track")

    def get_time_bound(self):
        '''
        Calculate time to reach boundaries
        :return: time until center of track event reaches boundary
        '''
        raise NotImplementedError("Cannot estimate time bound")


class LinearTrackTrajectory(TrackTrajectory):
    '''
    Linear trajectory
    '''
    def __init__(self, x0, y0, phi0, u0, a):
        '''

        :param x0: X coord of start
        :param y0: Y coord of start
        :param phi0: Direction angle coord of start
        :param u0: Initial speed
        :param a:  Acceleration
        '''
        self.x0 = x0
        self.y0 = y0
        self.phi0 = phi0
        self.u0 = u0
        self.a = a

    def offset(self,dx,dy):
        return LinearTrackTrajectory(
            self.x0+dx,
            self.y0+dy,
            self.phi0,
            self.u0,
            self.a
        )

    def generate(self, duration, nt):
        #t = np.arange(1 / Nt, actual_time, 1 / Nt)
        t = np.linspace(0.0, duration, nt * duration, endpoint=False)
        #t = np.linspace(1/nt, actual_time, nt * actual_time, endpoint=True)
        assert t[1] - t[0] == 1 / nt    # Caveat
        N = len(t)
        Rs_track = np.zeros((N, 2))
        Rs_track[:, 0] = self.x0 + (self.u0 * t + (self.a / 2) * t ** 2) * np.cos(self.phi0)
        Rs_track[:, 1] = self.y0 + (self.u0 * t + (self.a / 2) * t ** 2) * np.sin(self.phi0)
        return Rs_track

    def length(self, given_time):
        '''
        Get length of track event
        :param given_time: Total time given for movement
        :return: length of track
        '''
        time_bound = self.get_time_bound()
        return self.u0 * min(given_time, time_bound)

    def _get_xtime(self):
        if np.cos(self.phi0) > 0:
            x_bound = Xmax()
        else:
            x_bound = Xmin()
        kappa_x = 2 * (x_bound - self.x0) / (self.u0 * np.cos(self.phi0))
        x_time = kappa_x / (1 + np.sqrt(1 + kappa_x * self.a / self.u0))
        return x_time

    def _get_ytime(self):
        if np.sin(self.phi0) > 0:
            y_bound = Ymax()
        else:
            y_bound = Ymin()
        kappa_y = 2 * (y_bound - self.y0) / (self.u0 * np.sin(self.phi0))
        y_time = kappa_y / (1 + np.sqrt(1 + kappa_y * self.a / self.u0))
        return y_time

    def get_time_bound(self):
        if np.cos(self.phi0)==0:
            return self._get_ytime()
        elif np.sin(self.phi0)==0:
            return self._get_xtime()
        t_bound = np.amin([self._get_xtime(), self._get_ytime()])
        t_bound = np.floor(t_bound)
        return t_bound