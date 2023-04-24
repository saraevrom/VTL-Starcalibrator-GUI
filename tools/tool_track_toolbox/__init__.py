import tkinter as tk

import numpy as np

from ..tool_base import ToolBase
from vtl_common.localized_GUI.plotter import GridPlotter
from vtl_common.common_GUI.button_panel import ButtonPanel
from vtl_common.common_GUI.tk_forms import TkDictForm
from vtl_common.localization import get_locale
from vtl_common.localized_GUI.signal_plotter import PopupPlotable
from .form import ToolboxForm
from track_gen import generate_track
from track_gen.track_dynamics import Track

from vtl_common.parameters import PIXEL_SIZE, HALF_GAP_SIZE, HALF_PIXELS
from track_gen.pdm_params import pixel_size_a, pixel_size_b, side_a, side_b


GAP_SIZE = HALF_GAP_SIZE*2
PIXELS = HALF_PIXELS*2

GAP_OFFSET_X = GAP_SIZE * pixel_size_a/PIXEL_SIZE
GAP_OFFSET_Y = GAP_SIZE * pixel_size_b/PIXEL_SIZE


class TrackToolbox(ToolBase, PopupPlotable):
    def __init__(self, parent):
        ToolBase.__init__(self,parent)
        self.plotter = GridPlotter(self)
        PopupPlotable.__init__(self, self.plotter)
        self.plotter.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        right_panel = tk.Frame(self)
        right_panel.pack(side=tk.LEFT, fill=tk.Y)
        self.button_panel = ButtonPanel(right_panel)
        self.button_panel.add_button(get_locale("track_toolbox.btn.create_track"), self.on_create_track, row=0)

        self.button_panel.pack(side=tk.TOP, fill=tk.X)
        self.form_parser = ToolboxForm()
        self.form = TkDictForm(right_panel, self.form_parser.get_configuration_root())
        self.form.on_commit = self.sync_form
        self.form.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self._formdata = None
        self._track = None
        self.sync_form()

    def sync_form(self):
        formdata = self.form.get_values()
        self.form_parser.parse_formdata(formdata)
        self._formdata = self.form_parser.get_data()

    def on_create_track(self):
        # FIELD__trajectory = TrajectoryField
        # FIELD__light_curve = LightCurveField
        # FIELD__psf = PSFField
        # FIELD__duration = create_value_field(IntNode, get_locale("track_toolbox.form.duration"), 128)
        # FIELD__subframes = create_value_field(IntNode, get_locale("track_toolbox.form.subframes"), 10)
        # FIELD__time_cap = TimeCapOption
        kwargs = {k:self._formdata[k] for k in "trajectory light_curve psf duration subframes time_cap".split(" ")}

        off_x = GAP_OFFSET_X + HALF_PIXELS*pixel_size_a
        off_y = GAP_OFFSET_Y + HALF_PIXELS*pixel_size_b

        bl_trajectory:Track = kwargs["trajectory"]
        br_trajectory = bl_trajectory.offset(-off_x,0)
        tl_trajectory:Track = bl_trajectory.offset(0, -off_y)
        tr_trajectory = bl_trajectory.offset(-off_x, -off_y)
        max_time_bound = max(
            bl_trajectory.get_time_bound(),
            br_trajectory.get_time_bound(),
            tl_trajectory.get_time_bound(),
            tr_trajectory.get_time_bound()
        )
        track_time = kwargs["time_cap"]
        if track_time is None:
            track_time = kwargs["duration"]
        track_time = min(track_time,max_time_bound)
        print("TRACK TIME", track_time)
        kwargs["light_curve"].set_time_bound(track_time)

        self._track = np.zeros((kwargs["duration"],PIXELS,PIXELS))

        #BOTTOM LEFT
        self._track[:, :8, :8], _ = generate_track(**kwargs)

        #BOTTOM RIGHT
        kwargs["trajectory"] = br_trajectory
        self._track[:, 8:, :8], _ = generate_track(**kwargs)

        #TOP LEFT
        kwargs["trajectory"] = tl_trajectory
        self._track[:, :8, 8:], _ = generate_track(**kwargs)

        # TOP RIGHT
        kwargs["trajectory"] = tr_trajectory
        self._track[:, 8:, 8:], _ = generate_track(**kwargs)

        plot_data = np.max(self._track, axis=0)
        self.plotter.buffer_matrix = plot_data
        self.plotter.update_matrix_plot(True)
        self.plotter.draw()

    def get_plot_data(self):
        if self._track is None:
            return None
        x_data = np.arange(self._track.shape[0])
        return x_data, self._track