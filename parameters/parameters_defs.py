from common_GUI.tk_forms_assist import IntNode, FloatNode, StringNode, BoolNode
from multiprocessing import cpu_count
from .form_parts import LocaleSelection, ColormapSetting

PARAMETERS_DEFINITION = [
    ["MAIN_LATITUDE", FloatNode, 68.607279],
    ["MAIN_LONGITUDE", FloatNode, 31.803085],

    ["PIXEL_SIZE", FloatNode, 2.85],
    ["HALF_GAP_SIZE", FloatNode, 2.0],
    ["HALF_PIXELS", IntNode, 8],

    ["PLOT_COLORMAP", ColormapSetting, "viridis"],
    ["PLOT_BROKEN_COLOR", StringNode, "black"],
    ["PLOT_HIGHLIGHT_COLOR", StringNode, "red"],

    ["NPROC", IntNode, cpu_count()],

    ["LOCALE", LocaleSelection, "en"],

    ["SCALE_FLOATING_POINT_FORMAT", StringNode, "{:.2f}"],
    ["DATETIME_FORMAT", StringNode, "%Y-%m-%d %H:%M:%S"],

    ["USE_VIEWER", BoolNode, True],
    ["USE_CONVERTER", BoolNode, True],
    ["USE_FLATFIELDER", BoolNode, True],
    ["USE_STARCALIBRATOR", BoolNode, True],
    ["USE_BACKGROUND_EXTRACTOR", BoolNode, True],
    ["USE_DATASET_CREATOR", BoolNode, True],
    ["USE_TRAINER", BoolNode, True],
]

def get_defaults():
    return {item[0]: item[2] for item in PARAMETERS_DEFINITION}