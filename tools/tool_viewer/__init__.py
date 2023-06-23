import tkinter as tk
from vtl_common.localized_GUI.plotter import GridPlotter
from .player_controls import PlayerControls
import numpy as np
from datetime import datetime
from ..tool_base import ToolBase
from vtl_common.localization import get_locale
from vtl_common.common_GUI import TkDictForm
from vtl_common.parameters import DATETIME_FORMAT, HALF_PIXELS
import matplotlib.pyplot as plt
from .form import ViewerForm
from vtl_common.workspace_manager import Workspace
import tqdm
import io
import imageio as iio
import matplotlib.dates as md
from datetime import datetime
import json
from vtl_common.localized_GUI.signal_plotter import PopupPlotable
from friendliness import check_mat
from compatibility.h5py_aliased_fields import SafeMatHDF5
from preprocessing.denoising import slice_for_preprocess
from inner_communication import register_action


WORKSPACE_ANIMATIONS = Workspace("animations")
WORKSPACE_EXPORT = Workspace("export")
WORKSPACE_FRAMES = Workspace("frames")

class MatPlayer(ToolBase, PopupPlotable):
    def __init__(self, master):
        ToolBase.__init__(self,master)
        self.title(get_locale("matplayer.title"))
        self.file = None
        self.form_parser = ViewerForm()
        rframe = tk.Frame(self)

        self.form = TkDictForm(rframe, self.form_parser.get_configuration_root())
        self.form.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.form.on_commit = self.poke

        gif_btn = tk.Button(rframe, text=get_locale("matplayer.button.render_gif"), command=self.on_render_gif)
        gif_btn.pack(side=tk.TOP, fill=tk.X)

        attach_btn = tk.Button(rframe, text=get_locale("matplayer.button.attach_ff"), command=self.on_attach_ff)
        attach_btn.pack(side=tk.TOP, fill=tk.X)

        export_btn = tk.Button(rframe, text=get_locale("matplayer.button.export"), command=self.on_export)
        export_btn.pack(side=tk.TOP, fill=tk.X)

        rframe.pack(side=tk.RIGHT, fill=tk.Y)
        self.plotter = GridPlotter(self)
        self.plotter.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.player_controls = PlayerControls(self, self.on_frame_draw, self.click_callback)
        self.player_controls.pack(side=tk.BOTTOM, fill=tk.X)
        self.get_mat_file()
        self.form_data = None
        self.fig, self.ax = None, None
        PopupPlotable.__init__(self, self.plotter)
        register_action("view_frame", self.action_set_frame)
        register_action("view_save", self.action_save_frame)
        self.click_callback()

    def on_export(self):
        filename = WORKSPACE_EXPORT.asksaveasfilename(title=get_locale("matplayer.dialog.gif_target"),
                                                          auto_formats=["h5"],
                                                          parent=self)
        if filename and self.file:
            self.click_callback()
            low, high = self.player_controls.get_selected_range()
            filter_obj = self.form_data["filter"]

            prepdata, cutter = filter_obj.prepare_array(self.file["data0"],low,high)
            # affect = filter_obj.get_affected_range()
            # a_low = low - affect
            # if a_low<0:
            #     a_low = 0
            # a_high = high+1+affect
            # if a_high>self.file["data0"].shape[0]:
            #     a_high = self.file["data0"].shape[0]

            ffmodel = self.get_ff_model()

            #data = self.file["data0"][a_low:a_high]
            ut0 = self.file["UT0"][low:high]

            if (ffmodel is not None) and self.form_data["use_flatfielding"]:
                prepdata = ffmodel.apply(prepdata)

            if filter_obj.is_working():
                prepdata = filter_obj.preprocess_whole(prepdata, self.plotter.get_broken())

            data = prepdata[cutter]

            assert ut0.shape[0] == data.shape[0]

            with SafeMatHDF5(filename, "w") as fp:
                fp.create_dataset("data0", data=data)
                fp.create_dataset("UT0", data=ut0)

    def on_attach_ff(self):
        if self.file:
            ffmodel = self.get_ff_model()
            if ffmodel:
                jsd = ffmodel.dump()

                remembered_filename = self.get_loaded_filepath()
                self.close_mat_file()
                if check_mat(remembered_filename):
                    with SafeMatHDF5(remembered_filename, "a") as rw_file:
                        rw_file.attrs["ffmodel"] = json.dumps(jsd)

                self.reload_mat_file(remembered_filename, silent=True)

    def on_render_gif(self):
        if not self.file:
            return
        filename = WORKSPACE_ANIMATIONS.asksaveasfilename(title=get_locale("matplayer.dialog.gif_target"),
                                              auto_formats=["gif mp4"],
                                              parent=self)
        if filename:
            renderer = self.form_data["gif_renderer"]
            if renderer["frame_skip"] < 1:
                renderer["frame_skip"] = 1
            self.click_callback()
            low, high = self.player_controls.get_selected_range()
            print("GIF RENDER")
            print("-" * 20)
            print(f"FROM {low} to {high}")
            print("-" * 20)
            print(renderer)
            print("-" * 20)
            if filename.endswith(".gif"):
                writer = iio.get_writer(filename, duration=1000/renderer["fps"])
            else:
                writer = iio.get_writer(filename, fps=renderer["fps"])
            for i in tqdm.tqdm(range(low, high+1, renderer["frame_skip"])):
                self.on_frame_draw(i)
                buf = io.BytesIO()
                self.plotter.figure.savefig(buf, format="png")
                buf.seek(0)
                frame = iio.v3.imread(buf)
                writer.append_data(frame)
            writer.close()


    def on_frame_draw(self, frame_num):
        if self.file:
            #frame_start = time.time()
            #print("Frame START")
            frame = self.file["data0"][frame_num]
            #frame = self.file["data0"][frame_num]
            ut0 = self.ut0_s[frame_num]
            #ut0 = self.file["UT0"][frame_num]
            # print("UT0:", ut0)
            time_str = datetime.utcfromtimestamp(ut0).strftime(DATETIME_FORMAT)
            ffmodel = self.get_ff_model()
            filter_obj = self.form_data["filter"]
            if filter_obj.is_working():
                if self.form_data["use_flatfielding"]:
                    frame = filter_obj.preprocess_single(ffmodel, self.file["data0"], frame_num,
                                                         self.plotter.get_broken())
                else:
                    frame = filter_obj.preprocess_single(None, self.file["data0"], frame_num,
                                                         self.plotter.get_broken())
                # window = self.form_data["filter_window"]
                # #print("PING!", window)
                # slide_bg = np.median(self.file["data0"][frame_num:frame_num+window],axis=0)
                # if (ffmodel is not None) and self.form_data["use_flatfielding"]:
                #     frame = ffmodel.apply(self.file["data0"][frame_num]) - ffmodel.apply(slide_bg)
                # else:
                #     frame = self.file["data0"][frame_num] - slide_bg

            elif (ffmodel is not None) and self.form_data["use_flatfielding"]:
                frame = ffmodel.apply(frame)
            self.plotter.buffer_matrix = frame
            self.plotter.update_matrix_plot(True)
            self.plotter.axes.set_title(time_str)
            #print("Frame calculated:", time.time()-frame_start)
            self.plotter.draw()
            #self.plotter.figure.canvas.draw()
            #print("Frame END:", time.time()-frame_start)

    def click_callback(self):
         data_raw = self.form.get_values()
         self.form_parser.parse_formdata(data_raw)
         self.form_data = self.form_parser.get_data()

    def on_loaded_file_success(self):
        #self.frames = np.array(self.file["data0"])
        #self.ut0_s = np.array(self.file["UT0"])
        self.ut0_s = self.file["UT0"]
        print("VIEWER: times loaded")
        self.player_controls.link_time(self.ut0_s)
        self.player_controls.set_limit(self.file["UT0"].shape[0] - 1)
        #self.plotter.draw()
        self.poke()

    def poke(self):
        print("POKED")
        self.player_controls.draw_frame()

    def on_ff_reload(self):
        ffmodel = self.get_ff_model()
        if ffmodel:
            self.plotter.set_broken(ffmodel.broken_query())
        else:
            self.plotter.alive_pixels_matrix = np.ones([2*HALF_PIXELS, 2*HALF_PIXELS]).astype(bool)
        self.plotter.draw()
        self.poke()


    def handle_mpl_close(self, mpl_event):
        if self.fig is None:
            return
        if mpl_event.canvas.figure == self.fig:
            print("Closed last figure. Figure resetting.")
            self.fig = None
            self.ax = None

    def __get_plot_x(self, start, end):
        if self.form_data["use_times"]:
            if self.form_data["use_gtu"]:
                return self.ut0_s[start: end+1]
            return list(map(datetime.utcfromtimestamp, self.ut0_s[start: end+1]))
        else:
            return np.arange(start, end+1)

    def get_plot_data(self):
        if self.file:
            start, end = self.player_controls.get_selected_range()
            xs = self.__get_plot_x(start, end)
            #assert (np.diff(xs)>0).all()
            #ys = self.file["data0"][start: end + 1]
            filter_obj = self.form_data["filter"]
            ys, ys_slice = filter_obj.prepare_array(self.file["data0"], start, end+1)
            if self.form_data["use_flatfielding"]:
                ffmodel = self.get_ff_model()
                if ffmodel:
                    ys = ffmodel.apply_nobreak(ys)
            if filter_obj.is_working():
                ys = filter_obj.preprocess_whole(ys, self.plotter.get_broken())

            ys = ys[ys_slice]
            print("Y shape", ys.shape)
            return xs, ys
        else:
            return None

    def action_set_frame(self,frame=None):
        if frame is not None:
            self.player_controls.playing_position.set_frame(frame)
        return self.player_controls.playing_position.get_frame()

    def action_save_frame(self, filename):
        self.plotter.figure.savefig(WORKSPACE_FRAMES.get_file(filename))