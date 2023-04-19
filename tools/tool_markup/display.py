import tkinter as tk
import numpy as np

from vtl_common.localized_GUI.plotter import GridPlotter
from .storage import SingleStorage
from vtl_common.parameters import HALF_PIXELS
from vtl_common.common_flatfielding.models import FlatFieldingModel
from preprocessing.three_stage_preprocess import DataThreeStagePreProcessor

class Display(tk.Frame):
    def __init__(self, master, controller=None):
        if controller is None:
            controller = master
        tk.Frame.__init__(self, master)
        #Storing.__init__(self)
        self.storage = SingleStorage()
        self.storage.on_take = self.on_strong_change
        self.storage.on_store = self.on_strong_change
        self.controller = controller
        self.plotter = GridPlotter(self)
        self.plotter.pack(fill="both", expand=True)
        self._formdata = None
        self._ffmodel = None
        self._processed_data = None
        self._data_cache = None
        self._slicer_cache = None
        self._interval = None

    def set_formdata(self, formdata):
        self._formdata = formdata
        self.on_weak_change()

    def drop(self):
        self.storage.drop()
        self.on_strong_change()


    def set_ffmodel(self, model):
        self._ffmodel = model
        self.set_broken(self._ffmodel.broken_query())

    def set_broken(self, broken):
        self.plotter.set_broken(broken)
        self.on_weak_change()

    def on_strong_change(self):
        if self.storage.has_item() and self._formdata and self.controller.file:
            interval = self.storage.item
            start = interval.start
            end = interval.end
            preprocessor: DataThreeStagePreProcessor
            preprocessor = self._formdata["preprocessing"]
            print("SLICE", start, end)
            data, slicer = preprocessor.prepare_array(self.controller.file["data0"], start, end, margin_add=256)
            self._data_cache = data
            self._slicer_cache = slicer
            self._interval = interval
        else:
            self._data_cache = None
            self._slicer_cache = None
            self._interval = None
        self.on_weak_change()


    def on_weak_change(self):
        if self._data_cache is not None and self._formdata is not None:
            data = self._data_cache
            slicer = self._slicer_cache
            preprocessor = self._formdata["preprocessing"]
            interval = self._interval
            self._ffmodel: FlatFieldingModel
            if self._ffmodel:
                data = self._ffmodel.apply(data)
            data = preprocessor.preprocess_whole(data, self.plotter.get_broken())
            data = data[slicer]
            self._processed_data = data
            plotting = np.max(data,axis=0)
            self.plotter.buffer_matrix = plotting
            self.plotter.axes.set_title(repr(interval))
        else:
            self.plotter.buffer_matrix = np.zeros([2*HALF_PIXELS, 2*HALF_PIXELS]).astype(float)
            self.plotter.axes.set_title("---")
        self.plotter.update_matrix_plot(True)
        self.plotter.draw()