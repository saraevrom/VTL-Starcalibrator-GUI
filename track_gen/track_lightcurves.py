import numpy as np

class LightCurve(object):
    def generate(self,Dk,Nt):
        raise NotImplementedError("Cannot generate light curve")


class TriangularLightCurve(LightCurve):
    def __init__(self,t_peak,e_peak,e_min):
        self.t_peak = t_peak
        self.e_peak = e_peak
        self.e_min = e_min

    def generate(self,Dk,Nt):
        dT = 1 / Nt
        #T = np.arange(dT, Dk + dT, dT)
        T = np.linspace(0,Dk,Dk*Nt,endpoint=False)
        #T = np.linspace(dT,Dk,Dk*Nt,endpoint=True)

        Tmax = dT * np.floor(self.t_peak / dT)
        Emax = self.e_peak
        Emin = self.e_min
        if Tmax < Dk:
            LC1 = Emin / Nt + ((Emax - Emin) / Nt) * (T - dT) / (Tmax - dT)
            LC2 = Emin / Nt + ((Emax - Emin) / Nt) * (Dk - T) / (Dk - dT - Tmax)
            if Emax>Emin:
                LC = np.minimum(LC1,LC2)
            else:
                LC = np.maximum(LC1, LC2)
        else:
            LC = Emin / Nt + ((Emax - Emin) / Nt) * (T - dT) / (Tmax - dT)
        return LC