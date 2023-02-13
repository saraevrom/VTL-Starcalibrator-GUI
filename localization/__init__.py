from parameters import LOCALE
import json
import os.path as ospath
import atexit
import inspect

MISSING_LOCALES = []

cwd = ospath.abspath(__file__)
locale_path = ospath.join(ospath.dirname(cwd), LOCALE+".json")
print("LOCALE:",locale_path)
with open(locale_path, "r") as fp:
    locale_dict = json.load(fp)

def format_locale(key,*args,**kwargs):
    if key in locale_dict.keys():
        return locale_dict[key].format(*args,**kwargs)
    else:
        if key not in MISSING_LOCALES:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            MISSING_LOCALES.append([key, calframe[1][3]])
        return key

def get_locale(key):
    if key in locale_dict.keys():
        return locale_dict[key]
    else:
        if key not in MISSING_LOCALES:
            curframe = inspect.currentframe()
            calframe = inspect.getouterframes(curframe, 2)
            MISSING_LOCALES.append([key, calframe[1][3]])
        return key


help_path = ospath.join(ospath.dirname(cwd), "help", LOCALE)


def get_help(key):
    with open(ospath.join(help_path, key), "r") as fp:
        return fp.read()


def report_missing_locales():
    if MISSING_LOCALES:
        print(f"Found missing locales for locale '{LOCALE}'")
        for item in MISSING_LOCALES:
            print("{} (caller {})".format(*item))


atexit.register(report_missing_locales)