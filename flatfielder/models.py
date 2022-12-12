import numpy as np
import json


class FlatFieldingModel(object):
    subclass_dict = None

    def apply(self, pixel_data):
        raise NotImplementedError("How do I apply parameters?")

    def apply_single(self, pixel_data, i, j):
        raise NotImplementedError("How do I apply parameter?")

    def get_broken(self):
        raise NotImplementedError("How do I detect broken pixels?")

    def broken_query(self):
        return np.array(np.where(self.get_broken())).T

    def is_broken(self, i, j):
        return self.get_broken()[i, j]

    def get_data(self):
        return dict()

    def set_data(self, x_data):
        pass

    def display_parameter_1(self):
        return "flatfielder.nothing", None

    def display_parameter_2(self):
        return "flatfielder.nothing", None

    def save(self, file_path):
        class_name = type(self).__name__
        save_data = {
            "model": class_name,
            "parameters": self.get_data()
        }
        with open(file_path, "w") as fp:
            json.dump(save_data, fp, indent=4, sort_keys=True)

    @staticmethod
    def load(file_path):
        if FlatFieldingModel.subclass_dict is None:
            FlatFieldingModel.subclass_dict = {cls.__name__: cls for cls in FlatFieldingModel.__subclasses__()}
        with open(file_path, "r") as fp:
            jsd = json.load(fp)
        model = FlatFieldingModel.subclass_dict[jsd["model"]]
        instance = model()
        instance.set_data(jsd["parameters"])
        return instance


class Linear(FlatFieldingModel):
    def __init__(self, coefficients=None, baseline = None):
        self.coefficients = coefficients
        self.baseline = baseline


    def get_broken(self):
        return self.coefficients == 0

    def apply(self, pixel_data):
        rev_coeffs = 1/self.coefficients
        rev_coeffs[self.coefficients==0] = 0
        ret_data = (pixel_data - self.baseline) * rev_coeffs
        return ret_data

    def apply_single(self, single_data, i, j):
        if self.coefficients[i, j] == 0:
            rev_coeff = 0
        else:
            rev_coeff = 1 / self.coefficients[i, j]
        ret_data = (single_data - self.baseline[i, j]) * rev_coeff
        return ret_data

    def get_data(self):
        return {
            "coefficients": self.coefficients.tolist(),
            "baseline": self.baseline.tolist()
        }

    def set_data(self, x_data):
        self.coefficients = np.array(x_data["coefficients"])
        self.baseline = np.array(x_data["baseline"])

    def display_parameter_1(self):
        return "flatfielder.coefficients.title", self.coefficients

    def display_parameter_2(self):
        return "flatfielder.baselevel.title", self.baseline
