from settings_frame import SettingMenu, RangeDoubleValue, SliderRangeDoubleValue, CheckboxValue
from math import pi


def build_menu(menu: SettingMenu):
    menu.add_separator("Выбор звёзд")
    menu.add_setting(RangeDoubleValue, "Mag_threshold", "Порог звёздной величины", 4, start=-1.44, end=6.0,
                     step=1e-2, fmt="%.2f")
    menu.add_separator("Параметры ориентации")
    menu.add_setting(RangeDoubleValue, "dec0", "Склонение прибора, рад", 0, start=-pi/2, end=pi/2, step=1e-3, fmt="%.6f")
    menu.add_setting(RangeDoubleValue, "ra0", "П. в. прибора (при ERA=0), рад", 0, start=0, end=2*pi,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "psi", "Собственный поворот прибора, рад", 0, start=-pi, end=pi,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "f", "Фокусное расстояние, мм", 150, start=145, end=165,
                     step=1e-2, fmt="%.2f")
    menu.add_separator("Параметры оптимизатора (амлитуды изменения)")
    menu.add_setting(RangeDoubleValue, "d_dec0", "Склонение прибора, рад", 1e-2, start=0, end=1, step=1e-3, fmt="%.6f")
    menu.add_setting(RangeDoubleValue, "d_ra0", "П. в. прибора (при ERA=0), рад", 1e-2, start=0, end=1,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "d_psi", "Собственный поворот прибора, рад", 1e-2, start=0, end=1,
                     step=1e-3, fmt="%.3f")
    menu.add_setting(RangeDoubleValue, "d_f", "Фокусное расстояние, мм", 1, start=0, end=10,
                     step=1.0, fmt="%.2f")
    menu.add_setting(CheckboxValue, "optimizer_run", "Запустить оптимизатор", False)
    menu.add_separator("Выбор времени")
    menu.add_setting(SliderRangeDoubleValue, "t1", "Точка 1", 0, start=0, end=100)
    menu.add_setting(SliderRangeDoubleValue, "t2", "Точка 2", 100, start=0, end=100)
    menu.add_separator("Параметры отображения")
    menu.add_setting(RangeDoubleValue, "threshold", "Порог", 10, start=0, end=1000,
                     step=1.0, fmt="%.2f")
    menu.add_setting(RangeDoubleValue, "filter", "Окно фильтра", 60, start=0, end=1200,
                     step=1.0, fmt="%.2f")
    menu.add_setting(CheckboxValue, "global_filter", "Глобальный фильтр", False)