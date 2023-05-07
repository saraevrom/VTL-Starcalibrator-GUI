import h5py
import numpy as np
from tensorflow import keras
import tensorflow as tf
import json
from preprocessing.forms import DataPreProcessorField
from numpy.lib.stride_tricks import sliding_window_view
from ..compiler_form import CompileForm
from .common import  expand_window, deconvolve_windows_mean

CUSTOM_FIELD = "CUSTOM_MODEL_WRAPPER"
FILTER_FIELD = "CUSTOM_PREFERRED_FILTER"
COMPILE_PARAMS_FIELD = "CUSTOM_MODEL_COMPILE_PARAMS"
ATTRS_FIELD = "MOD_ATTRS"


class TargetParameters(object):
    def __init__(self):
        self.pmt_bottom_left = False
        self.pmt_bottom_right = False
        self.pmt_top_left = False
        self.pmt_top_right = False
        self.interference_bottom_left = False
        self.interference_bottom_right = False
        self.interference_top_left = False
        self.interference_top_right = False


    def has_track(self):
        return self.pmt_top_right or self.pmt_bottom_right \
                or self.pmt_top_left or self.pmt_bottom_left

    def create_mask(self):
        mask = np.full(False, (16,16))
        if self.pmt_bottom_left or self.interference_bottom_left:
            mask[:8, :8] = True
        if self.pmt_bottom_right or self.interference_bottom_right:
            mask[8:, :8] = True
        if self.pmt_top_left or self.interference_top_left:
            mask[:8, 8:] = True
        if self.pmt_top_right or self.interference_top_right:
            mask[8:, 8:] = True
        return mask

class ModelWrapper(object):
    SUBCLASSES = None
    MODEL_FORM = None  # Set it to class corresponding to form creation

    def __init__(self, model: keras.Model, preferred_filter_data=None, additional_params=None):
        self.model = model
        self.preferred_filter_data = preferred_filter_data
        self.additional_params = additional_params
        self.stabilize_slide = True
        self._compile_params = None
        self._expand_window = False
        self._deconvolver = None

    def require_bg(self):
        return False


    def set_window_expansion(self, v):
        self._expand_window = v

    def set_window_deconv(self,v):
        self._deconvolver = v

    def expand_window(self, booled_full, window):
        if self._expand_window:
            return expand_window(booled_full, window)
        else:
            return booled_full

    def deconvolve_windows(self,y_data,win):
        if self._deconvolver is None:
            self._deconvolver = deconvolve_windows_mean
        return self._deconvolver(y_data,win)

    def set_preferred_filter_data(self, data):
        self.preferred_filter_data = data

    def set_compile_parameters(self,data):
        self._compile_params = data

    def has_compile_parameters(self):
        return self._compile_params is not None

    def get_filter(self):
        processor = DataPreProcessorField()
        processor.parse_formdata(self.preferred_filter_data)
        return processor.get_data()

    def save_model(self, file_path, compile_parameters=None, attach_filter=None):
        self.model.save(file_path)
        with h5py.File(file_path, "a") as fp:
            fp.attrs[CUSTOM_FIELD] = type(self).__name__.encode("utf-8")
            if self.additional_params is not None:
                fp.attrs[ATTRS_FIELD] = json.dumps(self.additional_params)

            if attach_filter is not None:
                fp.attrs[FILTER_FIELD] = json.dumps(attach_filter).encode("utf-8")
            elif self.preferred_filter_data is not None:
                fp.attrs[FILTER_FIELD] = json.dumps(self.preferred_filter_data).encode("utf-8")

            if compile_parameters is None:
                fp.attrs[COMPILE_PARAMS_FIELD] = json.dumps(self._compile_params)
            else:
                fp.attrs[COMPILE_PARAMS_FIELD] = json.dumps(compile_parameters)


    @staticmethod
    def load_model(file_path):
        if ModelWrapper.SUBCLASSES is None:
            ModelWrapper.SUBCLASSES = {cls.__name__: cls for cls in ModelWrapper.__subclasses__()}
        compile_params = None
        add_data = None
        filter_data = None
        with h5py.File(file_path, "r") as fp:
            print(fp.keys())
            instance_class = ModelWrapper.SUBCLASSES[fp.attrs[CUSTOM_FIELD]]
            if FILTER_FIELD in fp.attrs.keys():
                filter_data = json.loads(fp.attrs[FILTER_FIELD])
            if ATTRS_FIELD in fp.attrs.keys():
                add_data = json.loads(fp.attrs[ATTRS_FIELD])
            if COMPILE_PARAMS_FIELD in fp.attrs.keys():
                compile_params = json.loads(fp.attrs[COMPILE_PARAMS_FIELD])

        if compile_params is None:
            model = keras.models.load_model(file_path)
        else:
            model = keras.models.load_model(file_path, compile=False)
            compiler = CompileForm()
            compiler.parse_formdata(compile_params)
            compile_params_1 = compiler.get_data()
            model.compile(**compile_params_1)
            print("Model compile workaround")
        instance = instance_class(model, filter_data, add_data)
        instance._compile_params = compile_params
        return instance

    def create_dataset_ydata_for_item(self, y_data_parameters: TargetParameters):
        raise NotImplementedError()

    def trigger(self, x, threshold):
        raise NotImplementedError()

    def trigger_split(self, x, threshold):
        arr = self.trigger(x, threshold)
        return arr, arr, arr, arr

    def plot_over_data(self, x, start, end, axes, cutter):
        raise NotImplementedError()

    def get_y_spec(self):
        raise NotImplementedError()

    def get_y_signature(self, n):
        raise NotImplementedError()

    def _predict_raw(self, x):
        x_data = sliding_window_view(x, 128, axis=0)
        if len(x.shape) == 3:
            x_data = np.moveaxis(x_data, [1, 2, 3], [2, 3, 1])
        else:
            x_data = np.moveaxis(x_data, [1, 2, 3, 4], [2, 3, 4, 1])
        y_data = self.model.predict(x_data)
        return y_data