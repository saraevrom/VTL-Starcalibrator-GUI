import tkinter as tk
from tkinter import ttk
from common_GUI import EntryWithEnterKey
from common_GUI.double_slider import DoubleSlider

FAST_FWD_SKIP = 1
FRAME_DELAY = 1 #ms



class ControlButtons(ttk.Frame):
    PAUSE = 0
    PLAYING = 1
    PLAYING_INV = 2
    FAST_FWD = 3
    REWIND = 4
    STEP_R = 5
    STEP_L = 6
    MUL_TABLE = [0, 1, -1, FAST_FWD_SKIP, -FAST_FWD_SKIP, 1, -1]
    def __init__(self, master):
        super(ControlButtons, self).__init__(master)
        self.playing_state = self.PAUSE
        self.multiplier = 1
        tk.Button(self, text="<<", command=lambda: self.on_button_press(self.REWIND))\
            .grid(row=0, column=0, sticky="nsew")
        tk.Button(self, text="<", command=lambda: self.on_button_press(self.PLAYING_INV))\
            .grid(row=0, column=1, sticky="nsew")
        tk.Button(self, text="<|", command=lambda: self.on_button_press(self.STEP_L)) \
            .grid(row=0, column=2, sticky="nsew")
        tk.Button(self, text="||", command=lambda: self.on_button_press(self.PAUSE))\
            .grid(row=0, column=3, sticky="nsew")
        tk.Button(self, text="|>", command=lambda: self.on_button_press(self.STEP_R)) \
            .grid(row=0, column=4, sticky="nsew")
        tk.Button(self, text=">", command=lambda: self.on_button_press(self.PLAYING))\
            .grid(row=0, column=5, sticky="nsew")
        tk.Button(self, text=">>", command=lambda: self.on_button_press(self.FAST_FWD))\
            .grid(row=0, column=6, sticky="nsew")
        self.button_callback = None

        self.rowconfigure(0, weight=1)

    def on_button_press(self, btn):
        if self.playing_state == btn == self.REWIND:
            self.multiplier *= 2
        elif self.playing_state == btn == self.FAST_FWD:
            self.multiplier *= 2
        else:
            self.multiplier = 1
        self.playing_state = btn
        if self.button_callback is not None:
            self.button_callback()

    def get_frame_step(self):
        return self.MUL_TABLE[self.playing_state]*self.multiplier

    def stop_playing(self):
        self.playing_state = self.PAUSE

    def step_single_check(self):
        if self.playing_state==self.STEP_L or self.playing_state==self.STEP_R:
            self.stop_playing()


class ValuedSlider(ttk.Frame):
    def __init__(self, master):
        super(ValuedSlider, self).__init__(master)
        self.display_variable = tk.StringVar(self)
        self.display_variable.set("0")
        #self.play_slider = ttk.Scale(self, orient=tk.HORIZONTAL, from_=0, to=100, variable=self.value_variable)
        self.play_slider = DoubleSlider(self, low_end=0, high_end=100)
        self.play_slider.grid(row=0, column=0, sticky="nsew")
        self.play_slider.set_slider_callback(self.on_slider_update)
        entry = EntryWithEnterKey(self, textvariable=self.display_variable, width=10)
        entry.grid(row=0, column=1, sticky="nsew")
        entry.on_commit = self.on_display_commit
        self.columnconfigure(0, weight=1)
        self.upper_limit = 100
        self.slider_callback = None
        self.real_value = 0

    def set_slider_callback(self, callback):
        self.slider_callback = callback

    def on_slider_update(self, low, high, pos):
        self.real_value = int(round(pos))
        self.display_variable.set(str(self.real_value))
        if self.slider_callback:
            self.slider_callback()

    def on_display_commit(self):
        pretending = self.display_variable.get()
        try:
            value = int(pretending)
            if value > self.upper_limit:
                value = self.upper_limit
                self.display_variable.set(str(value))
            self.play_slider.move_slider(value)
            self.slider_callback()
        except ValueError:
            pass


    def get_value(self):
        print("GET", self.real_value)
        return self.real_value

    def get_limits(self):
        low, high, pos = self.play_slider.get_params()
        return int(round(low)), int(round(high))

    def set_value(self, v):
        print("SET", v)
        self.real_value = v
        self.display_variable.set(str(self.real_value))
        low, high, pos = self.play_slider.get_params()
        if abs(pos-v)>0.5:
            self.play_slider.move_slider(v)

    def set_limit(self, upper):
        self.play_slider.high_end = upper
        self.upper_limit = upper



class PlayerControls(ttk.Frame):
    def __init__(self, master, frame_callback, click_callback):
        super(PlayerControls, self).__init__(master)
        self.play_slider = ValuedSlider(self)
        self.play_slider.pack(side=tk.TOP,expand=True, fill=tk.X)
        self.control_btns = ControlButtons(self)
        self.control_btns.pack(side=tk.BOTTOM)
        self.upper_limit = 100
        self.control_btns.button_callback = self.on_control_update
        self.play_slider.set_slider_callback(self.on_control_update)
        self.playing = False
        self.frame_callback = frame_callback
        self.click_callback = click_callback

    def set_limit(self, upper):
        self.play_slider.set_limit(upper)
        self.upper_limit = upper

    def on_control_update(self, *_):
        self.click_callback()
        self.start_play_checked()

    def start_play_checked(self):
        if not self.playing:
            self.playing = True
            self.playcycle()

    def draw_frame(self):
        frame_step = self.control_btns.get_frame_step()
        low, high = self.play_slider.get_limits()
        frame_num = self.play_slider.get_value() + frame_step
        if frame_num >= high:
            frame_num = high
            self.control_btns.stop_playing()
        if frame_num < low:
            frame_num = low
            self.control_btns.stop_playing()
        self.frame_callback(frame_num)
        self.play_slider.set_value(frame_num)
        self.control_btns.step_single_check()

    def playcycle(self):
        self.draw_frame()
        if self.control_btns.playing_state != ControlButtons.PAUSE:
            self.after(FRAME_DELAY, self.playcycle)
        else:
            self.playing = False
