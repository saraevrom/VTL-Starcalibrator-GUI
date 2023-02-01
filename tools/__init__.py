
from tools.tool_mat_converter import MatConverter
from .tool_flatfielder import FlatFielder
from .tool_mat_player import MatPlayer
from .tool_track_markup import TrackMarkup
from .tool_starcalibrator import StarCalibrator
from .tool_dataset_generation import DatasetGenerator

from extension.optional_tensorflow import TENSORFLOW_INSTALLED

def add_tools(adder):
        adder("app.menu.tools.mat_player", MatPlayer)
        adder("app.menu.tools.mat_converter", MatConverter)
        adder("app.menu.tools.flatfielder", FlatFielder)
        adder("app.menu.tools.starcalibrator", StarCalibrator)
        adder("app.menu.tools.track_markup", TrackMarkup)
        adder("app.menu.tools.dataset_generator", DatasetGenerator)
        if TENSORFLOW_INSTALLED:
                from .tool_teacher import ToolTeacher
                adder("app.menu.tools.teacher", ToolTeacher)