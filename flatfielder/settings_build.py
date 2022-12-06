from settings_frame import SettingMenu, RangeIntValue, CheckboxValue, ComboboxValue
from math import pi
from localization import format_locale, get_locale

def build_settings(menu:SettingMenu):
    menu.add_separator("Выбор диапазона")
    menu.add_setting(RangeIntValue, "time_1", get_locale("flatfielder.form.field.time_1"), 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "time_2", get_locale("flatfielder.form.field.time_2"), 100, start=0, end=100)
    menu.add_separator(get_locale("flatfielder.form.separator.data"))
    menu.add_setting(RangeIntValue, "samples_mean", get_locale("flatfielder.form.field.samples_mean"), 60, start=0, end=1200)
    menu.add_separator(get_locale("flatfielder.form.separator.algo"))
    menu.add_setting(ComboboxValue, "used_algo", get_locale("flatfielder.form.field.used_algo"), "median_corr", options=[
        "median_corr",
        "isotropic_lsq_corr_parallel",
        "isotropic_lad_multidim",
        "isotropic_lad_multidim_no_bg"
    ])