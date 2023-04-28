import numpy as np

class LightCurve(object):
    '''
    Base class for light curves
    '''

    def __init__(self, end_time=None):
        self.end_time = end_time

    def set_time_bound(self,t):
        '''
        Override end time. Can be useful if track is generated for 4 pmts
        :param t: time for override
        :return:
        '''
        self.end_time = int(t)

    def get_curve(self, Dk, Nt):
        '''
        Create light curve
        :param Dk: Frames. Usage of this argument can be suppressed by set_time_bound method.
        :param Nt: Subframes
        :return:
        '''
        if self.end_time is None:
            Dk = Dk
        else:
            Dk = self.end_time
        return self.generate(Dk, Nt)

    def generate(self, Dk, Nt):
        '''

        :param Dk: Required frames
        :param Nt: Subframes
        :return: Dk*Nt array of lightcurve
        '''
        raise NotImplementedError("Cannot generate light curve")



class TriangularLightCurve(LightCurve):
    def __init__(self,t_peak,e_peak,e_min, end_time=None):
        self.t_peak = t_peak
        self.e_peak = e_peak
        self.e_min = e_min
        super().__init__(end_time)


    def generate(self, Dk, Nt):
        dT = 1 / Nt
        #T = np.arange(dT, Dk + dT, dT)
        T = np.linspace(0,Dk,Dk*Nt,endpoint=False)
        #T = np.linspace(dT,Dk,Dk*Nt,endpoint=True)

        Tmax = dT * np.floor(self.t_peak / dT)
        Emax = self.e_peak
        Emin = self.e_min
        if Tmax > Dk:
            LC = Emin / Nt + ((Emax - Emin) / Nt) * (T - dT) / (Tmax - dT)
        elif Tmax<=dT:
            LC = Emin / Nt + ((Emax - Emin) / Nt) * (Dk - T) / (Dk - dT - Tmax)
        else:
            LC1 = Emin / Nt + ((Emax - Emin) / Nt) * (T - dT) / (Tmax - dT)
            LC2 = Emin / Nt + ((Emax - Emin) / Nt) * (Dk - T) / (Dk - dT - Tmax)
            if Emax>Emin:
                LC = np.minimum(LC1,LC2)
            else:
                LC = np.maximum(LC1, LC2)
        return LC