import tkinter as tk
from .shapes import IntervalSlider, PaddedRect, KnobSlider, PolySlider


def top_slider_knob(width, height):
    return [
        width/2, height,
        0, height/2,
        0, 0,
        width, 0,
        width, height / 2,
    ], (width/2, height)

def bottom_slider_knob(width, height):
    return [
        width/2, 0,
        width, height/2,
        width, height,
        0, height,
        0, height/2
    ], (width/2, 0)

class DoubleSlider(tk.Canvas):
    def __init__(self, master, low_end, high_end, knob_size=10, knob_offset=5, upper_pixels=20, bottom_pixels=20):
        super().__init__(master, height=80)
        self.low_end = low_end
        self.high_end = high_end

        self.lower_value = low_end
        self.higher_value = high_end
        self.pointer_value = 0

        self.border = PaddedRect(self, pixels_top=upper_pixels, pixels_bottom=bottom_pixels, padx=knob_size)
        self.interval = IntervalSlider(self, width=self.winfo_reqwidth()*0.5-2*knob_size, pixels_top=upper_pixels,
                                       pixels_bottom=bottom_pixels, fill="#AAAAAA", padx=knob_size)

        self.left_knob = KnobSlider(self, width=-knob_size, pixels_top=upper_pixels+knob_offset,
                                  pixels_bottom=bottom_pixels+knob_offset, fill="#444444", padx=knob_size)

        self.right_knob = KnobSlider(self, width=knob_size, pixels_top=upper_pixels + knob_offset,
                                    pixels_bottom=bottom_pixels + knob_offset, fill="#444444", padx=knob_size)

        self.upper_knob = PolySlider(self, top_slider_knob(2 * knob_size, upper_pixels), 0)
        self.bottom_knob = PolySlider(self, bottom_slider_knob(2 * knob_size, upper_pixels),
                                      self.winfo_reqheight() - bottom_pixels)

        self.tracked_objects = [self.border, self.interval,
                                self.left_knob, self.right_knob, self.upper_knob, self.bottom_knob]
        self.bind('<Motion>', self.on_motion)
        self.bind("<Configure>", self.on_scale)

        self.left_knob.on_move_callback = self.on_lknob_move
        self.right_knob.on_move_callback = self.on_rknob_move
        self.interval.on_move_callback = self.on_interval_move
        self.upper_knob.on_move_callback = self.on_upper_move
        self.bottom_knob.on_move_callback = self.on_lower_move
        self.bottom_pixels = bottom_pixels
        self.knob_size = knob_size
        self.change_value_callback = None
        self._callback_enable = True
        self.after(10, self.consistency_sheck)


    def set_range(self, low, high):
        self.lower_value = low
        self.higher_value = high
        lpos, rpos = self.interval.get_range()
        pos = self.upper_knob.get_position()
        self.report_motion(lpos,rpos,pos)


    def on_motion(self, event):
        for obj in self.tracked_objects:
            obj.on_hover(event)

    def on_scale(self, event):
        self.bottom_knob.pivot_height = self.winfo_height() - self.bottom_pixels
        for obj in self.tracked_objects:
            obj.on_resize(event)
        self.consistency_sheck()

    def remap_to_conf_range(self, x):
        xcoord = x - self.knob_size
        xrange = self.winfo_width() - 2*self.knob_size
        return xcoord*(self.high_end-self.low_end)/xrange+self.low_end

    def remap_from_conf_range(self, x):
        xcoord = x - self.low_end
        xrange = self.high_end - self.low_end
        return xcoord*(self.winfo_width() - 2*self.knob_size)/xrange+self.knob_size


    def get_params(self):
        return self.lower_value, self.higher_value, self.pointer_value

    def set_params(self, low, high, pos):
        self.lower_value = low
        self.higher_value = high
        self.pointer_value = pos
        self.consistency_sheck()


    def consistency_sheck(self):
        lpos = self.remap_from_conf_range(self.lower_value)
        rpos = self.remap_from_conf_range(self.higher_value)
        pos = self.remap_from_conf_range(self.pointer_value)
        self.interval.set_range(lpos, rpos)
        self.left_knob.set_position(lpos)
        self.right_knob.set_position(rpos)
        self.upper_knob.set_position(pos)
        self.bottom_knob.set_position(pos)


    def report_motion(self,lpos,rpos,pos):
        self.lower_value = self.remap_to_conf_range(lpos)
        self.higher_value = self.remap_to_conf_range(rpos)
        self.pointer_value = self.remap_to_conf_range(pos)
        if self.change_value_callback and self._callback_enable:
            self.change_value_callback(*self.get_params())
        self._callback_enable = True

    def set_slider_callback(self, callback):
        self.change_value_callback = callback


    def clamp_main_knobs(self):
        lpos, rpos = self.interval.get_range()
        pos = self.upper_knob.get_position()
        if pos<lpos:
            self.upper_knob.set_position(lpos)
            pos = lpos
        if pos>rpos:
            self.upper_knob.set_position(rpos)
            pos = rpos
        self.bottom_knob.set_position(pos)
        self.report_motion(lpos,rpos,pos)


    def on_lknob_move(self):
        lpos = self.left_knob.get_position()
        rpos = self.right_knob.get_position()
        if rpos<lpos:
            self.right_knob.set_position(lpos)
            rpos = lpos
        self.interval.set_range(lpos, rpos)
        self.clamp_main_knobs()

    def on_rknob_move(self):
        lpos = self.left_knob.get_position()
        rpos = self.right_knob.get_position()
        if rpos<lpos:
            self.left_knob.set_position(rpos)
            lpos = rpos
        self.interval.set_range(lpos, rpos)
        pos = self.upper_knob.get_position()
        self.bottom_knob.set_position(pos)
        self.clamp_main_knobs()


    def on_interval_move(self):
        lpos, rpos = self.interval.get_range()
        self.left_knob.set_position(lpos-1)
        self.right_knob.set_position(rpos-1)
        self.clamp_main_knobs()

    def move_slider(self, target_position):
        self._callback_enable = False
        target_position = self.remap_from_conf_range(target_position)
        self.upper_knob.set_position(target_position)
        self.bottom_knob.set_position(target_position)
        self.interval.grab_pos(target_position)
        self.on_interval_move()

    def on_upper_move(self):
        pos = self.upper_knob.get_position()
        self.bottom_knob.set_position(pos)
        self.interval.grab_pos(pos)
        self.on_interval_move()


    def on_lower_move(self):
        pos = self.bottom_knob.get_position()
        self.upper_knob.set_position(pos)
        self.interval.grab_pos(pos)
        self.on_interval_move()
