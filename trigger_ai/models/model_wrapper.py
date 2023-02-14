import h5py
import numpy as np
from tensorflow import keras
import tensorflow as tf
import json

CUSTOM_FIELD = "CUSTOM_MODEL_WRAPPER"
FILTER_FIELD = "CUSTOM_PREFERRED_FILTER"

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
    MODEL_FORM = None  # Set it to class correspondong to form creation

    def __init__(self, model: keras.Model, preferred_filter_data=None):
        self.model = model
        self.preferred_filter_data = preferred_filter_data

    def set_preferred_filter_data(self, data):
        self.preferred_filter_data = data

    def save_model(self, file_path, attach_filter=None):
        self.model.save(file_path)
        with h5py.File(file_path, "a") as fp:
            fp.attrs[CUSTOM_FIELD] = type(self).__name__.encode("utf-8")
            if attach_filter is not None:
                fp.attrs[FILTER_FIELD] = json.dumps(attach_filter).encode("utf-8")
            elif self.preferred_filter_data is not None:
                fp.attrs[FILTER_FIELD] = json.dumps(self.preferred_filter_data).encode("utf-8")


    @staticmethod
    def load_model(file_path):
        if ModelWrapper.SUBCLASSES is None:
            ModelWrapper.SUBCLASSES = {cls.__name__: cls for cls in ModelWrapper.__subclasses__()}
        with h5py.File(file_path, "r") as fp:
            print(fp.keys())
            instance_class = ModelWrapper.SUBCLASSES[fp.attrs[CUSTOM_FIELD]]
            filter_data = None
            if FILTER_FIELD in fp.attrs.keys():
                filter_data = json.loads(fp.attrs[FILTER_FIELD])

        model = keras.models.load_model(file_path)
        return instance_class(model, filter_data)

    def create_dataset_ydata_for_item(self, y_data_parameters: TargetParameters):
        raise NotImplementedError()

    def trigger(self, x, threshold):
        raise NotImplementedError()

    def plot_over_data(self, x, start, end, axes):
        raise NotImplementedError()

    def get_y_spec(self):
        raise NotImplementedError()

    def get_y_signature(self, n):
        raise NotImplementedError()