from tkinter import Canvas
import tkinter as tk

#HELP:
#LMB press
#canvas.tag_bind(<TAG>, '<ButtonPress-1>', <FUNCTION(EVENT)>)

class Shape(object):
    def __init__(self, canvas):
        self.canvas: Canvas = canvas
        #canvas.bind("<Configure>", self.on_resize)
        #canvas.bind('<Motion>', self.on_hover)

    def on_resize(self, event):
        pass

    def on_hover(self, event):
        pass


class PaddedRect(Shape):
    def __init__(self, canvas, pixels_top, pixels_bottom, padx=5):
        super().__init__(canvas)
        self.main_element = self.canvas.create_rectangle(padx, pixels_top,
                                                         self.canvas.winfo_reqwidth() - padx,
                                                         self.canvas.winfo_reqheight() - pixels_bottom)
        self.padx = padx
        self.pixels_bottom = pixels_bottom
        self.pixels_top = pixels_top

    def on_resize(self, event):
        self.canvas.coords(self.main_element, self.padx, self.pixels_top,
                           event.width - self.padx,
                           event.height - self.pixels_bottom)


class Sliding(Shape):
    def __init__(self, canvas, pivot_height, main_element):
        super().__init__(canvas)
        self.pivot_height = pivot_height
        self.main_element = main_element
        self.canvas.tag_bind(self.main_element, '<ButtonPress-1>', self.on_click)
        self.grab = None
        self.on_move_callback = None
        x1 = self.canvas.coords(self.main_element)[0]
        self.mover(x1, self.pivot_height)


    def on_click(self, event):
        x1 = self.canvas.coords(self.main_element)[0]
        self.grab = x1-event.x

    def on_hover(self, event):
        if self.grab is not None:
            if event.state & 256:
                gx = self.grab
                self.mover(event.x+gx, self.pivot_height)
                self.check_constraint()
                if self.on_move_callback:
                    self.on_move_callback()
            else:
                self.grab = None
                self.check_constraint()


    def mover(self, x, y):
        self.canvas.moveto(self.main_element, int(x), y-1)

    def check_constraint(self):
        pass


class SlidingBox(Sliding):
    def __init__(self, canvas: Canvas, width, pixels_top, pixels_bottom, fill, padx=5):
        self.pixels_top = pixels_top
        self.pixels_bottom = pixels_bottom
        if width>0:
            self.box = canvas.create_rectangle(padx, pixels_top, width+padx,
                                               canvas.winfo_reqheight() - pixels_bottom,
                                               fill=fill)
        else:
            self.box = canvas.create_rectangle(width + padx, pixels_top, padx,
                                               canvas.winfo_reqheight() - pixels_bottom,
                                               fill=fill)
        self.padx = padx
        super().__init__(canvas, pixels_top, self.box)
        self.width = canvas.winfo_reqwidth()-2*padx


class IntervalSlider(SlidingBox):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def check_constraint(self):
        x1, y1, x2, y2 = self.canvas.coords(self.main_element)
        w = x2-x1
        if w > self.canvas.winfo_width()-2*self.padx:
            self.canvas.coords(self.main_element, self.padx, y1, self.canvas.winfo_width()-self.padx, y2)
        else:
            if x1<self.padx:
                self.mover(self.padx-1, self.pivot_height)
            if x2 > self.canvas.winfo_width()-self.padx:
                self.mover(self.canvas.winfo_width()-self.padx-w-1, self.pivot_height)

    def set_range(self, pos1, pos2):
        if (pos1 is not None) and (pos2 is not None) and pos1>pos2:
            pos1, pos2 = pos2, pos1
        x1, y1, x2, y2 = self.canvas.coords(self.main_element)
        if pos1 is None:
            pos1 = x1
        if pos2 is None:
            pos2 = x2
        self.canvas.coords(self.main_element, pos1, y1, pos2, y2)
        self.check_constraint()

    def get_range(self):
        x1, y1, x2, y2 = self.canvas.coords(self.main_element)
        return int(x1), int(x2)

    def grab_pos(self, x):
        x1, y1, x2, y2 = self.canvas.coords(self.main_element)
        w = x2 - x1
        if x<x1:
            self.mover(x, self.pivot_height)
        elif x>x2:
            self.mover(x-w, self.pivot_height)
        self.check_constraint()



class KnobSlider(SlidingBox):

    def __init__(self, canvas: Canvas, width, pixels_top, pixels_bottom, fill, padx=5):
        super().__init__(canvas, width, pixels_top, pixels_bottom, fill, padx)
        self.inverse = width<0

    def check_constraint(self):
        x1, y1, x2, y2 = self.canvas.coords(self.main_element)
        w = x2-x1
        if self.inverse:
            if x2 < self.padx:
                self.mover(self.padx - 1-w, self.pivot_height)
            if x2 > self.canvas.winfo_width() - self.padx:
                self.mover(self.canvas.winfo_width() - w - self.padx - 1, self.pivot_height)
        else:
            if x1<self.padx:
                 self.mover(self.padx-1, self.pivot_height)
            if x1 > self.canvas.winfo_width()-self.padx:
                 self.mover(self.canvas.winfo_width()-self.padx-1, self.pivot_height )

    def set_position(self, position):
        if self.inverse:
            x1, y1, x2, y2 = self.canvas.coords(self.main_element)
            w = x2 - x1
            self.mover(position-w, self.pivot_height)
        else:
            self.mover(position, self.pivot_height)
        self.check_constraint()

    def get_position(self):
        x1, y1, x2, y2 = self.canvas.coords(self.main_element)
        if self.inverse:
            return int(x2)
        else:
            return int(x1)

class PolySlider(Sliding):
    def __init__(self, canvas:Canvas, poly_conf, pivot_height, padx=5):
        poly, self.poly_pivot = poly_conf
        poly = canvas.create_polygon(*poly)
        super().__init__(canvas, pivot_height, poly)
        self.width = canvas.winfo_reqwidth()
        self.padx = padx
        
    def mover(self, x, y):
        dx = self.poly_pivot[0]
        super().mover(x-dx, y)

    def get_position(self):
        x1 = self.canvas.coords(self.main_element)[0]
        return int(x1)

    def set_position(self, x):
        self.mover(x-1, self.pivot_height)

    def check_constraint(self):
        pass
        # x1 = self.canvas.coords(self.main_element)[0]
        # if x1 < self.padx:
        #     self.canvas.moveto(self.padx, self.pivot_height-1)
        # if x1 > self.canvas.winfo_width()-self.padx:
        #     print("!!")
        #     self.canvas.moveto(self.canvas.winfo_width()-self.padx, self.pivot_height-1)


