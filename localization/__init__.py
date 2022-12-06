from parameters import LOCALE
import json
import os.path as ospath

cwd = ospath.abspath(__file__)
locale_path = ospath.join(ospath.dirname(cwd), LOCALE+".json")
print("LOCALE:",locale_path)
with open(locale_path, "r") as fp:
    locale_dict = json.load(fp)

def format_locale(key,*args,**kwargs):
    if key in locale_dict.keys():
        return locale_dict[key].format(*args,**kwargs)
    else:
        return key

def get_locale(key):
    if key in locale_dict.keys():
        return locale_dict[key]
    else:
        return key