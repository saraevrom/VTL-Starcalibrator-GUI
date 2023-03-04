import tkinter as tk
from ..plotter import Plotter, GridPlotter
import numpy.random as rng
import numpy as np
from common_GUI.settings_frame import SettingMenu
from .build_settings import build_menu
from localization import get_locale


def generate_color_part(generator):
    return (generator.random()+0.1)/1.15

def generate_color(generator):
    r = generate_color_part(generator)
    g = generate_color_part(generator)
    b = generate_color_part(generator)
    #roundval = generator.random()*2*np.pi
    # r = (np.cos(roundval)+1)/2
    # g = (np.cos(roundval+2*np.pi/3)+1)/2
    # b = (np.cos(roundval+4*np.pi/3)+1)/2
    return r,g,b

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
        self.accumulated, = self.axes.plot(x_plot, np.zeros(shape=display_data.shape[0]), "--",
                                           color="#BBBBBB", label="_hidden")
        self.accumulated.set_visible(False)
        box = self.axes.get_position()
        self.axes.set_position([box.x0, box.y0, box.width * 0.8, box.height])
        self.axes.legend(loc='upper left', bbox_to_anchor=(1.05, 1),
              ncol=2, borderaxespad=0)
        self.draw()
        self._accumulation_mode = "Off"
        self.display_matrix = np.full(fill_value=False, shape=(16,16))

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


class ChoosablePlotter(tk.Toplevel):
    def __init__(self, master, x_plot, display_data):
        super().__init__(master)
        self.display_data = display_data
        self._close_callback_cp = None
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.plotter = MainPlotter(self, x_plot, display_data)
        self.plotter.pack(side="left", fill="both", expand=True)

        auxpanel = tk.Frame(self)
        auxpanel.pack(side="right", fill="y")
        self.selector = GridPlotter(auxpanel, enable_scale_configuration=False)
        self.selector.alive_pixels_matrix = np.full(fill_value=False, shape=(16, 16))
        self.selector.update_matrix_plot()
        self.selector.pack(side="top", anchor="ne",fill="x")
        self.selector.on_left_click_callback = self.on_lmb
        self.selector.draw()
        self.selector.toolbar.pack_forget()
        self.selector.on_right_click_callback_outofbounds = self.on_right_click_callback_oob_inside

        self.settings_menu = SettingMenu(auxpanel, autocommit=True)
        self.settings_menu.commit_action = self.on_settings_commit
        build_menu(self.settings_menu)
        self.settings_menu.pack(side="bottom",fill="x")
        self.settings_dict = dict()

        quickactive_btn = tk.Button(auxpanel, text=get_locale("app.popup_plot.detect_active"),
                                    command=self.on_active_select)
        quickactive_btn.pack(side="bottom", fill="x")

    def get_axes(self):
        return self.plotter.axes

    def on_settings_commit(self):
        self.settings_menu.push_settings_dict(self.settings_dict)
        self.plotter.switch_accumulation_mode(self.settings_dict["lightcurve"])
        self.plotter.use_mean = self.settings_dict["lightcurve_mean"]
        self.plotter.draw()

    def on_active_select(self):
        dst_matrix = self.selector.alive_pixels_matrix[:]
        amplitudes = np.max(self.display_data, axis=0)
        src_matrix = amplitudes > self.settings_dict["threshold"]
        dst_matrix = np.logical_or(src_matrix, dst_matrix)
        self.selector.alive_pixels_matrix = dst_matrix
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(-1, -1)

    def on_lmb(self,i,j):
        self.plotter.set_visibility(self.selector.alive_pixels_matrix)
        self.plotter.update_accumulation_selected()

    def on_right_click_callback(self,i,j):
        self.selector.alive_pixels_matrix[i,j] = True
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(i,j)

    def on_right_click_callback_oob(self):
        self.selector.alive_pixels_matrix = np.full(shape=(16, 16), fill_value=True)
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(-1, -1)

    def on_right_click_callback_oob_inside(self):
        '''
        QOL improvement: clicking inside grid will reset selection.
        :return:
        '''
        if not self.selector.alive_pixels_matrix.any():
            self.selector.alive_pixels_matrix = np.full(shape=(16, 16), fill_value=True)
        else:
            self.selector.alive_pixels_matrix = np.full(shape=(16, 16), fill_value=False)
        self.selector.update_matrix_plot()
        self.selector.draw()
        self.on_lmb(-1, -1)

    def connect_close(self, callback):
        self._close_callback_cp = callback

    def on_closing(self):
        if self._close_callback_cp is not None:
            self._close_callback_cp()
        self.destroy()


class PopupPlotable(tk.Misc):
    def __init__(self, grid_plotter:GridPlotter):
        self._active_gridplotter = grid_plotter
        self._plotter_window = None
        self._active_gridplotter.on_right_click_callback = self.on_right_click_callback
        self._active_gridplotter.on_right_click_callback_outofbounds = self.on_right_click_callback_oob

    def get_plot_data(self):
        raise NotImplementedError("Unable to obtain plot data")

    def postprocess_plot(self, axes):
        pass

    def on_left_click(self, i, j):
        if self.ensure_plotter():
            self._plotter_window.on_lmb(i, j)

    def on_right_click_callback(self,i,j):
        if self.ensure_plotter():
            self._plotter_window.on_right_click_callback(i,j)

    def on_right_click_callback_oob(self):
        if self.ensure_plotter():
            self._plotter_window.on_right_click_callback_oob()

    def ensure_plotter(self):
        if self._plotter_window is None:
            self.create_plotter()
        return self._plotter_window is not None

    def _on_popup_close(self):
        self._plotter_window = None

    def create_plotter(self):
        draw_data = self.get_plot_data()
        if draw_data is not None:
            x_data, display_data = draw_data
            self._plotter_window = ChoosablePlotter(self, x_data, display_data)
            self.postprocess_plot(self._plotter_window.get_axes())
            self._plotter_window.connect_close(self._on_popup_close)
