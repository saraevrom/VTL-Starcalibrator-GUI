from settings_frame import SettingMenu, RangeDoubleValue, SliderRangeDoubleValue, RangeIntValue, CheckboxValue
from settings_frame import ComboboxValue
from localization import get_locale

def build_menu(menu: SettingMenu):
    menu.add_separator(get_locale("datasetgen.form.data_augmentagion"))