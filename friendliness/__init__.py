
from vtl_common.localization import get_locale
import tkinter.messagebox as msg
import os.path as ospath

'''
Makes program more polite and forgiving
'''
from vtl_common import localization


localization.SEARCH_DIRS.append(ospath.join(ospath.dirname(ospath.abspath(__file__)),"localization"))

def show_attention(topic, error=False):
    if error:
        msg.showerror(title=get_locale("attention"),message=get_locale("attention."+topic))
    else:
        msg.showwarning(title=get_locale("attention"),message=get_locale("attention."+topic))


def check_data_file(file_obj):
    passed = True
    for required_field in ["data0", "UT0"]:
        if required_field not in file_obj.keys():
            passed = False

    if not passed:
        show_attention("convert_data")
    # return passed
    return True # EXPERIMENTAL