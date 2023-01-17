from common_GUI.settings_frame import SettingMenu, RangeIntValue, CheckboxValue, ComboboxValue
from localization import get_locale
from .flat_fielding_methods import ALGO_MAP

def build_settings(menu:SettingMenu):

    menu.add_separator(get_locale("flatfielder.form.separator.data"))
    menu.add_setting(RangeIntValue, "samples_mean", get_locale("flatfielder.form.field.samples_mean"), 60, start=0, end=1200)

    menu.add_separator(get_locale("flatfielder.form.separator.rangeselect"))
    menu.add_setting(RangeIntValue, "time_1", get_locale("flatfielder.form.field.time_1"), 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "time_2", get_locale("flatfielder.form.field.time_2"), 100, start=0, end=100)


    menu.add_separator(get_locale("flatfielder.form.separator.algo"))
    menu.add_setting(ComboboxValue, "used_algo", get_locale("flatfielder.form.field.used_algo"), "median_corr",
        options=list(ALGO_MAP.keys())
    )
    menu.add_separator(get_locale("flatfielder.form.separator.display"))
    menu.add_setting(CheckboxValue, "use_model", get_locale("flatfielder.form.field.use_model"), True)