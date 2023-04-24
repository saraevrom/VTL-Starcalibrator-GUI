import numpy as np
from vtl_common.localization import get_locale
from vtl_common.common_GUI.tk_forms_assist import FormNode, AlternatingNode, FloatNode, IntNode
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field
from .track_dynamics import LinearTrack
from .track_lightcurves import TriangularLightCurve
from .track_psf import GaussianPSF

class LinearTrajectoryField(FormNode):
    DISPLAY_NAME = get_locale("app.trackgen.trajectory.linear")
    FIELD__x0 = create_value_field(FloatNode,"x_0",0.0)
    FIELD__y0 = create_value_field(FloatNode,"y_0",0.0)
    FIELD__u0 = create_value_field(FloatNode,"u_0",0.1)
    FIELD__phi0 = create_value_field(FloatNode,"φ_0 [°]",0.0)
    FIELD__a = create_value_field(FloatNode,"a_0",0.0)

    def get_data(self):
        kwargs = super().get_data()
        kwargs["phi0"] = kwargs["phi0"]*np.pi/180
        return LinearTrack(**kwargs)

class TrajectoryField(AlternatingNode):
    DISPLAY_NAME = get_locale("app.trackgen.trajectory")
    SEL__linear = LinearTrajectoryField

class TriangularLightCurveField(FormNode):
    DISPLAY_NAME = get_locale("app.trackgen.light_curve.triangular")
    FIELD__t_peak = create_value_field(FloatNode,"t_peak",0.0)
    FIELD__e_peak = create_value_field(FloatNode,"e_peak",1.0)
    FIELD__e_min = create_value_field(FloatNode,"e_min", 0.25)

    def get_data(self):
        kwargs = super().get_data()
        return TriangularLightCurve(**kwargs)

class LightCurveField(AlternatingNode):
    DISPLAY_NAME = get_locale("app.trackgen.light_curve")
    SEL__triangular = TriangularLightCurveField

class GaussianPSFField(FormNode):
    DISPLAY_NAME = get_locale("app.trackgen.psf.gauss")
    FIELD__sigma_x = create_value_field(FloatNode, "sigma_x", 0.25)
    FIELD__sigma_y = create_value_field(FloatNode, "sigma_y", 0.25)

    def get_data(self):
        kwargs = super().get_data()
        return GaussianPSF(**kwargs)

class PSFField(AlternatingNode):
    DISPLAY_NAME = get_locale("app.trackgen.psf")
    SEL__gauss = GaussianPSFField