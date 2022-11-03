from settings_frame import SettingMenu, RangeDoubleValue, SliderRangeDoubleValue, RangeIntValue, CheckboxValue
from math import pi


def build_menu(menu: SettingMenu):
    menu.add_separator("Выбор звёзд")
    menu.add_setting(RangeDoubleValue, "Mag_threshold", "Порог звёздной величины", 4, start=-1.44, end=6.0,
                     step=1e-2, fmt="%.2f")
    menu.add_setting(RangeIntValue, "star_samples", "Количество точек на траектории.", 10, start=0, end=100)
    menu.add_separator("Параметры ориентации")
    menu.add_setting(RangeDoubleValue, "dec0", "Склонение прибора, °", 53.688444, start=-90, end=90, step=1e-3, fmt="%.6f")
    menu.add_setting(RangeDoubleValue, "ra0", "П. в. прибора (при ERA=0), °", 40.754414, start=0., end=360.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "psi", "Собственный поворот прибора, °", 0, start=180., end=180.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "f", "Фокусное расстояние, мм", 150, start=145., end=165.,
                     step=1e-2, fmt="%.2f")
    menu.add_separator("Параметры оптимизатора (амлитуды изменения)")
    menu.add_setting(RangeDoubleValue, "d_dec0", "Склонение прибора, °", 1., start=0., end=1., step=1e-3, fmt="%.6f")
    menu.add_setting(RangeDoubleValue, "d_ra0", "П. в. прибора (при ERA=0), °", 1., start=0., end=10.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "d_psi", "Собственный поворот прибора, °", 1., start=0., end=10.,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "d_f", "Фокусное расстояние, мм", 1., start=0., end=10.,
                     step=1.0, fmt="%.2f")
    menu.add_setting(CheckboxValue, "optimizer_run", "Запустить оптимизатор", False)
    menu.add_separator("Выбор времени")
    menu.add_setting(RangeIntValue, "time_1", "Точка 1", 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "time_2", "Точка 2", 100, start=0, end=100)
    menu.add_separator("Параметры отображения")
    menu.add_setting(RangeDoubleValue, "display_threshold", "Порог", 10, start=0, end=1000,
                     step=1.0, fmt="%.2f")
    menu.add_setting(RangeIntValue, "filter_window", "Окно фильтра", 60, start=0, end=1200)
    menu.add_setting(CheckboxValue, "global_filter", "Глобальный фильтр", False)