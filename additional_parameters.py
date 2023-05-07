from vtl_common.common_GUI.tk_forms_assist import BoolNode

ADD_PARAMS = [
    ["USE_VIEWER", BoolNode, True],
    ["USE_CONVERTER", BoolNode, True],
    ["USE_FLATFIELDER", BoolNode, True],
    ["USE_STARCALIBRATOR", BoolNode, True],
    ["USE_BACKGROUND_EXTRACTOR", BoolNode, True],
    ["USE_DATASET_CREATOR", BoolNode, True],
    ["USE_TRAINER", BoolNode, True],
    ["USE_TRACK_TOOLBOX", BoolNode, True],
    ["ALLOW_MAT_MODIFICATION", BoolNode, False]
]