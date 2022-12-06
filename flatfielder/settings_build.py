from settings_frame import SettingMenu, RangeIntValue, CheckboxValue, ComboboxValue
from math import pi

def build_settings(menu:SettingMenu):
    menu.add_separator("Выбор диапазона")
    menu.add_setting(RangeIntValue, "time_1", "Точка 1", 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "time_2", "Точка 2", 100, start=0, end=100)
    menu.add_separator("Данные")
    menu.add_setting(RangeIntValue, "samples_mean", "Усреднение", 60, start=0, end=1200)
    menu.add_separator("Алгоритм")
    menu.add_setting(ComboboxValue, "used_algo", "Алгоритм", "median_corr", options=[
        "median_corr",
        "isotropic_lsq_corr_parallel",
        "isotropic_lad_multidim",
        "isotropic_lad_multidim_no_bg"
    ])