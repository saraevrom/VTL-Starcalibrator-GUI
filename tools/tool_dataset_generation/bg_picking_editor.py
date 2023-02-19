from localized_GUI import Plotter
from preprocessing.denoising import moving_average_subtract
import numpy as np
from matplotlib.patches import Rectangle




class BgPickingEditor(Plotter):
    def __init__(self, master):
        super().__init__(master)
        self.draw_cache = []
        self.axes.set_axis_off()
        self.draw_y = None
        self.figure.tight_layout()
        self.toolbar.pack_forget()
        self.mpl_canvas.get_tk_widget().configure(height=200)
        self.pointer = self.axes.vlines(0, -1, 1, color="black")
        self.pointer_location = 0
        self.frame_pointer = self.axes.vlines(0, -1, 1, color="red")
        self.frame_pointer_location = 0
        self.axes.set_ylim(-1,1)
        self.figure.canvas.mpl_connect("motion_notify_event", self.on_motion)
        self.figure.canvas.mpl_connect('button_press_event', self.on_mouse_button_press)
        self.figure.canvas.mpl_connect('button_release_event', self.on_mouse_button_release)
        self.on_frame_lmb_event = None

        self._mark_placing_patch = None
        self._mark_placing_rectangle = None
        self._mark_start = 0

        self.marked_intervals = []

    def clear_placing_rectangle(self):
        if self._mark_placing_patch:
            self._mark_placing_patch.remove()
            self._mark_placing_patch = None
            self._mark_placing_rectangle = None

    def start_placement(self, x, silent=False):
        self._mark_start = x
        self.clear_placing_rectangle()
        self._mark_placing_rectangle = Rectangle((x, -1), 1, 2, color="gray", alpha=0.25)
        self._mark_placing_patch = self.axes.add_patch(self._mark_placing_rectangle)

    def end_placement(self, x):
        if self._mark_placing_patch:
            self.draw_cache.append(self._mark_placing_patch)
            self._mark_placing_patch = None
            self._mark_placing_rectangle = None
            if x > self._mark_start:
                self.marked_intervals.append([self._mark_start, x, 1.0])
            else:
                self.marked_intervals.append([x, self._mark_start, 1.0])

    def on_motion(self, event):
        if (event.xdata is not None):
            x = int(event.xdata)
            #if event.button == 1:
            self.set_pointer(x)
            if self._mark_placing_patch:
                self._mark_placing_rectangle.set_width(x-self._mark_start)
            self.figure.canvas.draw_idle()

    def on_mouse_button_press(self, event):
        if (event.xdata is not None):
            x = self.pointer_location
            if event.button == 1:
                self.set_frame_pointer(x)
                if self.on_frame_lmb_event:
                    self.on_frame_lmb_event(x)
            elif event.button == 3:
                self.start_placement(x)
                print("RMB press at", x)

    def on_mouse_button_release(self, event):
        if (event.xdata is not None):
            x = self.pointer_location
            if event.button == 3:
                self.end_placement(x)
                print("RMB release at", x)


    def set_pointer(self, new_x):
        seg_old = self.pointer.get_segments()
        ymin = seg_old[0][0, 1]
        ymax = seg_old[0][1, 1]

        seg_new = [np.array([[new_x, ymin],
                             [new_x, ymax]])]
        self.pointer.set_segments(seg_new)
        self.pointer_location = new_x

    def set_frame_pointer(self, new_x):
        seg_old = self.frame_pointer.get_segments()
        ymin = seg_old[0][0, 1]
        ymax = seg_old[0][1, 1]

        seg_new = [np.array([[new_x, ymin],
                             [new_x, ymax]])]
        self.frame_pointer.set_segments(seg_new)
        self.frame_pointer_location = new_x

    def clear(self):
        for x in self.draw_cache:
            x.remove()
        self.draw_cache.clear()
        self.axes.set_prop_cycle(None)

    def clear_intervals(self):
        self.marked_intervals.clear()

    def draw_data(self, settings):
        cutoff_start = settings["cutoff_start"]
        cutoff_end = settings["cutoff_end"]
        if cutoff_end is None:
            end = self.draw_y.shape[0]
        else:
            end = self.draw_y.shape[0]-cutoff_end
        if end < cutoff_start:
            cutoff_start, end = end, cutoff_start
        xs = np.arange(cutoff_start, end)
        ys = self.draw_y[cutoff_start:end]
        ys = ys/np.max(ys)
        fill = self.axes.fill_between(xs, -ys, ys)
        self.axes.set_xlim(cutoff_start, end-1)
        self.axes.set_ylim(-1,1)
        self.draw_cache.append(fill)

    def draw_intervals(self):
        for interval in self.marked_intervals:
            start, end, weight = interval
            mark_placing_rectangle = Rectangle((start, -1), end-start, 2, color="gray", alpha=0.25)
            self.draw_cache.append(self.axes.add_patch(mark_placing_rectangle))

    def redraw(self, settings):
        self.clear()
        self.draw_data(settings)
        self.draw_intervals()
        self.draw()

    def reload_data(self, file, settings, ff_model=None):
        ys = file["data0"]
        if ff_model:
            ys = ff_model.apply(np.array(ys))
        else:
            ys = np.array(ys)
        print(ys.shape)
        ys = moving_average_subtract(ys, settings["filter_window"])


        if ff_model:
            ys[:, ff_model.get_broken()] = 0


        draw_y = np.max(ys,axis=(1,2))
        #draw_y = draw_y/np.max(draw_y)
        self.draw_y = draw_y
        #draw_y = np.log(draw_y)

    def find_selected_interval(self):
        x = self.frame_pointer_location
        found = False
        interval_index = 0
        for i in range(len(self.marked_intervals) - 1, -1, -1):
            start, end, weight = self.marked_intervals[i]
            if start <= x <= end:
                found = True
                interval_index = i
                break
        if found:
            return True, interval_index
        else:
            return False, 0

    def delete_interval_on_frame_pointer(self):
        found,interval_index = self.find_selected_interval()
        if found:
            self.marked_intervals.pop(interval_index)

    def get_interval_weight_on_frame_pointer(self):
        found, interval_index = self.find_selected_interval()
        if found:
            return self.marked_intervals[interval_index][2]
        else:
            return 0

    def set_interval_weight_on_frame_pointer(self, target):
        found, interval_index = self.find_selected_interval()
        if found:
            self.marked_intervals[interval_index][2] = target

    def populate_intervals(self, found_events):
        self.marked_intervals = [[start, end, 1.0] for (start, end) in found_events]