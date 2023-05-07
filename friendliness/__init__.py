
from vtl_common.localization import get_locale
import tkinter.messagebox as msg
import os.path as ospath

'''
Makes program more polite and forgiving
'''
from vtl_common import localization
from vtl_common.parameters import ALLOW_MAT_MODIFICATION

if not ALLOW_MAT_MODIFICATION:
    print("MODIFYING MAT IS DISALLOWED")

localization.SEARCH_DIRS.append(ospath.join(ospath.dirname(ospath.abspath(__file__)),"localization"))

def show_attention(topic, error_level=1):
    if error_level==2:
        msg.showerror(title=get_locale("attention"),message=get_locale("attention."+topic))
    elif error_level==1:
        msg.showwarning(title=get_locale("attention"),message=get_locale("attention."+topic))
    elif error_level==0:
        msg.showinfo(title=get_locale("attention"),message=get_locale("attention."+topic))

def check_data_file(file_obj):
    passed = True
    for required_field in ["data0", "UT0"]:
        if required_field not in file_obj.keys():
            passed = False

    if not passed:
        show_attention("convert_data",1)
    # return passed
    return True # EXPERIMENTAL

def check_mat(filename, verbose=True):
    if filename.endswith(".mat") and not ALLOW_MAT_MODIFICATION:
        if verbose:
            show_attention("mat_modification", 2)
        return False
    return True