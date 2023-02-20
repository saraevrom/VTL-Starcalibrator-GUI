from localized_GUI.plotter import Plotter
from .datetime_parser import parse_datetimes
import tkinter as tk
from localization import get_locale
from common_GUI.modified_base import EntryWithEnterKey
from datetime import datetime
from tkinter.simpledialog import askstring
import numpy as np
from matplotlib.patches import Rectangle

MARK_LOW = 0
MARK_HIGH = 1
MARK_PTR = 2

class ValueWrapper(tk.Frame):
    def __init__(self, master, validator, mark):
        super().__init__(master)
        self.mark = mark
        self.display_value = tk.StringVar(self)
        self.display_value.set("0")
        self.actual_value = 0
        self.utc_explorer = None
        self.entry = EntryWithEnterKey(self, textvariable=self.display_value)
        self.entry.on_commit = self.on_entry_commit
        self.entry.grid(row=0, column=0, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        btn = tk.Button(self, text=get_locale("matplayer.button.datetime_entry"), command=self.on_datetime_entry)
        btn.grid(row=1, column=0, sticky="nsew")
        self.rowconfigure(1, weight=1)
        self.validator = validator

    def on_entry_commit(self):
        v = self.display_value.get()
        try:
            self.set_value(int(v)) # For convinience
        except ValueError:
            self.display_value.set(str(self.actual_value))

    def on_datetime_entry(self):
        if self.utc_explorer is not None:
            print("UTCS:", self.utc_explorer)
            ans = askstring(title=get_locale("matplayer.button.datetime_entry"),
                           prompt=get_locale("matplayer.dialog.datetime_prompt"))
            if ans:
                start_dt = datetime.utcfromtimestamp(self.utc_explorer[self.get_value()])
                ut0 = parse_datetimes(ans, start_dt)
                print("got UTC:", ut0)
                if ut0 < np.min(self.utc_explorer):
                    return
                if ut0 > np.max(self.utc_explorer):
                    return
                frame = np.argmin(np.abs(self.utc_explorer - ut0))
                print("INTERVAL OK")
                self.set_value(frame)

    def link_time(self, utc_explore):
        self.utc_explorer = utc_explore

    def set_value(self, v, validate=True):
        self.actual_value = v
        self.display_value.set(str(v))
        if self.validator and validate:
            self.validator(self.mark)

    def get_value(self):
        return self.actual_value

    def clamp(self, low, high):
        '''
        clamps stored value between two values (inclusive)
        :param low: Lowest value
        :param high: Highest value
        :return:
        '''
        v = self.get_value()
        if v < low:
            self.set_value(low, validate=False)
        if v > high:
            self.set_value(high, validate=False)

    def clamp_lower(self, reference):
        '''
        sets own value lower or equal to value of reference
        :param reference: instance of ValueWrapper to refer on
        :return:
        '''
        v = self.get_value()
        v_ref = reference.get_value()
        if v > v_ref:
            self.set_value(v_ref, validate=False)

    def clamp_higher(self, reference):
        '''
        sets own value higher or equal to value of reference
        :param reference: instance of ValueWrapper to refer on
        :return:
        '''
        v = self.get_value()
        v_ref = reference.get_value()
        if v < v_ref:
            self.set_value(v_ref, validate=False)

    def sync_to(self, reference):
        '''
        Sets own value to reference
        :param reference:
        :return:
        '''
        v_ref = reference.get_value()
        self.set_value(v_ref)


def set_vlines_position(lines, position):
    seg_old = lines.get_segments()
    ymin = seg_old[0][0, 1]
    ymax = seg_old[0][1, 1]

    seg_new = [np.array([[position, ymin],
                         [position, ymax]])]
    lines.set_segments(seg_new)

class PlayingPosition(Plotter):
    def __init__(self, master):
        super().__init__(master)
        self.axes.set_axis_off()
        self.axes.set_ylim(-1, 1)
        self.mpl_canvas.get_tk_widget().configure(height=100)
        self.figure.tight_layout()
        self.toolbar.pack_forget()

        subframe = tk.Frame(self)
        subframe.pack(side="bottom", fill="x")

        starter = tk.Button(subframe, text=get_locale("matplayer.button.set_start"), command=self.on_lcut)
        starter.grid(row=0, column=0, sticky="ew")

        self.min_cutter = ValueWrapper(subframe, self.validate_intervals, MARK_LOW)
        self.min_cutter.grid(row=0, column=1, sticky="nsew")
        self.pointer = ValueWrapper(subframe, self.validate_intervals, MARK_PTR)
        self.pointer.grid(row=0, column=2, sticky="nsew")
        self.max_cutter = ValueWrapper(subframe, self.validate_intervals, MARK_HIGH)
        self.max_cutter.grid(row=0, column=3, sticky="nsew")

        ender = tk.Button(subframe, text=get_locale("matplayer.button.set_end"), command=self.on_rcut)
        ender.grid(row=0, column=4, sticky="ew")

        self._range_patch = Rectangle((0, -1), 1, 2, color="gray", alpha=0.25)
        self.axes.add_patch(self._range_patch)
        self._mouse_pointer = self.axes.vlines(0, -1, 1, color="black")
        self._frame_pointer = self.axes.vlines(0, -1, 1, color="red")
        self._mouse_pointer_position = 0
        self.figure.canvas.mpl_connect("motion_notify_event", self.on_motion)

        self._low = 0
        self._high = 0
        self.callback = None
        self.set_range(0, 100)


    def on_lcut(self):
        self.min_cutter.sync_to(self.pointer)

    def on_rcut(self):
        self.max_cutter.sync_to(self.pointer)

    def set_mouse_pointer(self, new_x):
        self._mouse_pointer_position = new_x
        set_vlines_position(self._mouse_pointer, new_x)
        self.draw()

    def on_motion(self, event):
        if (event.xdata is not None):
            x = int(round(event.xdata))
            self.set_mouse_pointer(x)
            self.figure.canvas.draw_idle()
            if event.button == 1:
                self.set_frame(x)

    def update_interval(self):
        low_v = self.min_cutter.get_value()
        high_v = self.max_cutter.get_value()
        self._range_patch.set_x(low_v)
        self._range_patch.set_width(high_v-low_v)

    def set_range(self, low, high):
        self._low = low
        self._high = high
        self.axes.set_xlim(low, high)
        self.min_cutter.set_value(low)
        self.max_cutter.set_value(high)

    def get_range_full(self):
        return self._low, self._high

    def get_range_selected(self):
        return self.min_cutter.get_value(), self.max_cutter.get_value()

    def get_frame(self):
        return self.pointer.get_value()

    def set_frame(self, v):
        self.pointer.set_value(v)

    def validate_intervals(self, asker):
        self.min_cutter.clamp(self._low, self._high)
        self.max_cutter.clamp(self._low, self._high)
        if asker == MARK_LOW:
            self.max_cutter.clamp_higher(self.min_cutter)
        elif asker == MARK_HIGH:
            self.min_cutter.clamp_lower(self.max_cutter)

        if asker == MARK_PTR:
            v_min = self.min_cutter.get_value()
            v_max = self.max_cutter.get_value()
            width = v_max - v_min
            v = self.pointer.get_value()
            if v > v_max:
                self.max_cutter.set_value(v, False)
                #self.min_cutter.set_value(v-width, False)
            if v < v_min:
                #self.max_cutter.set_value(v+width, False)
                self.min_cutter.set_value(v, False)
        else:
            self.pointer.clamp(self._low, self._high)
            self.pointer.clamp_higher(self.min_cutter)
            self.pointer.clamp_lower(self.max_cutter)

        set_vlines_position(self._frame_pointer, self.pointer.get_value())
        self.update_interval()
        self.draw()
        if self.callback:
            self.callback()

    def link_time(self, utc_explorer):
        self.min_cutter.link_time(utc_explorer)
        self.max_cutter.link_time(utc_explorer)
        self.pointer.link_time(utc_explorer)