import gc
import tkinter as tk
import numpy as np

from vtl_common.localized_GUI.plotter import GridPlotter
from .storage import SingleStorage, Interval, IntervalStorage
from vtl_common.parameters import HALF_PIXELS
from vtl_common.common_flatfielding.models import FlatFieldingModel
from preprocessing.three_stage_preprocess import DataThreeStagePreProcessor
from .edges import split_intervals, edged_intervals


def prepare_data(interval:Interval, formdata, file_src):
    start = interval.start
    end = interval.end
    preprocessor: DataThreeStagePreProcessor
    preprocessor = formdata["preprocessing"]
    # print("SLICE", start, end)
    data, slicer = preprocessor.prepare_array(file_src["data0"], start, end, margin_add=256)
    return data, slicer, preprocessor

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

    def set_formdata(self, formdata, lazy=False):
        self._formdata = formdata
        if not lazy:
            self.on_strong_change()

    def drop(self):
        self.storage.drop()
        self.on_strong_change()


    def set_ffmodel(self, model):
        self._ffmodel = model
        self.set_broken(self._ffmodel.broken_query())

    def set_broken(self, broken):
        self.plotter.set_broken(broken)
        self.on_weak_change()

    def get_broken(self):
        return self.plotter.get_broken()

    def serialize(self):
        return  self.storage.serialize()

    def deserialize_inplace(self, obj):
        self.storage.deserialize_inplace(obj)
        self.on_strong_change()

    def on_strong_change(self):
        gc.collect()
        if self.storage.has_item() and self._formdata and self.controller.file:
            interval = self.storage.item
            data, slicer, preprocessor = prepare_data(interval, self._formdata, self.controller.file)
            # start = interval.start
            # end = interval.end
            # preprocessor: DataThreeStagePreProcessor
            # preprocessor = self._formdata["preprocessing"]
            # #print("SLICE", start, end)
            # data, slicer = preprocessor.prepare_array(self.controller.file["data0"], start, end, margin_add=256)

            self._data_cache = data
            self._slicer_cache = slicer
            self._interval = interval
        else:
            self._data_cache = None
            self._slicer_cache = None
            self._interval = None
        self._processed_data = None
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

    def get_plot_data(self):
        if self._processed_data is None:
            return None

        return self._interval.to_arange(), self._processed_data


    def get_tf_data(self, tf_model):
        if self.storage.has_item() and (self._formdata is not None) and self.controller.file:
            assert self.storage.item.is_same_as(self._interval)

            start = self._interval.start
            end = self._interval.end
            preprocessor = tf_model.get_filter()
            data, slicer = preprocessor.prepare_array(self.controller.file["data0"], start, end, margin_add=257)
            return data, slicer, preprocessor

    def trigger(self, tf_model, positive_storage, negative_storage):
        tf_data =  self.get_tf_data(tf_model)
        if tf_data:
            data, slicer, preprocessor = tf_data
            trigger = self._formdata["trigger"]
            threshold = trigger["threshold"]

            data = preprocessor.preprocess_whole(data, self.plotter.get_broken())
            triggered = tf_model.trigger(data,threshold)
            triggered = triggered[slicer]
            intervals = edged_intervals(triggered)
            pos, neg = split_intervals(np.array(intervals))
            source: IntervalStorage
            source = self._interval.to_istorage()
            base = self._interval.start
            for p in pos:
                item = Interval(base+p[0],base+p[1])
                assert source.try_move_to(positive_storage, item)
            for n in neg:
                item = Interval(base+n[0],base+n[1])
                assert source.try_move_to(negative_storage, item)
            assert source.is_empty()
            self.storage.take_external()

    def postprocess(self, tf_model, axes):
        tf_data = self.get_tf_data(tf_model)
        if tf_data:
            data, slicer, preprocessor = tf_data
            data = preprocessor.preprocess_whole(data, self.plotter.get_broken())
            start = self._interval.start
            end = self._interval.end
            tf_model.plot_over_data(data, start, end, axes, slicer)