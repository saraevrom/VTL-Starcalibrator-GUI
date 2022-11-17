from settings_frame import SettingMenu, RangeDoubleValue, SliderRangeDoubleValue, RangeIntValue, CheckboxValue
from math import pi

def build_settings(menu:SettingMenu):
    menu.add_separator("Выбор диапазона")
    menu.add_setting(RangeIntValue, "time_1", "Точка 1", 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "time_2", "Точка 2", 100, start=0, end=100)
    menu.add_separator("Данные")
    menu.add_setting(RangeIntValue, "samples_mean", "Усреднение", 60, start=0, end=1200)
    menu.add_separator("Алгоритм")
    menu.add_setting(CheckboxValue, "use_alt_algo", "Изотропный алгоритм.", False)