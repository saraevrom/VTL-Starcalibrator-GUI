from common_GUI.settings_frame import SettingMenu, DoubleValue, ComboboxValue, CheckboxValue
from localization import get_locale

def build_menu(menu: SettingMenu):
    menu.add_setting(ComboboxValue, "lightcurve", get_locale("app.popup_plot.lightcurve"),"Off",
                     options=["Off", "All", "Selected"], sensitive=True)
    menu.add_setting(CheckboxValue, "lightcurve_mean", get_locale("app.popup_plot.lightcurve_mean"), False, sensitive=True)
    menu.add_setting(CheckboxValue, "show_pixels", get_locale("app.popup_plot.show_pixels"), True, sensitive=True)

    menu.add_setting(DoubleValue, "threshold", get_locale("app.popup_plot.threshold"), 3.5)