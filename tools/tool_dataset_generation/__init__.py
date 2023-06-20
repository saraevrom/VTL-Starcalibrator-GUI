from ..tool_base import ToolBase
from .bg_picking_editor import BgPickingEditor
from .create_settings import build_menu
import gc
import numpy as np
import numba as nb
from vtl_common.common_GUI import SettingMenu
from vtl_common.localized_GUI import GridPlotter
from vtl_common.localization import get_locale, format_locale
import json
import tkinter.messagebox as messagebox
import h5py
from .hdf5_utils import overwrite_with_numpy
from datetime import datetime
from vtl_common.parameters import DATETIME_FORMAT
from vtl_common.workspace_manager import Workspace
import tkinter as tk
from friendliness import check_mat
from tools.tool_markup.storage import IntervalStorage

MARKUP_WORKSPACE = Workspace("marked_up_tracks")

@nb.njit()
def putmask_max(arr1,arr2):
    dst = np.zeros(arr1.shape)
    for i in range(arr1.shape[0]):
        for j in range(arr1.shape[1]):
            if arr1[i,j] > arr2[i,j]:
                dst[i,j] = arr1[i,j]
            else:
                dst[i, j] = arr2[i, j]
    return dst


@nb.njit()
def decimate_max(src,window):
    length = src.shape[0]//window
    dst = np.zeros((length,src.shape[1],src.shape[2]))
    for i in range(length):
        i_start = i*window
        i_end = i_start+window
        dst[i] = src[i_start]
        for j in range(i_start+1,i_end):
            dst[i] = putmask_max(dst[i], src[j])
    return dst


class DatasetGenerator(ToolBase):
    def __init__(self, master):
        super().__init__(master)

        left_panel = tk.Frame(self)

        left_panel.pack(side="left", fill="both", expand=True)

        self.plotter = GridPlotter(left_panel)
        self.plotter.pack(side="top", fill="both", expand=True)

        interval_editor_panel = tk.Frame(left_panel)
        interval_editor_panel.pack(side="bottom", fill="x")
        interval_editor_panel.rowconfigure(0,weight=1)
        interval_editor_panel.columnconfigure(0, weight=1)
        interval_editor_panel.columnconfigure(1, weight=1)
        interval_editor_panel.columnconfigure(2, weight=1)

        self.interval_editor = BgPickingEditor(interval_editor_panel)
        self.interval_editor.grid(row=0, column=0, columnspan=3, sticky="nsew")
        self.interval_editor.on_frame_lmb_event = self.draw_frame
        button_cutleft = tk.Button(interval_editor_panel, text=get_locale("datasetgen.button.cut_left"),
                                   command=self.on_cut_left)
        button_cutleft.grid(row=1, column=0, sticky="nsew")
        button_view_reset = tk.Button(interval_editor_panel, text=get_locale("datasetgen.button.view_reset"),
                                      command=self.on_view_reset)
        button_view_reset.grid(row=1, column=1, sticky="nsew")
        button_cutright = tk.Button(interval_editor_panel, text=get_locale("datasetgen.button.cut_right"),
                                   command=self.on_cut_right)
        button_cutright.grid(row=1, column=2, sticky="nsew")

        right_panel = tk.Frame(self)
        right_panel.pack(side="right", fill="y")

        self.settings_menu = SettingMenu(right_panel, autocommit=True)
        self.settings_menu.pack(fill="both", expand=True)
        build_menu(self.settings_menu)
        self.cutoff_1_setting = self.settings_menu.lookup_setting("cutoff_start")
        self.cutoff_2_setting = self.settings_menu.lookup_setting("cutoff_end")
        self.settings_dict = dict()
        self.settings_menu.commit_action = self.on_settings_commit
        self.settings_menu.add_tracer("filter_window", self.on_ma_filter_change)
        self.settings_menu.add_tracer("interval_weight", self.on_weight_edit)

        delete_button = tk.Button(right_panel, text=get_locale("datasetgen.button.delete"), command=self.on_delete)
        clear_button = tk.Button(right_panel, text=get_locale("datasetgen.button.clear"), command=self.on_clear)
        load_button = tk.Button(right_panel, text=get_locale("datasetgen.button.load"), command=self.on_load)
        save_button = tk.Button(right_panel, text=get_locale("datasetgen.button.save"), command=self.on_save)
        reload_button = tk.Button(right_panel, text=get_locale("datasetgen.button.reload"),
                                command=self.on_intervals_reload)

        save_button.pack(side="bottom", fill="x")
        reload_button.pack(side="bottom", fill="x")
        clear_button.pack(side="bottom", fill="x")
        delete_button.pack(side="bottom", fill="x")
        load_button.pack(side="bottom", fill="x")
        self.settings_menu.push_settings_dict(self.settings_dict)

        #self.plotter.grid(row=0, column=0, sticky="nsew", rowspan=2)


    def on_cut_left(self):
        ptr = self.interval_editor.frame_pointer_location
        self.set_view(left_override=ptr)

    def on_cut_right(self):
        if self.file:
            ptr = self.interval_editor.frame_pointer_location
            self.set_view(right_override=self.file["data0"].shape[0]-ptr)

    def on_view_reset(self):
        self.set_view(0, 0)

    def set_view(self, left_override=None, right_override=None):
        if left_override is not None:
            self.settings_dict["cutoff_start"] = left_override
        if right_override is not None:
            self.settings_dict["cutoff_end"] = right_override
        self.settings_menu.pull_settings_dict(self.settings_dict, ["cutoff_start", "cutoff_end"])
        self.on_settings_commit()

    def on_weight_edit(self):
        selected_weight = self.settings_dict["interval_weight"]
        self.interval_editor.set_interval_weight_on_frame_pointer(selected_weight)

    def on_clear(self):
        if self.file:
            if messagebox.askyesno(title=get_locale("datasetgen.messagebox.reset.title"),
                                   message=get_locale("datasetgen.messagebox.reset.content")):
                self.interval_editor.clear_intervals()
                self.interval_editor.redraw(self.settings_dict)

    def on_delete(self):
        if self.file:
            self.interval_editor.delete_interval_on_frame_pointer()
            self.interval_editor.redraw(self.settings_dict)

    def on_intervals_reload(self):
        if self.file:
            self.reload_stored_marked_intervals()
            self.interval_editor.redraw(self.settings_dict)

    def on_load(self):
        if self.file:
            load_path = MARKUP_WORKSPACE.askopenfilename(initialdir=".", filetypes=(("JSON", "*.json"),),
                                                             initialfile="progress.json", parent=self)
            if load_path:
                with open(load_path,"r") as fp:
                    jsd = json.load(fp)
                    if "found_event" in jsd.keys():
                        self.interval_editor.populate_intervals(jsd["found_event"])
                    else:
                        tracks = jsd["tracks"]
                        storage = IntervalStorage.deserialize(tracks)
                        events = [item.serialize for item in storage.get_available()]
                        self.interval_editor.populate_intervals(events)
                    self.interval_editor.redraw(self.settings_dict)

    def on_save(self):
        if messagebox.askokcancel(title=get_locale("datasetgen.messagebox.save.title"),
                                   message=get_locale("datasetgen.messagebox.save.content")):
            print("FILE SAVE PRESSED!!!")
            remembered_filename = self.get_loaded_filepath()
            self.close_mat_file()
            if check_mat(remembered_filename):
                with h5py.File(remembered_filename, "a") as rw_file:
                    overwrite_with_numpy(rw_file, "marked_intervals", self.interval_editor.marked_intervals)
                    overwrite_with_numpy(rw_file, "broken", np.logical_not(self.plotter.alive_pixels_matrix))

            self.reload_mat_file(remembered_filename, silent=True)
            messagebox.showinfo(title=get_locale("datasetgen.messagebox.save_success.title"),
                                   message=get_locale("datasetgen.messagebox.save_success.content"))

    def reload_stored_marked_intervals(self):
        if "marked_intervals" in self.file:
            loaded_intervals = np.array(self.file["marked_intervals"]).tolist()
            if loaded_intervals:
                if len(loaded_intervals[0])<3:
                    print("Weights are missing. They will be added.")
                    loaded_intervals = [[start, end, 1.0] for (start, end) in loaded_intervals]
            self.interval_editor.marked_intervals = loaded_intervals

    def on_loaded_file_success(self):
        gc.collect()
        self.reload_data()
        self.interval_editor.clear_intervals()
        self.reload_stored_marked_intervals()
        self.on_settings_commit()
        gc.collect()

    def reload_data(self):
        model = self.get_ff_model()
        self.interval_editor.reload_data(self.file, self.settings_dict, model)
        self.propagate_limits(self.file["data0"].shape[0])

    def on_ma_filter_change(self):
        print("MA filter changed")
        self.reload_data()

    def on_settings_commit(self):
        if self.file:
            self.settings_menu.push_settings_dict(self.settings_dict)

            print("Commit REDRAW")
            self.interval_editor.redraw(self.settings_dict)

    def propagate_limits(self, maxlen):
        self.cutoff_1_setting.set_limits(0, maxlen)
        self.cutoff_2_setting.set_limits(0, maxlen)

    def on_ff_reload(self):
        self.plotter.set_broken(self.get_ff_model().broken_query())
        if self.file:
            self.on_loaded_file_success()
        else:
            self.plotter.draw()


    def draw_frame(self,frame):
        if self.file:
            model = self.get_ff_model()
            draw_frame = self.file["data0"][frame]
            if model:
                draw_frame = model.apply(draw_frame)
            win = self.settings_dict["filter_window"]
            start = frame-win//2
            end = start + win
            if start < 0:
                start = 0
            if end > self.file["data0"].shape[0]:
                end = self.file["data0"].shape[0]
            meaning_interval = self.file["data0"][start:end]
            if model:
                meaning_interval = model.apply(meaning_interval)
            draw_frame = draw_frame - np.mean(meaning_interval, axis=0)
            self.plotter.buffer_matrix = draw_frame
            tim = datetime.utcfromtimestamp(self.file["UT0"][frame]).strftime(DATETIME_FORMAT)
            self.plotter.axes.set_title(format_locale("datasetgen.plot.title",frame=frame,time=tim))
            self.plotter.update_matrix_plot(True)
            self.plotter.draw()

            selected_weight = self.interval_editor.get_interval_weight_on_frame_pointer()
            self.settings_dict["interval_weight"] = selected_weight
            self.settings_menu.pull_settings_dict(self.settings_dict, "interval_weight")