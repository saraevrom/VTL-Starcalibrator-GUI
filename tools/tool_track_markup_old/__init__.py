import gc
import tkinter as tk

from vtl_common.common_GUI import TkDictForm
from vtl_common.localized_GUI import GridPlotter
from ..tool_base import ToolBase
from .sorted_queue import SortedQueue
import numpy as np
import tkinter.messagebox
#import tkinter.filedialog
from vtl_common.workspace_manager import Workspace
import json
from vtl_common.localization import get_locale
import matplotlib.pyplot as plt
from .reset import ResetAsker
from .form import TrackMarkupForm
from extension.optional_tensorflow import TENSORFLOW_INSTALLED
import zipfile, h5py, io
import os.path as ospath
from .edges import EdgeProcessor
from preprocessing.three_stage_preprocess import DataThreeStagePreProcessor
from vtl_common.common_GUI.button_panel import ButtonPanel

if TENSORFLOW_INSTALLED:
    from tensorflow import keras
    from trigger_ai.models.model_wrapper import ModelWrapper
else:
    keras = None
    ModelWrapper = None

from .edges import edged_intervals, split_intervals
from vtl_common.localized_GUI.signal_plotter import PopupPlotable


OFF = get_locale("app.state_off")
ON = get_locale("app.state_on")

MARKUP_WORKSPACE = Workspace("marked_up_tracks")
TENSORFLOW_MODELS_WORKSPACE = Workspace("ann_models")
TRACKS_WORKSPACE = Workspace("tracks")

def try_append_event(target_list,start,end):
    ok = True
    for e_start,e_end in target_list:
        if start>=e_start and end<=e_end:
            ok = False
            break
    if ok:
        target_list.append([start,end])
    return ok


def stitch_events(events):
    sorted_events = list(sorted(events, key=lambda x: x[0]))
    deflation_i = 0
    while deflation_i < len(sorted_events) - 1:
        if sorted_events[deflation_i][1] == sorted_events[deflation_i + 1][0]:
            sorted_events[deflation_i][1] = sorted_events[deflation_i + 1][1]
            sorted_events.pop(deflation_i + 1)
        else:
            deflation_i += 1
    return sorted_events


def track_sym(a):
    if a:
        return "#"
    else:
        return "."

def print_track(bl,br,tl,tr):
    r = ""
    r += track_sym(tl)
    r += track_sym(tr)
    r += "\n"
    r += track_sym(bl)
    r += track_sym(br)
    print(r)

class TrackMarkup(ToolBase, PopupPlotable):
    def __init__(self, master):
        ToolBase.__init__(self,master)
        self.form_data = None
        self.title(get_locale("track_markup.title"))
        self.plotter = GridPlotter(self)
        self.get_mat_file()
        left_panel = tk.Frame(self)
        left_panel.pack(side="left", fill="y")
        self.queue = []
        self.trackless_events = []
        self.tracked_events = []
        self.last_single_plot_data = None
        self.tf_model = None
        self.tf_filter = None

        self.current_event = None
        self.event_set = False

        self.selected_data = tk.Listbox(left_panel, selectmode="single")
        self.selected_data.pack(side="bottom", fill="both", expand=True)
        tk.Label(left_panel,text=get_locale("track_markup.label.accepted")).pack(side="bottom", fill="x", expand=False)
        self.rejected_data = tk.Listbox(left_panel, selectmode="single")
        self.rejected_data.pack(side="bottom", fill="both", expand=True)
        tk.Label(left_panel,text=get_locale("track_markup.label.rejected")).pack(side="bottom", fill="x", expand=False)
        right_panel = tk.Frame(self)
        right_panel.pack(side="right", fill="y")
        self.button_panel = ButtonPanel(right_panel)
        self.button_panel.grid(row=0, column=0, sticky="ew")
        #right_panel.rowconfigure(0, weight=1)

        self.button_panel.add_button(text=get_locale("track_markup.btn.reset"),
             command=self.on_reset, row=0)
        self.button_panel.add_button(text=get_locale("track_markup.btn.recheck_tracks"),
                                     command=self.on_recheck_tracks, row=0)
        self.button_panel.add_button(text=get_locale("track_markup.btn.save"),
             command=self.on_save_data, row=1)
        self.button_panel.add_button(text=get_locale("track_markup.btn.export"),
             command=self.on_export_data, row=2)
        self.button_panel.add_button(text=get_locale("track_markup.btn.export_bg"),
             command=self.on_export_bg, row=3)
        self.button_panel.add_button(text=get_locale("track_markup.btn.load"),
             command=self.on_load_data, row=4)


        if TENSORFLOW_INSTALLED:
            self.button_panel.add_button(text=get_locale("track_markup.btn.load_tf"),
                      command=self.on_load_tf, row=5)
            # tk.Button(right_panel, text=get_locale("track_markup.btn.load_tf"),
            #           command=self.on_load_tf).grid(row=5, column=0, sticky="ew")

        self.tf_filter_info = tk.StringVar()
        tk.Label(right_panel, textvariable=self.tf_filter_info, justify=tk.LEFT) \
            .grid(row=1, column=0, sticky="nw")

        self.params_form_parser = TrackMarkupForm()

        self.params_form = TkDictForm(right_panel, self.params_form_parser.get_configuration_root())
        self.params_form.grid(row=2, column=0, sticky="nsew")
        right_panel.rowconfigure(2, weight=1)


        self.plotter.pack(side="top", expand=True, fill="both")
        bottom_panel = tk.Frame(self)
        bottom_panel.pack(side="bottom", fill="x")
        spawn_button = tk.Button(bottom_panel,
                                         text=get_locale("track_markup.btn.spawn_window"),
                                         command=self.on_spawn_figure_press)
        spawn_button.pack(side="bottom", expand=True, fill="both")
        tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_fuzzy"),
                  command=self.redraw_event).pack(side="bottom", expand=True, fill="both")
        self.yes_btn = tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_yes"),
                  command=self.on_track_visible_poll)
        self.no_btn = tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_no"),
                  command=self.on_track_invisible_poll)
        if TENSORFLOW_INSTALLED:
            self.auto_btn = tk.Button(bottom_panel, text=get_locale("track_markup.btn.im_too_lazy"),
                      command=self.on_auto)
        else:
            self.auto_btn = None
        #self.yes_btn.pack(side="left", expand=True, fill="both")
        #self.no_btn.pack(side="right", expand=True, fill="both")

        self.start_btn = tk.Button(bottom_panel, text=get_locale("track_markup.btn.start"),
                                command=self.on_start)
        self.start_btn.pack(expand=True, fill="both")

        self.just_started =  True
        #self.plotter.on_right_click_callback = self.popup_draw_signal
        #self.plotter.on_right_click_callback_outofbounds = self.popup_draw_all
        PopupPlotable.__init__(self, self.plotter)
        # self.reset_events()
        self.retractable_event = False
        self.event_in_queue = True, None
        self.selected_data.bind('<<ListboxSelect>>', self.on_review_trackless_select)
        self.rejected_data.bind('<<ListboxSelect>>', self.on_review_tracked_select)
        self.update_highlight_button()
        self.update_answer_panel()




    def on_export_bg(self):
        if self.trackless_events and self.file:
            fbase = self.get_loaded_filename()
            fbase = ospath.splitext(fbase)[0]
            filename = TRACKS_WORKSPACE.asksaveasfilename(auto_formats=["zip"], initialfile=f"bg-{fbase}.zip")
            if filename:
                with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    index = 1
                    for bg_start, bg_end in self.trackless_events_events:
                        buffer = io.BytesIO(b"")
                        h5_file = h5py.File(buffer, "w")

                        # plot_data = self.file["data0"][track_start:track_end]
                        plot_data = self._get_data_at(bg_start, bg_end, True)
                        ut0 = self.file["UT0"][bg_start:bg_end]


                        assert plot_data.shape[0] == ut0.shape[0]
                        h5_file.create_dataset("data0", data=plot_data)
                        h5_file.create_dataset("UT0", data=ut0)

                        h5_file.close()
                        zipf.writestr(f"f{index}_bg_{bg_start}_{bg_end}.h5", buffer.getvalue())
                        index += 1

    def on_export_data(self):
        if self.tracked_events and self.file and self.tf_model:
            fbase = self.get_loaded_filename()
            fbase = ospath.splitext(fbase)[0]
            filename = TRACKS_WORKSPACE.asksaveasfilename(auto_formats=["zip"], initialfile=f"tracks-{fbase}.zip")
            if filename:
                with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    index = 1
                    for track_start, track_end in self.tracked_events:
                        buffer = io.BytesIO(b"")
                        h5_file = h5py.File(buffer, "w")

                        #plot_data = self.file["data0"][track_start:track_end]
                        plot_data, plot_data_cutter = self._get_data_at_semiprepared(track_start, track_end, True, margin_add=256)
                        ut0 = self.file["UT0"][track_start:track_end]
                        self.sync_form()
                        trigger:EdgeProcessor = self.form_data["trigger"]
                        #bl, br, tl, tr = self.form_data["trigger"].get_triggering(self, plot_data)
                        res = self.tf_model.trigger_split(plot_data, trigger.threshold)
                        plot_data = plot_data[plot_data_cutter]
                        bl, br, tl, tr = [item.any() for item in res]

                        print(f"TRACK {index}:")
                        print_track(bl, br, tl, tr)

                        #self.tf_model.trigger_split(plot_data, threshold, broken, ts_filter)

                        assert plot_data.shape[0] == ut0.shape[0]
                        h5_file.create_dataset("data0", data=plot_data)
                        h5_file.create_dataset("UT0", data=ut0)
                        h5_file.attrs["bottom_left"] = bl
                        h5_file.attrs["bottom_right"] = br
                        h5_file.attrs["top_left"] = tl
                        h5_file.attrs["top_right"] = tr

                        h5_file.close()
                        zipf.writestr(f"f{index}_track_{track_start}_{track_end}.h5", buffer.getvalue())
                        index += 1
                        # tgtfile = zipf.open(f"track_{track_start}_{track_end}", "w")
                        #tgtfile.close()



    def update_answer_panel(self):
        if not self.event_set and self.current_event:
            self.start_btn.pack_forget()
            self.yes_btn.pack(side="left", expand=True, fill="both")
            self.no_btn.pack(side="right", expand=True, fill="both")
            if self.auto_btn:
                self.auto_btn.pack(expand=True, fill="both")
            self.event_set = True
        elif self.event_set and not self.current_event:
            self.yes_btn.pack_forget()
            self.no_btn.pack_forget()
            if self.auto_btn:
                self.auto_btn.pack_forget()
            self.start_btn.pack(expand=True, fill="both")
            self.event_set = False


    def update_highlight_button(self):
        if self.just_started:
            self.yes_btn.config(fg="red")
            self.no_btn.config(fg="red")
            self.start_btn.config(fg="red")
            if self.auto_btn:
                self.auto_btn.config(fg="red")
        else:
            self.yes_btn.config(fg="black")
            self.no_btn.config(fg="black")
            self.start_btn.config(fg="black")
            if self.auto_btn:
                self.auto_btn.config(fg="black")

    def on_loaded_file_success(self):
        self.just_started = True
        self.current_event = None
        self.clear_events()

    def on_spawn_figure_press(self):
        self.create_plotter()

    def on_reset(self):
        if tkinter.messagebox.askokcancel(
                get_locale("track_markup.messagebox.reset.title"),
                get_locale("track_markup.messagebox.reset.content"),
                parent=self):
            self.reset_events()


    def clear_tracks(self):
        self.tracked_events.clear()
        self.rejected_data.delete(0, tk.END)

    def clear_trackless(self):
        self.trackless_events.clear()
        self.selected_data.delete(0, tk.END)

    def clear_events(self):
        self.current_event = None
        self.clear_tracks()
        self.clear_trackless()
        self.queue.clear()
        self.update_highlight_button()
        self.update_answer_panel()

    def reset_events(self):
        newformdata = ResetAsker(self)
        form_data = newformdata.result
        if form_data:
            self.current_event = None
            self.selected_data.delete(0, tk.END)
            self.rejected_data.delete(0, tk.END)
            self.trackless_events.clear()
            self.tracked_events.clear()
            self.queue.clear()
            #form_data = self.params_form.get_values()
            if self.file:

                data0 = self.file["data0"]
                max_frame = form_data["max_frame"]
                if max_frame==0:
                    self.queue.append([form_data["start_skip"], len(data0)-form_data["end_skip"]])
                else:
                    for frame_start in range(form_data["start_skip"], len(data0)-form_data["end_skip"]-max_frame, max_frame):
                        self.queue.append([frame_start, frame_start + max_frame])
                    last = self.queue[-1][1]
                    if last<len(data0)-form_data["end_skip"]-1:
                        self.queue.append([last,len(data0)-form_data["end_skip"]])
                self.just_started = False
            self.update_highlight_button()
            self.update_answer_panel()
            return True
        else:
            return False

    def show_next_event(self):
        while self.show_next_event_it():
            pass


    def retract_event(self):
        if self.current_event is None:
            self.retractable_event = False
        if self.retractable_event:
            self.queue.insert(0, list(self.current_event))
            self.retractable_event = False

    def redraw_event(self):
        if self.file and self.current_event:
            self.sync_form()
            form_data = self.params_form.get_values()
            print(self.queue)
            event_start, event_end = self.current_event
            #plot_data = self.file["data0"][event_start:event_end]
            model = self.get_ff_model()
            if model:
                self.plotter.set_broken(model.broken_query())
            plot_data = self._get_current_data()
            plot_data = np.max(plot_data, axis=0)
            pmt = form_data["pmt_select"]
            real_plot_data = np.zeros(shape=plot_data.shape)
            if pmt == "bottomleft":
                real_plot_data[:, :] = np.min(plot_data[:8, :8])
                real_plot_data[:8, :8] = plot_data[:8, :8]
            elif pmt == "bottomright":
                real_plot_data[:, :] = np.min(plot_data[8:, :8])
                real_plot_data[8:, :8] = plot_data[8:, :8]
            elif pmt == "topleft":
                real_plot_data[:, :] = np.min(plot_data[:8, 8:])
                real_plot_data[:8, 8:] = plot_data[:8, 8:]
            elif pmt == "topright":
                real_plot_data[:, :] = np.min(plot_data[8:, 8:])
                real_plot_data[8:, 8:] = plot_data[8:, 8:]
            else:
                real_plot_data = plot_data

            assert real_plot_data.shape == (16,16)

            self.plotter.buffer_matrix = real_plot_data
            self.plotter.update_matrix_plot(True)
            self.plotter.axes.set_title(f"{event_start} - {event_end} ({event_end - event_start})")
            self.plotter.draw()
            return False

    def show_next_event_it(self):
        if self.file:
            if not self.queue:
                tk.messagebox.showinfo(
                    get_locale("track_markup.messagebox.markup_done.title"),
                    get_locale("track_markup.messagebox.markup_done.content"),
                    parent=self
                )
                self.retractable_event = False
                self.current_event = None
                return False
            form_data = self.form_data
            print(self.queue)
            event_start, event_end = self.queue.pop(0)
            self.retractable_event = True
            self.event_in_queue = True, None
            if (event_end-event_start) < form_data["min_frame"]:
                self.add_tracked_event(event_start, event_end)
                return True
            self.current_event = event_start, event_end
            return self.redraw_event()

    def on_track_visible_poll(self):
        self.on_poll(True)

    def on_track_invisible_poll(self):
        self.on_poll(False)

    def on_start(self):
        self.sync_form()
        if self.just_started:
            if not self.reset_events():
                return
        self.show_next_event()
        self.update_answer_panel()
        self.update_highlight_button()

    def on_recheck_tracks(self):
        self.retract_event()
        self.queue = self.queue + list(self.tracked_events)
        self.clear_tracks()
        self.show_next_event()
        self.update_answer_panel()
        gc.collect()


    def on_auto(self):
        gc.collect()
        self.sync_form()
        if self.tf_model is None:
            self.on_load_tf()
        if self.tf_model is None:
            # Model was not loaded during last time. Do nothing
            return
        if self.current_event is None:
            return

        trigger_params: EdgeProcessor = self.form_data["trigger"]

        x_data, xdata_cut = self._get_current_data_semiprepared(True, margin_add=128)
        event_start, event_end = self.current_event
        booled_full = self.tf_model.trigger(x_data, trigger_params.threshold)
        booled_full = booled_full[xdata_cut]
        print(booled_full.any())
        print(booled_full)
        ranges = edged_intervals(booled_full)
        print(ranges)
        pos, neg = split_intervals(np.array(ranges), event_start)

        #pos, neg = self.form_data["trigger"].apply(self)
        print("TRACKS:", pos)
        print("NO TRACKS", neg)
        if not self.event_in_queue[0]:
            if self.event_in_queue[1][1]:
                self.pop_event(self.event_in_queue[1][0], True)
            else:
                self.pop_event(self.event_in_queue[1][0], False)

        for r in pos:
            self.add_tracked_event(r[0], r[1])

        for r in neg:
            self.add_trackless_event(r[0], r[1])

        self.show_next_event()
        self.update_answer_panel()
        gc.collect()
        if self.form_data["auto_cont"]:
            self.after(1000, self.on_auto_cont)

    def on_auto_cont(self):
        self.sync_form()
        if self.form_data["auto_cont"]:
            self.on_auto()

    def on_poll(self, result):
        self.sync_form()
        if self.current_event is not None:
            start, end = self.current_event
            assert end>=start
            if result:
                midpoint = (end+start)//2
                print(f"{start}->{midpoint}<-{end}")
                assert start <= midpoint
                assert midpoint <= end
                subdivide = True
                if not self.event_in_queue[0]:
                    if self.event_in_queue[1][1]:
                        self.pop_event(self.event_in_queue[1][0], True)
                    else:
                        self.pop_event(self.event_in_queue[1][0], False)
                        # subdivide = False

                if subdivide:
                    self.queue.append([start, midpoint])
                    self.queue.append([midpoint, end])
            else:
                if self.event_in_queue[0]:
                    self.add_trackless_event(start, end)
                elif not self.event_in_queue[1][1]:
                    start, end = self.pop_event(self.event_in_queue[1][0], False)
                    print("POPPED EVENT:",start,end)
                    self.add_trackless_event(start, end)
            self.show_next_event()
            self.update_answer_panel()

    def add_trackless_event(self, start, end):
        if try_append_event(self.trackless_events,start,end):
            self.trackless_events = stitch_events(self.trackless_events)
            self.selected_data.delete(0,tk.END)
            for start, end in self.trackless_events:
                self.selected_data.insert(tk.END, f"{start} - {end}")

    def add_tracked_event(self, start, end):
        if try_append_event(self.tracked_events, start, end):
            self.tracked_events = stitch_events(self.tracked_events)
            self.rejected_data.delete(0, tk.END)
            for start, end in self.tracked_events:
                self.rejected_data.insert(tk.END, f"{start} - {end}")

    def pop_event(self, index, use_accepted):
        if use_accepted:
            self.selected_data.delete(index)
            return self.trackless_events.pop(index)
        else:
            self.rejected_data.delete(index)
            return self.tracked_events.pop(index)

    def on_save_data(self):
        fbase = self.get_loaded_filename()
        fbase = ospath.splitext(fbase)[0]

        save_path = MARKUP_WORKSPACE.asksaveasfilename(initialdir=".",filetypes=(("JSON", "*.json"),),
                                                         initialfile=f"track_progress-{fbase}.json", parent=self)
        if save_path:
            current_queue = self.queue.copy()
            if self.current_event is not None and self.retractable_event:
                current_queue.insert(0, self.current_event)
                #current_queue = [self.current_event] + current_queue
            save_data = {
                "queue": current_queue,
                "found_event": self.trackless_events,
                "rejected_event": self.tracked_events,
                "configuration": self.params_form.get_values()
            }
            with open(save_path, "w") as fp:
                json.dump(save_data, fp)

    def on_load_data(self):
        load_path = MARKUP_WORKSPACE.askopenfilename(initialdir=".", filetypes=(("JSON", "*.json"),),
                                                         initialfile="progress.json", parent=self)
        if load_path:
            self.clear_events()
            with open(load_path, "r") as fp:
                save_data = json.load(fp)
                self.clear_events()
                self.queue = save_data["queue"]
                for e in save_data["found_event"]:
                    self.add_trackless_event(e[0], e[1])
                for e in save_data["rejected_event"]:
                    self.add_tracked_event(e[0],e[1])
                self.params_form.set_values(save_data["configuration"])

                self.just_started = False
                self.show_next_event()
                self.update_highlight_button()
                self.update_answer_panel()

    def on_load_tf(self):
        filename = TENSORFLOW_MODELS_WORKSPACE.askopenfilename(
            title=get_locale("app.filedialog.load_model.title"),
            filetypes=[(get_locale("app.filedialog_formats.model"), "*.h5")]
        )
        if filename:
            self.tf_model = ModelWrapper.load_model(filename)
            self.tf_filter = self.tf_model.get_filter()
            self.tf_filter_info.set("ANN "+self.tf_filter.get_representation())

    def on_review_trackless_select(self, evt):
        return self.on_review_select_universal(evt, True)

    def on_review_tracked_select(self, evt):
        return self.on_review_select_universal(evt, False)

    def on_review_select_universal(self, evt, use_accepted):
        # Note here that Tkinter passes an event object to onselect()
        w = evt.widget
        if not w.curselection():
            return
        event_index = int(w.curselection()[0])
        self.retract_event()
        if use_accepted:
            self.current_event = self.trackless_events[event_index]
        else:
            self.current_event = self.tracked_events[event_index]
        self.event_in_queue = False, (event_index, use_accepted)
        self.update_answer_panel()
        self.redraw_event()

    def sync_form(self):
        raw_form_data = self.params_form.get_values()
        self.params_form_parser.parse_formdata(raw_form_data)
        self.form_data = self.params_form_parser.get_data()

    def get_filter_for_nn(self):
        if self.form_data["override_ann_filter"] or not self.tf_model:
            return self.form_data["preprocessing"]

    def get_broken(self):
        return np.logical_not(self.plotter.alive_pixels_matrix)


    def get_filter(self, use_nn=False) -> DataThreeStagePreProcessor:
        if self.form_data["override_ann_filter"] or not use_nn or not self.tf_model:
            return self.form_data["preprocessing"]
        else:
            return self.tf_filter

    def apply_filter(self, signal, use_nn=False):
        self.sync_form()
        preprocessor = self.get_filter(use_nn)
        broken = self.plotter.get_broken()
        plot_data = preprocessor.preprocess_whole(signal, broken)
        return plot_data


    def _get_data_at_semiprepared(self, t1, t2, use_nn_filter=False, margin_add=0):
        # signal = self.file["data0"][t1:t2]
        signal, signal_cutter = self.get_filter(use_nn_filter).prepare_array(self.file["data0"], t1, t2,
                                                                             margin_add=margin_add)
        model = self.get_ff_model()
        if model:
            signal = model.apply(signal)
            signal[:, np.logical_not(self.plotter.alive_pixels_matrix)] = 0

        current_data = self.apply_filter(signal, use_nn_filter)
        # current_data = current_data[signal_cutter]
        # print("ACCESSED", current_data.shape)
        return current_data, signal_cutter

    def _get_current_data_semiprepared(self, use_nn_filter=False, margin_add=0):
        t1, t2 = self.current_event
        return self._get_data_at_semiprepared(t1,t2,use_nn_filter,margin_add)

    def _get_data_at(self, t1, t2, use_nn_filter=False):
        # signal = self.file["data0"][t1:t2]
        current_data, signal_cutter = self._get_data_at_semiprepared(t1, t2, use_nn_filter, margin_add=0)
        return current_data[signal_cutter]

    def _get_current_data(self, use_nn_filter=False):
        t1, t2 = self.current_event
        return self._get_data_at(t1,t2,use_nn_filter)

    def get_plot_data(self):
        if self.file and self.current_event:
            t1, t2 = self.current_event
            plot_data = self._get_current_data()
            xs = np.arange(t1, t2)
            return xs, plot_data

    def postprocess_plot(self, axes):
        self.sync_form()
        trigger_params: EdgeProcessor = self.form_data["trigger"]
        if self.tf_model and self.current_event:
            e_start, e_end = self.current_event
            if trigger_params.max_plot >= abs(e_end - e_start) >= 128:
                #self.form_data["trigger"].get_prob(self, axes)
                x_data, cutter = self._get_current_data_semiprepared(True, margin_add=256)
                self.tf_model.plot_over_data(x_data, e_start, e_end, axes, cutter=cutter)



