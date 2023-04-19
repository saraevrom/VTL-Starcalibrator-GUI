

import tkinter as tk

from vtl_common.localized_GUI.signal_plotter import PopupPlotable
from vtl_common.common_GUI import TkDictForm
from vtl_common.localized_GUI import GridPlotter
from .form import TrackMarkupForm
from vtl_common.localization import get_locale
from vtl_common.common_GUI.button_panel import ButtonPanel

from ..tool_base import ToolBase
from .interval_storage_with_display import DisplayStorage
from .storage import IntervalStorage, Interval, ArrayStorage
from .reset import ResetAsker
from .display import Display

class ToolMarkup(ToolBase):
    def __init__(self, master):
        ToolBase.__init__(self, master)
        self.display = Display(self)
        self.get_mat_file()

        # PANELS

        left_panel = tk.Frame(self)
        left_panel.pack(side="left", fill="y")

        right_panel = tk.Frame(self)
        right_panel.pack(side="right", fill="y")

        bottom_panel = tk.Frame(self)
        bottom_panel.pack(side="bottom", fill="x")




        self.display.pack(side="top", expand=True, fill="both")

        # Left panel

        self.tracks = DisplayStorage(left_panel, "track_markup.label.rejected")
        self.tracks.grid(row=0, column=0, sticky="nsew")

        self.background = DisplayStorage(left_panel, "track_markup.label.accepted")
        self.background.grid(row=1, column=0, sticky="nsew")


        bottom_left_panel = tk.Frame(left_panel)
        bottom_left_panel.grid(row=2, column=0, sticky="nsew")

        self.schedule = DisplayStorage(bottom_left_panel, "track_markup.label.schedule")
        self.schedule.grid(row=0, column=0,sticky="nsew")

        self.afterprocessing = DisplayStorage(bottom_left_panel, "track_markup.label.schedule_2")
        self.afterprocessing.grid(row=0, column=1, sticky="nsew")
        self.afterprocessing.set_storage(ArrayStorage())

        bottom_left_panel.columnconfigure(0,weight=1)
        bottom_left_panel.columnconfigure(1,weight=1)
        bottom_left_panel.rowconfigure(0,weight=1)


        left_panel.columnconfigure(0,weight=1)
        left_panel.rowconfigure(0,weight=1)
        left_panel.rowconfigure(1,weight=1)
        left_panel.rowconfigure(2,weight=1)

        # Right panel

        self.params_form_parser = TrackMarkupForm()

        self.params_form = TkDictForm(right_panel, self.params_form_parser.get_configuration_root())
        self.params_form.grid(row=2, column=0, sticky="nsew")
        self.params_form.on_commit = self.on_form_changed
        right_panel.rowconfigure(2, weight=1)

        self.button_panel = ButtonPanel(right_panel)

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

        self.button_panel.grid(row=0, column=0, sticky="ew")

        # Bottom panel

        # spawn_button = tk.Button(bottom_panel,
        #                          text=get_locale("track_markup.btn.spawn_window"),
        #                          command=self.on_spawn_figure_press)
        # spawn_button.pack(side="bottom", expand=True, fill="both")
        tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_fuzzy"),
                  command=self.on_redraw_event).pack(side="bottom", expand=True, fill="both")
        self.yes_btn = tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_yes"),
                                 command=self.on_track_visible)
        self.no_btn = tk.Button(bottom_panel, text=get_locale("track_markup.btn.track_no"),
                                command=self.on_track_invisible)

        self.start_btn = tk.Button(bottom_panel, text=get_locale("track_markup.btn.start"),
                                   command=self.on_start)
        self.start_btn.pack(expand=True, fill="both")
        self._formdata = None

        self.on_form_changed()


    def update_answer_panel(self):
        if self.display.storage.has_item():
            self.start_btn.pack_forget()
            self.yes_btn.pack(side="left", expand=True, fill="both")
            self.no_btn.pack(side="right", expand=True, fill="both")
            # if self.auto_btn:
            #     self.auto_btn.pack(expand=True, fill="both")
        else:
            self.yes_btn.pack_forget()
            self.no_btn.pack_forget()
            # if self.auto_btn:
            #     self.auto_btn.pack_forget()
            self.start_btn.pack(expand=True, fill="both")


    def on_form_changed(self):
        formdata = self.params_form.get_values()
        self.params_form_parser.parse_formdata(formdata)
        formdata = self.params_form_parser.get_data()
        self.display.set_formdata(formdata)
        self._formdata = formdata

    #Button press events
    def on_redraw_event(self):
        pass


    def on_track_visible(self):
        if self.ensure_storage():
            interval:Interval
            interval = self.display.storage.take_external()
            if interval is not None:
                if interval.length()<self._formdata["min_frame"]:
                    if not self.tracks.storage.store_external(interval):
                        self.display.storage.store_external(interval)
                else:
                    interval_1, interval_2 = interval.subdivide()
                    self.afterprocessing.storage.store(interval_1)
                    self.afterprocessing.storage.store_external(interval_2)


                self.pull_next_interval()

    def on_track_invisible(self):
        if self.ensure_storage():
            self.display.storage.try_move_to(self.background.storage)
            self.pull_next_interval()

    def on_start(self):
        if self.ensure_storage():
            self.pull_next_interval()


    def pull_next_interval(self):
        if not self.pull_next_interval_from_schedule():
            self.pull_next_interval_from_afterprocessing()
        self.update_answer_panel()

    def pull_next_interval_from_schedule(self):
        print("PULLING NEXT INTERVAL")
        if self.schedule.storage:
            accessible_interval = self.schedule.storage.get_first_accessible()
            if accessible_interval:
                requested_length = self._formdata["max_frame"]
                print("ALLOWED",accessible_interval)

                if accessible_interval.length() > requested_length > 0:
                    desired_interval = Interval(accessible_interval.start,
                                                accessible_interval.start+requested_length)
                else:
                    desired_interval = accessible_interval
                print("DESIRED CHECK",desired_interval)
                print("SLOT",self.display.storage.item)
                return self.schedule.storage.try_move_to(self.display.storage, desired_interval)
        return False

    def pull_next_interval_from_afterprocessing(self):
        return self.afterprocessing.storage.try_move_to(self.display.storage, 0)


    def on_reset(self):
        self.reset()

    def on_recheck_tracks(self):
        avail = self.tracks.storage.get_available()
        for item in avail:
            self.tracks.storage.try_move_to(self.schedule.storage,item)

    def on_save_data(self):
        pass

    def on_load_data(self):
        pass

    def on_export_data(self):
        pass

    def on_export_bg(self):
        pass


    def on_ff_reload(self):
        model = self.get_ff_model()
        if model:
            self.display.set_ffmodel(model)

    def on_loaded_file_success(self):
        self.clear_storage()

    def clear_storage(self):
        self.tracks.disconnect_storage()
        self.background.disconnect_storage()
        self.schedule.disconnect_storage()
        self.afterprocessing.clear()
        self.display.drop()

    def ensure_storage(self):
        if self.schedule.storage is None:
            self.reset()
        return self.schedule.storage is not None

    def reset(self):
        if self.file:
            l = len(self.file["data0"])
            asked = ResetAsker(self, tgt_length=l)
            if asked.result:
                start_cut, end_cut = asked.result
                s = start_cut
                e = l-end_cut
                print("INTERVAL", s,e)
                self.clear_storage()
                self.schedule.set_storage(IntervalStorage(s,e))
                self.tracks.set_storage(IntervalStorage(s,e,empty=True))
                self.background.set_storage(IntervalStorage(s,e,empty=True))
        self.update_answer_panel()