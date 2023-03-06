import numpy.random as rng
import numpy as np
from ..plotter import Plotter

from utilities import set_vlines_position, set_vlines_position_ylims

from parameters import SCALE_FLOATING_POINT_FORMAT
import numba as nb


@nb.njit()
def hsv_to_rgb(h,s,v):
    '''
    0<=h<=360
    0<=s<=1
    0<=v<=1
    '''
    h = h % 360
    c = v*s
    x = c*(1-abs((h/60)%2-1))
    m = v-c
    if h<60:
        _r = c
        _g = x
        _b = 0
    elif h<120:
        _r = x
        _g = c
        _b = 0
    elif h<180:
        _r = 0
        _g = c
        _b = x
    elif h<240:
        _r = 0
        _g = x
        _b = c
    elif h<300:
        _r = x
        _g = 0
        _b = c
    else:
        _r = c
        _g = 0
        _b = x
    return _r+m, _g+m, _b+m



def generate_color_part(generator,l,h):
    return generator.random()*(h-l)+l

def generate_color(generator):
    h = generate_color_part(generator,0.0,360.0)
    s = generate_color_part(generator,0.8,1.0)
    v = generate_color_part(generator,0.5,1.0)
    #roundval = generator.random()*2*np.pi
    # r = (np.cos(roundval)+1)/2
    # g = (np.cos(roundval+2*np.pi/3)+1)/2
    # b = (np.cos(roundval+4*np.pi/3)+1)/2
    return hsv_to_rgb(h,s,v)

LEGEND_PARAMS = dict(loc='upper left', bbox_to_anchor=(1.05, 1),
              ncol=2, borderaxespad=0)

class MainPlotter(Plotter):
    def __init__(self, master, x_plot, display_data):
        super().__init__(master)
        gen = rng.default_rng(42)
        self.lines = []
        for i in range(16):
            line_row = []
            for j in range(16):
                line, = self.axes.plot(x_plot, display_data[:,i,j], c=generate_color(gen), label="_hidden")
                line.set_visible(False)
                line_row.append(line)
            self.lines.append(line_row)
        self.display_data = display_data
        self.use_mean = False
        self.accumulated, = self.axes.plot(x_plot, np.zeros(shape=display_data.shape[0]), "-",
                                           color="black", label="_hidden")
        self.accumulated.set_visible(False)
        box = self.axes.get_position()
        self.axes.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        self.axes.legend(loc='upper left', bbox_to_anchor=(1.05, 1),
              ncol=2, borderaxespad=0)
        self.draw()
        self._accumulation_mode = "Off"
        self.display_matrix = np.full(fill_value=False, shape=(16,16))
        self.figure.canvas.mpl_connect('button_press_event', self.on_button_press_event)
        self.figure.canvas.mpl_connect('motion_notify_event', self.on_hover_event)
        self.figure.canvas.mpl_connect('figure_leave_event', self.on_mouse_leave)
        self.__right_hold = False
        self.__start_x = 0
        self.__end_x = 0
        lowx = np.min(x_plot)
        lowy = np.min(display_data)
        highy =np.max(display_data)
        self.__start_line = self.axes.vlines(lowx, lowy, highy, colors=["black"])
        self.__start_line.set_visible(False)
        self.__end_line = self.axes.vlines(lowx, lowy, highy, colors=["black"])
        self.__end_line.set_visible(False)
        self.__arrow = self.axes.arrow(lowx,lowy,0,0)
        self.__arrow.set_visible(False)
        self.__display_dt_annotation = self.axes.annotate("0", (0,0), xytext=(10,10),
                                                          xycoords="figure pixels",textcoords="offset pixels")

    def set_visibility(self, matrix):
        for i in range(16):
            for j in range(16):
                self.lines[i][j].set_visible(matrix[i,j])
                if matrix[i,j]:
                    self.lines[i][j].set_label(f"[{i + 1}, {j + 1}]")
                else:
                    self.lines[i][j].set_label("_hidden")
        self.axes.legend(**LEGEND_PARAMS)
        self.display_matrix = matrix
        self.draw()

    def set_accumulation_visibility(self, visible):
        self.accumulated.set_visible(visible)
        if visible:
            self.accumulated.set_label("Σ")
        else:
            self.accumulated.set_label("_hidden")
        self.draw()

    def on_button_press_event(self, event):
        if event.button == 3 and (event.xdata is not None) and self.allow_callbacks():
            self.__right_hold = True
            print("START")
            self.__start_x = event.xdata
            ymin, ymax = self.axes.get_ylim()
            set_vlines_position_ylims(self.__start_line, self.__start_x, ymin, ymax)
            self.axes.set_autoscaley_on(False)

            self.__show_field(self.__start_line)
            self.__show_field(self.__end_line)
            self.__show_field(self.__arrow)
            self.__show_field(self.__display_dt_annotation)
            self.track_position(event)
        if not self.allow_callbacks() or event.button == 1:
            self.__hide_field(self.__start_line)
            self.__hide_field(self.__end_line)
            self.__hide_field(self.__arrow)
            self.__hide_field(self.__display_dt_annotation)



    def on_hover_event(self, event):
        if event.button == 3 and self.__right_hold:
            self.track_position(event)
        else:
            self.stop_measuring()

    def on_mouse_leave(self, event):
        self.stop_measuring()


    def __hide_field(self, field):
        # if not hasattr(self, field_name):
        #     setattr(self, field_name, None)
        field.set_visible(False)

    def __show_field(self, field):
        # if not hasattr(self, field_name):
        #     setattr(self, field_name, None)
        field.set_visible(True)

    def stop_measuring(self):
        self.__right_hold = False

        self.axes.set_autoscaley_on(True)
        self.draw()


    def track_position(self,event):
        if (event.xdata is not None):
            self.__end_x = event.xdata
            ymin, ymax = self.axes.get_ylim()
            middle_y = (ymin+ymax)/2
            set_vlines_position_ylims(self.__end_line, self.__end_x, ymin, ymax)

            self.__arrow.set_data(x=self.__start_x,
                                               y=middle_y,
                                               dx=(self.__end_x - self.__start_x),
                                               dy=0)

            dx = abs(self.__start_x - self.__end_x)
            middle_x = (self.__start_x + self.__end_x)/2
            #self.__display_dt_annotation.set_position((middle_x, middle_y))
            self.__display_dt_annotation.set_text(SCALE_FLOATING_POINT_FORMAT.format(dx))

        self.draw()


    def update_accumulation_selected(self, checkmode=None):
        if checkmode is None:
            checkmode = self._accumulation_mode
        if checkmode =="Selected":
            srcdata = self.display_data[:, self.display_matrix]
            func = self.get_lightcurve_func()
            self.accumulated.set_ydata(func(srcdata, axis=1))
        self.draw()

    def get_lightcurve_func(self):
        if self.use_mean:
            return np.mean
        else:
            return np.sum

    def switch_accumulation_mode(self, new_mode):
        if self._accumulation_mode != new_mode:
            self.set_accumulation_visibility(new_mode != "Off")
            if new_mode == "All":
                func = self.get_lightcurve_func()
                full_sum = func(self.display_data, axis=(1, 2))
                self.accumulated.set_ydata(full_sum)
            self.update_accumulation_selected(new_mode)
        self._accumulation_mode = new_mode
