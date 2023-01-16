from common_GUI import Plotter
from ..tool_track_markup.denoising import reduce_noise, antiflash, moving_average_subtract
import numpy as np




class BgPickingEditor(Plotter):
    def __init__(self, master):
        super().__init__(master)
        self.draw_cache = []
        self.axes.figure.set_size_inches(10, 2)
        self.axes.get_xaxis().set_visible(False)
        self.axes.get_yaxis().set_visible(False)
        self.draw_y = None
        self.figure.tight_layout()
        self.toolbar.pack_forget()
        self.mpl_canvas.get_tk_widget().configure(height=200)
        self.pointer = self.axes.vlines(0, -1, 1)
        self.pointer_location = 0

    def on_left_click(self, event):
        pass

    def set_pointer(self, new_x):
        self.pointer.set_xdata([new_x, new_x])
        self.pointer_location = new_x

    def clear(self):
        for x in self.draw_cache:
            x.remove()
        self.draw_cache.clear()
        self.axes.set_prop_cycle(None)

    def draw_data(self, settings):
        cutoff_start = settings["cutoff_start"]
        cutoff_end = settings["cutoff_end"]
        if cutoff_end is None:
            end = self.draw_y.shape[0]
        else:
            end = self.draw_y.shape[0]-cutoff_end
        xs = np.arange(cutoff_start, end)
        ys = self.draw_y[cutoff_start:end]
        ys = ys/np.max(ys)
        fill = self.axes.fill_between(xs, -ys, ys)
        self.axes.set_xlim(cutoff_start, end-1)
        self.draw_cache.append(fill)


    def redraw(self, settings):
        self.clear()
        self.draw_data(settings)
        self.draw()

    def reload_data(self, file, settings, ff_model=None):
        ys = file["data0"]
        if ff_model:
            ys = ff_model.apply(ys)
        else:
            ys = np.array(ys)
        print(ys.shape)
        ys = moving_average_subtract(ys, settings["filter_window"])


        if ff_model:
            ys[:, ff_model.get_broken()] = 0


        draw_y = np.max(ys,axis=(1,2))
        draw_y = draw_y/np.max(draw_y)
        self.draw_y = draw_y
        #draw_y = np.log(draw_y)

