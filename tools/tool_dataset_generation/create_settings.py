from common_GUI import SettingMenu
from common_GUI.settings_frame import RangeIntValue, CheckboxValue, ComboboxValue
from localization import get_locale

def build_menu(menu: SettingMenu):
    menu.add_separator(get_locale("datasetgen.form.separator.display"))
    menu.add_setting(RangeIntValue, "cutoff_start", get_locale("datasetgen.form.cutoff_start"), 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "cutoff_end", get_locale("datasetgen.form.cutoff_end"), 0, start=0, end=100)
    menu.add_setting(RangeIntValue, "filter_window", get_locale("datasetgen.form.filter_window"), 60, start=0, end=1000)
    # menu.add_separator(get_locale("datasetgen.form.separator.data_augmentagion"))
    # menu.add_setting(CheckboxValue, "use_transpose", get_locale("datasetgen.form.use_transpose"), True)
    # menu.add_setting(CheckboxValue, "use_reverse", get_locale("datasetgen.form.use_reverse"), True)