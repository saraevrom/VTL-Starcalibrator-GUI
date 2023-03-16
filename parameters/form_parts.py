from vtl_common.common_GUI.tk_forms_assist import StringNode, ComboNode
import matplotlib.pyplot as plt

def valid_cmap(x:str):
    if x[0].isupper():
        return False
    if x.startswith("_"):
        return False
    return True

class ColormapSetting(ComboNode):
    DEFAULT_VALUE = "viridis"
    SELECTION_READONLY = True
    VALUES = list(filter(valid_cmap, dir(plt.cm)))

    def get_data(self):
        dat = super().get_data()
        try:
            cm = getattr(plt.cm, dat)
            return cm
        except AttributeError:
            return plt.cm.viridis

class LocaleSelection(ComboNode):
    SELECTION_READONLY = True
    DEFAULT_VALUE = "en"
    VALUES = ["en", "ru"]
