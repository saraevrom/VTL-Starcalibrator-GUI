import h5py
from tensorflow import keras
import tensorflow as tf

CUSTOM_FIELD = "CUSTOM_MODEL_WRAPPER"

class TargetParameters(object):
    def __init__(self, pmt_bottom_left, pmt_bottom_right, pmt_top_left, pmt_top_right):
        self.pmt_bottom_left = pmt_bottom_left
        self.pmt_bottom_right = pmt_bottom_right
        self.pmt_top_left = pmt_top_left
        self.pmt_top_right = pmt_top_right

    def has_track(self):
        return self.pmt_top_right or self.pmt_bottom_right \
                or self.pmt_top_left or self.pmt_bottom_left

class ModelWrapper(object):
    SUBCLASSES = None
    MODEL_FORM = None  # Set it to class correspondong to form creation

    def __init__(self, model: keras.Model):
        self.model = model

    def save_model(self, file_path):
        self.model.save(file_path)
        with h5py.File(file_path, "a") as fp:
            fp.attrs[CUSTOM_FIELD] = type(self).__name__.encode("utf-8")


    @staticmethod
    def load_model(file_path):
        if ModelWrapper.SUBCLASSES is None:
            ModelWrapper.SUBCLASSES = {cls.__name__: cls for cls in ModelWrapper.__subclasses__()}
        with h5py.File(file_path, "r") as fp:
            print(fp.keys())
            instance_class = ModelWrapper.SUBCLASSES[fp.attrs[CUSTOM_FIELD]]

        model = keras.models.load_model(file_path)
        return instance_class(model)

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