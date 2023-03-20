from extension.optional_tensorflow import TENSORFLOW_INSTALLED
import vtl_common.parameters
print(dir(vtl_common.parameters))
from vtl_common.parameters import USE_VIEWER, USE_CONVERTER, USE_FLATFIELDER, USE_STARCALIBRATOR, USE_BACKGROUND_EXTRACTOR
from vtl_common.parameters import USE_DATASET_CREATOR, USE_TRAINER

def add_tools(adder):
        if USE_VIEWER:
                from .tool_mat_player import MatPlayer
                adder("app.menu.tools.mat_player", MatPlayer)
        if USE_CONVERTER:
                from tools.tool_mat_converter import MatConverter
                adder("app.menu.tools.mat_converter", MatConverter)
        if USE_FLATFIELDER:
                from .tool_flatfielder import FlatFielder
                adder("app.menu.tools.flatfielder", FlatFielder)
        if USE_STARCALIBRATOR:
                from .tool_starcalibrator import StarCalibrator
                adder("app.menu.tools.starcalibrator", StarCalibrator)
        if USE_BACKGROUND_EXTRACTOR:
                from .tool_track_markup import TrackMarkup
                adder("app.menu.tools.track_markup", TrackMarkup)
        if USE_DATASET_CREATOR:
                from .tool_dataset_generation import DatasetGenerator
                adder("app.menu.tools.dataset_generator", DatasetGenerator)
        if TENSORFLOW_INSTALLED and USE_TRAINER:
                from .tool_teacher import ToolTeacher
                adder("app.menu.tools.teacher", ToolTeacher)