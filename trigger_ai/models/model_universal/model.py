from ..common import apply_layer_array, deconvolve_windows
import tensorflow as tf
from ..model_wrapper import ModelWrapper
import numpy as np
from ..common import splat_select, plot_offset

OUT_SINGLE_SIGMA, OUT_SOFT, OUT_SPLIT = OUTPUT_TYPES = ["single_sigma", "binary_softmax", "splitted_sigma"]
S_SINGLE_SIGMA, S_SOFT, S_SPLIT = OUTPUT_SHAPES = [(1,), (2,), (4,)]

def create_tf_model(callable_array):
    inputs = tf.keras.Input(shape=(128, 16, 16))
    outputs = apply_layer_array(inputs, callable_array)
    return tf.keras.Model(inputs, outputs)

class UniversalModel(ModelWrapper):

    def get_mode(self):
        return self.additional_params["mode"]
    def create_dataset_ydata_for_item(self, y_data_parameters):
        mode = self.get_mode()
        if mode == OUT_SPLIT:
            ydata = np.array([0., 0., 0., 0.])
            if y_data_parameters.pmt_bottom_left:
                ydata[0] = 1.0
            if y_data_parameters.pmt_bottom_right:
                ydata[1] = 1.0
            if y_data_parameters.pmt_top_left:
                ydata[2] = 1.0
            if y_data_parameters.pmt_top_right:
                ydata[3] = 1.0
            return ydata
        elif mode == OUT_SOFT:
            if y_data_parameters.has_track():
                return np.array([0., 1.])
            else:
                return np.array([1., 0.])
        elif mode == OUT_SINGLE_SIGMA:
            if y_data_parameters.has_track():
                return np.array([1.])
            else:
                return np.array([0.])
        else:
            raise RuntimeError("Unknown mode")

    def trigger(self, x, threshold):
        mode = self.get_mode()
        y_data = self._predict_raw(x)
        if mode == OUT_SPLIT:
            #y_data = 1 - np.prod(1 - y_data, axis=1)
            deconvolved = []
            for i in range(4):
                deconvolved.append(deconvolve_windows(y_data[:, i], 128))
            y_data = np.max(np.vstack(deconvolved), axis=0)
        elif mode == OUT_SOFT:
            y_data = y_data[:, 1]
            y_data = deconvolve_windows(y_data, 128)
        elif mode == OUT_SINGLE_SIGMA:
            y_data = y_data[:, 0]
            y_data = deconvolve_windows(y_data, 128)
        else:
            raise RuntimeError("Unknown mode")

        # booled = y_data > threshold
        booled_full = y_data > threshold

        #print("R0", booled)
        #booled_full = splat_select(booled, 128)
        #return booled_full
        return self.expand_window(booled_full,128)
    
    def trigger_split(self, x, threshold):
        mode = self.get_mode()
        y_data = self._predict_raw(x)
        if mode == OUT_SPLIT:
            # y_data = 1 - np.prod(1 - y_data, axis=1)
            signals = []
            for i in range(4):
                deconv = deconvolve_windows(y_data[:, i], 128)
                booled_full = deconv > threshold
                #signal = booled_full
                signal = self.expand_window(booled_full,128)
                signals.append(signal)
            return signals
        else:
            return super().trigger_split(x, threshold)

    def plot_over_data(self, x, start, end, axes, cutter):
        mode = self.get_mode()
        y_data = self._predict_raw(x)
        #y_data = y_data[cutter]
        xs = np.arange(start, end)
        if mode == OUT_SPLIT:
            print("PLOT!")
            plot_offset(axes, xs, y_data[:, 0], 20, "bottom left", "-", cutter=cutter)
            plot_offset(axes, xs, y_data[:, 1], 22, "bottom right", "--", cutter=cutter)
            plot_offset(axes, xs, y_data[:, 2], 24, "top left", "-.", cutter=cutter)
            plot_offset(axes, xs, y_data[:, 3], 26, "top right", ":", cutter=cutter)
        else:
            if mode == OUT_SOFT:
                y_data = y_data[:, 1]
            elif mode == OUT_SINGLE_SIGMA:
                y_data = y_data[:, 0]
            else:
                raise RuntimeError("Unknown mode")
            plot_offset(axes, xs, y_data, 20, "ANN output", "-")
            #axes.plot(xs, y_data + 20, "-", color="black")

    def get_y_spec(self):
        mode = self.get_mode()
        if mode == OUT_SPLIT:
            return tf.TensorSpec(shape=(None, 4), dtype=tf.double)
        elif mode == OUT_SOFT:
            return tf.TensorSpec(shape=(None, 2), dtype=tf.double)
        elif mode == OUT_SINGLE_SIGMA:
            return tf.TensorSpec(shape=(None, 1), dtype=tf.double)

    def get_y_signature(self, n):
        mode = self.get_mode()
        if mode == OUT_SPLIT:
            return n, 4
        elif mode == OUT_SOFT:
            return n, 2
        elif mode == OUT_SINGLE_SIGMA:
            return n, 1