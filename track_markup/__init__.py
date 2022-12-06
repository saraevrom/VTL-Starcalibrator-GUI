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

FORM_CONF = {
    "filter_win":{
        "type": "int",
        "default": 60,
        "display_name": get_locale("track_markup.form.filter_win")
    },
    "min_frame": {
        "type": "int",
        "default": 60,
        "display_name": get_locale("track_markup.form.min_frame")
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

        self.current_event = None

        self.selected_data = tk.Listbox(left_panel, selectmode="single")
        self.selected_data.pack(side="bottom", fill="both", expand=True)
        tk.Button(left_panel, text=get_locale("track_markup.btn.remove_selected"),
                  command=self.on_element_delete).pack(side="top", fill="x")
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


        self.reset_events()

    def on_reset(self):
        if tkinter.messagebox.askokcancel(
                get_locale("track_markup.dialog.reset.title"),
                get_locale("track_markup.dialog.reset.content")):
            self.reset_events()

    def reset_events(self):
        self.current_event = None
        self.selected_data.delete(0, tk.END)
        self.trackless_events.clear()
        self.queue.clear()
        form_data = self.params_form.get_values()
        if self.file:
            data0 = self.file["data0"]
            self.queue.append([form_data["start_skip"], len(data0)-form_data["end_skip"]])

    def show_next_event(self):
        while self.show_next_event_it():
            pass

    def redraw_event(self):
        if self.file and self.current_event:
            form_data = self.params_form.get_values()
            win = form_data["filter_win"]
            print(self.queue)
            event_start, event_end = self.current_event
            #self.current_event = event_start, event_end
            plot_data = self.file["data0"][event_start:event_end]

            if os.path.isfile("flat_fielding.npy"):
                with open("flat_fielding.npy", "rb") as f:
                    coeffs = np.load(f)
                    bg = np.load(f)
                    plot_data = (plot_data-bg)/coeffs
                    plot_data = np.nan_to_num(plot_data)
            slides = np.mean(sliding_window_view(plot_data, axis=0, window_shape=win), axis=-1)
            plot_data = plot_data[win//2:win//2+slides.shape[0]] - slides
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

            real_plot_data[coeffs==0] = 0
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
                return False
            form_data = self.params_form.get_values()
            win = form_data["filter_win"]
            print(self.queue)
            event_start, event_end = self.queue.pop(0)
            if (event_end-event_start) < win or (event_end-event_start)<form_data["min_frame"]:
                return True
            self.current_event = event_start, event_end
            return self.redraw_event()

    def on_track_visible_poll(self):
        self.on_poll(True)

    def on_track_invisible_poll(self):
        self.on_poll(False)

    def on_poll(self, result):
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
                self.queue.append([start, midpoint])
                self.queue.append([midpoint, end])
                self.show_next_event()
            else:
                self.add_trackless_event(start, end)
                self.show_next_event()

    def add_trackless_event(self,start,end):
        if [start, end] not in self.trackless_events:
            self.selected_data.insert(tk.END, f"{start} - {end}")
            self.trackless_events.append([start, end])

    def on_save_data(self):
        save_path = tkinter.filedialog.asksaveasfilename(initialdir=".",filetypes=(("JSON", "*.json"),),
                                                         initialfile="progress.json")
        if save_path:
            current_queue = self.queue.copy()
            if self.current_event is not None:
                current_queue = [self.current_event] + current_queue
            save_data = {
                "queue": current_queue,
                "found_event": self.trackless_events,
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
                self.params_form.set_values(save_data["configuration"])
                self.show_next_event()

    def on_element_delete(self):
        pass
