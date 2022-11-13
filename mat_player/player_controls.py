import tkinter as tk
from tkinter import ttk

FAST_FWD_SKIP = 10
FRAME_DELAY = 100 #ms



class ControlButtons(ttk.Frame):
    PAUSE = 0
    PLAYING = 1
    PLAYING_INV = 2
    FAST_FWD = 3
    REWIND = 4
    MUL_TABLE = [0, 1, -1, FAST_FWD_SKIP, -FAST_FWD_SKIP]
    def __init__(self, master):
        super(ControlButtons, self).__init__(master)
        self.playing_state = self.PAUSE
        tk.Button(self, text="<<", command=lambda: self.on_button_press(self.REWIND))\
            .grid(row=0, column=0, sticky="nsew")
        tk.Button(self, text="<", command=lambda: self.on_button_press(self.PLAYING_INV))\
            .grid(row=0, column=1, sticky="nsew")
        tk.Button(self, text="||", command=lambda: self.on_button_press(self.PAUSE))\
            .grid(row=0, column=2, sticky="nsew")
        tk.Button(self, text=">", command=lambda: self.on_button_press(self.PLAYING))\
            .grid(row=0, column=3, sticky="nsew")
        tk.Button(self, text=">>", command=lambda: self.on_button_press(self.FAST_FWD))\
            .grid(row=0, column=4, sticky="nsew")
        self.button_callback = None

    def on_button_press(self, btn):
        self.playing_state = btn
        if self.button_callback is not None:
            self.button_callback()

    def get_frame_step(self):
        return self.MUL_TABLE[self.playing_state]

    def stop_playing(self):
        self.playing_state = self.PAUSE


class ValuedSlider(ttk.Frame):
    def __init__(self, master):
        super(ValuedSlider, self).__init__(master)
        self.value_variable = tk.IntVar(self)
        self.display_variable = tk.StringVar(self)
        self.display_variable.set("0")
        self.value_variable.trace("w", self.on_slider_update)
        self.play_slider = ttk.Scale(self, orient=tk.HORIZONTAL, from_=0, to=100, variable=self.value_variable)
        self.play_slider.grid(row=0, column=0, sticky="nsew")
        tk.Label(self, textvariable=self.display_variable, width=10).grid(row=0, column=1, sticky="nsew")
        self.columnconfigure(0, weight=1)
        self.upper_limit = 100

    def set_slider_callback(self, callback):
        self.play_slider.config(command=callback)

    def on_slider_update(self, *_):
        self.display_variable.set(str(self.value_variable.get()))

    def get_value(self):
        return self.value_variable.get()

    def set_value(self, v):
        return self.value_variable.set(v)

    def set_limit(self, upper):
        self.play_slider.config(to=upper)
        self.upper_limit = upper



class PlayerControls(ttk.Frame):
    def __init__(self, master, frame_callback):
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

    def set_limit(self, upper):
        self.play_slider.set_limit(upper)
        self.upper_limit = upper

    def on_control_update(self, *_):
        self.start_play_checked()

    def start_play_checked(self):
        if not self.playing:
            self.playing = True
            self.playcycle()

    def draw_frame(self):
        frame_step = self.control_btns.get_frame_step()
        frame_num = self.play_slider.get_value() + frame_step
        if frame_num >= self.upper_limit:
            frame_num = self.upper_limit - 1
            self.control_btns.stop_playing()
        if frame_num < 0:
            frame_num = 0
            self.control_btns.stop_playing()
        self.frame_callback(frame_num)
        self.play_slider.set_value(frame_num)

    def playcycle(self):
        self.draw_frame()
        if self.control_btns.playing_state != ControlButtons.PAUSE:
            self.after(FRAME_DELAY, self.playcycle)
        else:
            self.playing = False
