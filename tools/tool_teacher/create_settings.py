from common_GUI import SettingMenu
from common_GUI.settings_frame import IntValue, CheckboxValue, ComboboxValue, RangeDoubleValue
from localization import get_locale

def build_menu(menu: SettingMenu):
    menu.add_separator(get_locale("teacher.form.separator.dataset_parameters"))
    menu.add_separator(get_locale("teacher.form.separator.model_teaching"))
    menu.add_setting(IntValue, "epochs", get_locale("teacher.form.epochs"), 10)
    menu.add_setting(IntValue, "batch_size", get_locale("teacher.form.batch_size"), 10)

