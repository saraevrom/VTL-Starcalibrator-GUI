import tkinter as tk
from localized_GUI.plotter import GridPlotter
from .player_controls import PlayerControls
import numpy as np
from datetime import datetime
from ..tool_base import ToolBase
from localization import get_locale
from common_GUI import TkDictForm
from parameters import DATETIME_FORMAT
from preprocessing.denoising import moving_average_subtract
import matplotlib.pyplot as plt
from .form import ViewerForm
from workspace_manager import Workspace
import tqdm
import io
import imageio as iio
import matplotlib.dates as md
from datetime import datetime
import json, h5py

from preprocessing.three_stage_preprocess import preprocess_single

WORKSPACE_ANIMATIONS = Workspace("animations")


class MatPlayer(ToolBase):
    def __init__(self, master):
        super(MatPlayer, self).__init__(master)
        self.title(get_locale("matplayer.title"))
        self.file = None
        self.form_parser = ViewerForm()
        rframe = tk.Frame(self)

        self.form = TkDictForm(rframe, self.form_parser.get_configuration_root())
        self.form.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        gif_btn = tk.Button(rframe, text=get_locale("matplayer.button.render_gif"), command=self.on_render_gif)
        gif_btn.pack(side=tk.TOP, fill=tk.X)

        attach_btn = tk.Button(rframe, text=get_locale("matplayer.button.attach_ff"), command=self.on_attach_ff)
        attach_btn.pack(side=tk.TOP, fill=tk.X)

        rframe.pack(side=tk.RIGHT, fill=tk.Y)
        self.plotter = GridPlotter(self)
        self.plotter.pack(side=tk.TOP, expand=True, fill=tk.BOTH)
        self.plotter.on_right_click_callback = self.on_pixel_rmb
        self.plotter.on_right_click_callback_outofbounds = self.on_common_rmb
        self.player_controls = PlayerControls(self, self.on_frame_draw, self.click_callback)
        self.player_controls.pack(side=tk.BOTTOM, fill=tk.X)
        self.get_mat_file()
        self.form_data = None
        self.fig, self.ax = None, None
        self.click_callback()



    def on_attach_ff(self):
        if self.file:
            ffmodel = self.get_ff_model()
            if ffmodel:
                jsd = ffmodel.dump()

                remembered_filename = self.get_loaded_filepath()
                self.close_mat_file()
                with h5py.File(remembered_filename, "a") as rw_file:
                    rw_file.attrs["ffmodel"] = json.dumps(jsd)

                self.reload_mat_file(remembered_filename, silent=True)

    def on_render_gif(self):
        if not self.file:
            return
        filename = WORKSPACE_ANIMATIONS.asksaveasfilename(title=get_locale("matplayer.dialog.gif_target"),
                                              filetypes=[(get_locale("app.filedialog_formats.gif"), "*.gif")],
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
            time_str = datetime.utcfromtimestamp(ut0).strftime(DATETIME_FORMAT)
            ffmodel = self.get_ff_model()
            filter_obj = self.form_data["filter"]
            if filter_obj.is_working():
                if self.form_data["use_flatfielding"]:
                    frame = preprocess_single(filter_obj, ffmodel, self.file["data0"], frame_num, self.plotter.get_broken())
                else:
                    frame = preprocess_single(filter_obj, None, self.file["data0"], frame_num,
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
            #print("Frame END:", time.time()-frame_start)

    def click_callback(self):
         data_raw = self.form.get_values()
         self.form_parser.parse_formdata(data_raw)
         self.form_data = self.form_parser.get_data()

    def on_loaded_file_success(self):
        #self.frames = np.array(self.file["data0"])
        self.ut0_s = np.array(self.file["UT0"])
        self.player_controls.link_time(self.ut0_s)
        self.player_controls.set_limit(len(self.file["UT0"]) - 1)
        #self.plotter.draw()
        self.poke()

    def poke(self):
        self.player_controls.draw_frame()

    def on_ff_reload(self):
        ffmodel = self.get_ff_model()
        self.plotter.set_broken(ffmodel.broken_query())
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
            return list(map(datetime.utcfromtimestamp, self.ut0_s[start: end+1]))
        else:
            return np.arange(start, end+1)

    def on_pixel_rmb(self, i, j):
        if self.file:
            self.click_callback()
            print("DRAW", i, j)
            start, end = self.player_controls.get_selected_range()
            print("FROM", start, "TO", end)
            xs = self.__get_plot_x(start,end)
            ys = self.file["data0"][start: end+1]
            if self.form_data["use_flatfielding"]:
                ffmodel = self.get_ff_model()
                if ffmodel:
                    ys = ffmodel.apply_nobreak(ys)
            filter_obj = self.form_data["filter"]
            if filter_obj.is_working():
                ys = filter_obj.preprocess(ys, self.plotter.get_broken())
            ys = ys[:, i, j]
            if self.fig is None:
                self.fig, self.ax = plt.subplots()
                self.fig.canvas.mpl_connect('close_event', self.handle_mpl_close)

            self.ax.plot(xs, ys, label=f"[{i+1},{j+1}]")
            self.ax.legend()
            self.fig.show()

    def on_common_rmb(self):
        if self.file:
            self.click_callback()
            print("DRAW ALL")
            start, end = self.player_controls.get_selected_range()
            xs = self.__get_plot_x(start,end)
            ys = self.file["data0"][start: end + 1]
            if self.form_data["use_flatfielding"]:
                ffmodel = self.get_ff_model()
                if ffmodel:
                    ys = ffmodel.apply_nobreak(ys)
            filter_obj = self.form_data["filter"]
            if filter_obj.is_working():
                ys = filter_obj.preprocess(ys, self.plotter.get_broken())
            fig, ax = plt.subplots()
            for i in range(16):
                for j in range(16):
                    ax.plot(xs, ys[:, i, j], label=f"[{i+1},{j+1}]")
            ax.legend()
            fig.show()
