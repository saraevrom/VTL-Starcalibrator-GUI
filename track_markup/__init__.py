import tkinter as tk
from plotter import GridPlotter
from tool_base import ToolBase
from .sorted_queue import SortedQueue
from numpy.lib.stride_tricks import sliding_window_view
import os
import os.path
import numpy as np
from tk_forms import TkDictForm
import tkinter.messagebox
import tkinter.filedialog
import json
from localization import get_locale
from flatfielder import FlatFieldingModel
import matplotlib.pyplot as plt

FORM_CONF = {
    "filter_win":{
        "type": "int",
        "default": 10,
        "display_name": get_locale("track_markup.form.filter_win")
    },
    # "signal_filter_win":{
    #     "type": "int",
    #     "default": 2,
    #     "display_name": get_locale("track_markup.form.signal_filter_win")
    # },
    "min_frame": {
        "type": "int",
        "default": 256,
        "display_name": get_locale("track_markup.form.min_frame")
    },
    "max_frame": {
        "type": "int",
        "default": 0,
        "display_name": get_locale("track_markup.form.max_frame")
    },
    "start_skip":{
        "type": "int",
        "default": 0,
        "display_name": get_locale("track_markup.form.start_skip")
    },
    "end_skip":{
        "type": "int",
        "default": 0,
        "display_name": get_locale("track_markup.form.end_skip")
    },
    "pmt_select": {
        "type": "combo",
        "default": "full",
        "display_name": get_locale("track_markup.form.pmt_select"),
        "values": ["full", "topright", "topleft", "bottomright", "bottomleft"],
        "readonly": True
    }
}

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

class TrackMarkup(ToolBase):
    def __init__(self, master):
        super(TrackMarkup, self).__init__(master)
        self.title(get_locale("track_markup.title"))
        self.plotter = GridPlotter(self)
        self.get_mat_file()
        left_panel = tk.Frame(self)
        left_panel.pack(side="left", fill="y")
        self.queue = []
        self.trackless_events = []
        self.tracked_events = []
        self.model = None

        self.current_event = None

        self.selected_data = tk.Listbox(left_panel, selectmode="single")
        self.selected_data.pack(side="bottom", fill="both", expand=True)
        #tk.Button(left_panel, text=get_locale("track_markup.btn.remove_selected"),
        #          command=self.on_element_delete).pack(side="top", fill="x")
        tk.Label(left_panel,text=get_locale("track_markup.label.accepted")).pack(side="bottom", fill="x", expand=False)
        self.rejected_data = tk.Listbox(left_panel, selectmode="single")
        self.rejected_data.pack(side="bottom", fill="both", expand=True)
        tk.Label(left_panel,text=get_locale("track_markup.label.rejected")).pack(side="bottom", fill="x", expand=False)
        right_panel = tk.Frame(self)
        right_panel.pack(side="right")
        tk.Button(right_panel, text=get_locale("track_markup.btn.reset"),
                  command=self.on_reset).grid(row=0, column=0, sticky="ew")
        tk.Button(right_panel, text=get_locale("track_markup.btn.save"),
                  command=self.on_save_data).grid(row=1, column=0, sticky="ew")
        tk.Button(right_panel, text=get_locale("track_markup.btn.load"),
                  command=self.on_load_data).grid(row=2, column=0, sticky="ew")

        self.params_form = TkDictForm(right_panel, FORM_CONF)
        self.params_form.grid(row=3, column=0, sticky="ew", columnspan=2)

        self.plotter.pack(side="top", expand=True, fill="both")
        bottom_panel = tk.Frame(self)
        bottom_panel.pack(side="bottom", fill="x")
        tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_fuzzy"),
                  command=self.redraw_event).pack(side="bottom", expand=True, fill="both")
        tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_yes"),
                  command=self.on_track_visible_poll).pack(side="left", expand=True, fill="both")
        tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_no"),
                  command=self.on_track_invisible_poll).pack(side="right", expand=True, fill="both")

        self.just_started =  True
        self.plotter.on_right_click_callback = self.popup_draw_signal
        self.plotter.on_right_click_callback_outofbounds = self.popup_draw_all
        # self.reset_events()
        self.retractable_event = False
        self.event_in_queue = True, None
        self.selected_data.bind('<<ListboxSelect>>', self.on_review_trackless_select)
        self.rejected_data.bind('<<ListboxSelect>>', self.on_review_tracked_select)

    def on_reset(self):
        if tkinter.messagebox.askokcancel(
                get_locale("track_markup.messagebox.reset.title"),
                get_locale("track_markup.messagebox.reset.content")):
            self.reset_events()

    def reset_events(self):
        self.current_event = None
        self.selected_data.delete(0, tk.END)
        self.rejected_data.delete(0, tk.END)
        self.trackless_events.clear()
        self.tracked_events.clear()
        self.queue.clear()
        form_data = self.params_form.get_values()
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

    def show_next_event(self):
        while self.show_next_event_it():
            pass


    def retract_event(self):
        if self.retractable_event:
            self.queue.insert(0, list(self.current_event))
            self.retractable_event = False

    def redraw_event(self):
        if self.file and self.current_event:
            form_data = self.params_form.get_values()
            win = form_data["filter_win"]
            #win_s = form_data["signal_filter_win"]
            # if win_s < 1:
            #     win_s = 1
            # if win_s > win:
            #     win_s = win
            print(self.queue)
            event_start, event_end = self.current_event
            #self.current_event = event_start, event_end
            plot_data = self.file["data0"][event_start:event_end]

            if os.path.isfile("flat_fielding.json"):
                if self.model is None:
                    self.model = FlatFieldingModel.load("flat_fielding.json")

                plot_data = self.model.apply(plot_data)
                self.plotter.set_broken(self.model.broken_query())

            #filtered_fg = np.mean(sliding_window_view(plot_data, axis=0, window_shape=win_s), axis=-1)
            filtered_bg = np.mean(sliding_window_view(plot_data, axis=0, window_shape=win), axis=-1)
            plot_data = plot_data[win//2:win//2+filtered_bg.shape[0]] - filtered_bg
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

            #print(real_plot_data)
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
                    get_locale("track_markup.messagebox.markup_done.content")
                )
                self.retractable_event = False
                return False
            form_data = self.params_form.get_values()
            win = form_data["filter_win"]
            print(self.queue)
            event_start, event_end = self.queue.pop(0)
            self.retractable_event = True
            self.event_in_queue = True, None
            if (event_end-event_start) < win or (event_end-event_start)<form_data["min_frame"]:
                self.add_tracked_event(event_start, event_end)
                return True
            self.current_event = event_start, event_end
            return self.redraw_event()

    def on_track_visible_poll(self):
        self.on_poll(True)

    def on_track_invisible_poll(self):
        self.on_poll(False)

    def on_poll(self, result):
        if self.just_started:
            self.reset_events()
            self.just_started = False
        if self.current_event is None:
            self.show_next_event()
        else:
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
                        subdivide = False

                if subdivide:
                    self.queue.append([start, midpoint])
                    self.queue.append([midpoint, end])
                self.show_next_event()
            else:
                if self.event_in_queue[0]:
                    self.add_trackless_event(start, end)
                elif not self.event_in_queue[1][1]:
                    start, end = self.pop_event(self.event_in_queue[1][0], False)
                    print("POPPED EVENT:",start,end)
                    self.add_trackless_event(start, end)
                self.show_next_event()

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
        save_path = tkinter.filedialog.asksaveasfilename(initialdir=".",filetypes=(("JSON", "*.json"),),
                                                         initialfile="progress.json")
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
        load_path = tkinter.filedialog.askopenfilename(initialdir=".", filetypes=(("JSON", "*.json"),),
                                                         initialfile="progress.json")
        if load_path:
            self.reset_events()
            with open(load_path, "r") as fp:
                save_data = json.load(fp)
                self.queue = save_data["queue"]
                for e in save_data["found_event"]:
                    self.add_trackless_event(e[0], e[1])
                for e in save_data["rejected_event"]:
                    self.add_tracked_event(e[0],e[1])
                self.params_form.set_values(save_data["configuration"])
                self.show_next_event()

    def on_element_delete(self):
        pass


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
        self.redraw_event()

        #value = w.get(index)
        #print('You selected item %d: "%s"' % (index, value))

    def apply_filter(self,signal):
        form_data = self.params_form.get_values()
        win = form_data["filter_win"]
        # win_s = form_data["signal_filter_win"]
        # if win_s < 1:
        #     win_s = 1
        # if win_s > win:
        #     win_s = win

        filtered_bg = np.mean(sliding_window_view(signal, axis=0, window_shape=win), axis=-1)
        plot_data = signal[win // 2: win // 2 + filtered_bg.shape[0]] - filtered_bg
        return plot_data

    def popup_draw_all(self):
        if self.file and self.current_event:
            t1, t2 = self.current_event
            signal = self.file["data0"][t1:t2]
            if os.path.isfile("flat_fielding.json"):
                if self.model is None:
                    self.model = FlatFieldingModel.load("flat_fielding.json")
                signal = self.model.apply(signal)
                signal[:, np.logical_not(self.plotter.alive_pixels_matrix)] = 0

            plot_data = self.apply_filter(signal)
            fig, ax = plt.subplots()
            xs = np.linspace(t1, t2, len(plot_data))
            for i in range(16):
                for j in range(16):
                    ax.plot(xs, plot_data[:,i,j])
            fig.show()

    def popup_draw_signal(self, i, j):
        if self.file and self.current_event:
            t1, t2 = self.current_event
            signal = self.file["data0"][t1:t2, i, j]
            if os.path.isfile("flat_fielding.json"):
                if self.model is None:
                    self.model = FlatFieldingModel.load("flat_fielding.json")
                signal = self.model.apply_single_nobreak(signal,i,j)

            plot_data = self.apply_filter(signal)


            fig, ax = plt.subplots()
            xs = np.linspace(t1, t2, len(plot_data))
            ax.plot(xs, plot_data)
            ax.set_title(f"[{i}, {j}]")
            fig.show()
