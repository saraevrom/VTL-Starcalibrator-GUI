from common_GUI.settings_frame import SettingMenu
from localization import get_locale

def build_menu(menu: SettingMenu):
    menu.add_separator(get_locale("datasetgen.form.data_augmentagion"))