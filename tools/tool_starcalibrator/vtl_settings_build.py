from settings_frame import SettingMenu, RangeDoubleValue, SliderRangeDoubleValue, RangeIntValue, CheckboxValue
from settings_frame import ComboboxValue
from math import pi
from localization import get_locale

def build_menu(menu: SettingMenu):
    menu.add_separator(get_locale("app.settings.separator.stars_selection"))
    menu.add_setting(RangeDoubleValue, "Mag_threshold", get_locale("app.settings.field.Mag_threshold"), 4, start=-1.44, end=6.0,
                     step=1e-2, fmt="%.2f")
    menu.add_setting(RangeIntValue, "star_samples", get_locale("app.settings.field.star_samples"), 10, start=0, end=100)
    menu.add_separator(get_locale("app.settings.separator.orientation_parameters"))
    menu.add_setting(RangeDoubleValue, "dec0", get_locale("app.settings.field.dec0"), 53.688444, start=-90, end=90, step=1e-3, fmt="%.6f")
    menu.add_setting(RangeDoubleValue, "ra0", get_locale("app.settings.field.ra0"), 40.754414, start=0., end=360.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "psi", get_locale("app.settings.field.psi"), 0, start=-180., end=180.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "f", get_locale("app.settings.field.f"), 150, start=145., end=165.,
                     step=1e-2, fmt="%.2f")
    menu.add_separator(get_locale("app.settings.separator.amplitude_parameters"))

    menu.add_setting(RangeDoubleValue, "d_dec0", get_locale("app.settings.field.dec0"), 1., start=0., end=1., step=1e-3, fmt="%.6f")
    menu.add_setting(RangeDoubleValue, "d_ra0", get_locale("app.settings.field.ra0"), 1., start=0., end=10.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "d_psi", get_locale("app.settings.field.psi"), 1., start=0., end=10.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "d_f", get_locale("app.settings.field.f"), 1., start=0., end=10.,
                     step=1.0, fmt="%.2f")
    menu.add_separator(get_locale("app.settings.separator.optimizer_parameters"))
    menu.add_setting(CheckboxValue, "optimizer_descent", get_locale("app.settings.field.optimizer_descent"), False)
    menu.add_setting(ComboboxValue, "optimizer_descent_mode", get_locale("optimizer_descent_mode"), "nelder-mead", options=[
        "nelder-mead",
        "powell"
    ])
    menu.add_setting(CheckboxValue, "optimizer_run", get_locale("app.settings.field.optimizer_run"), False)
    menu.add_setting(RangeIntValue, "optimizer_steps", get_locale("app.settings.field.optimizer_steps"), 0, start=0, end=100)
    menu.add_setting(CheckboxValue, "optimizer_use_min", get_locale("app.settings.field.optimizer_use_min"), False)
    menu.add_separator(get_locale("app.settings.separator.time_select"))
    menu.add_setting(RangeIntValue, "time_1", get_locale("app.settings.field.time_1"), 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "time_2", get_locale("app.settings.field.time_2"), 100, start=0, end=100)
    menu.add_separator(get_locale("app.settings.separator.display_parameters"))
    menu.add_setting(CheckboxValue, "display_use_filter", get_locale("app.settings.field.display_use_filter"), True)
    menu.add_setting(CheckboxValue, "display_use_max", get_locale("app.settings.field.display_use_max"), False)
    menu.add_setting(CheckboxValue, "global_filter", get_locale("app.settings.field.global_filter"), False)
    menu.add_setting(CheckboxValue, "flatfielding", get_locale("app.settings.field.flatfielding"), False)

    menu.add_setting(RangeDoubleValue, "display_threshold", get_locale("app.settings.field.display_threshold"), 10, start=0, end=1000,
                     step=1.0, fmt="%.2f")
    menu.add_setting(RangeIntValue, "filter_window", get_locale("app.settings.field.filter_window"), 60, start=0, end=1200)

