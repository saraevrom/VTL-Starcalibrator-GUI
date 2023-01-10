import numpy as np
import json


class FlatFieldingModel(object):
    subclass_dict = None

    def __init__(self):
        self.broken_pixels = None

    def apply(self, pixel_data):
        raise NotImplementedError("How do I apply parameters?")

    def apply_single(self, pixel_data, i, j):
        raise NotImplementedError("How do I apply parameter?")

    def get_broken_auto(self):
        raise NotImplementedError("How do I detect broken pixels?")


    def set_broken(self, broken):
        self.broken_pixels = broken

    def get_broken(self):
        if self.broken_pixels is None:
            print("Generated auto")
            self.broken_pixels = self.get_broken_auto()
        return self.broken_pixels

    def broken_query(self):
        return np.array(np.where(self.get_broken())).T

    def is_broken(self, i, j):
        return self.get_broken()[i, j]

    def get_data(self):
        return dict()

    def set_data(self, x_data):
        pass

    def display_parameter_1(self):
        return "tool_flatfielder.nothing", None

    def display_parameter_2(self):
        return "tool_flatfielder.nothing", None

    def save(self, file_path):
        class_name = type(self).__name__
        save_data = {
            "model": class_name,
            "parameters": self.get_data()
        }
        with open(file_path, "w") as fp:
            json.dump(save_data, fp, indent=4, sort_keys=True)

    def apply_nobreak(self, pixel_data):
        pre_res = self.apply(pixel_data)
        broken = self.get_broken()
        pre_res[:, broken] = 0
        return pre_res

    def apply_single_nobreak(self, pixel_data, i, j):
        if self.is_broken(i, j):
            return np.zeros(pixel_data.shape[0])
        else:
            return self.apply_single(pixel_data, i, j)


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
    def __init__(self, coefficients=None, baseline=None):
        super().__init__()
        self.coefficients = coefficients
        self.baseline = baseline


    def get_broken_auto(self):
        return np.abs(self.coefficients) <= 1e-8

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
            "baseline": self.baseline.tolist(),
            "broken": self.broken_pixels.tolist()
        }

    def set_data(self, x_data):
        self.coefficients = np.array(x_data["coefficients"])
        self.baseline = np.array(x_data["baseline"])
        self.set_broken(np.array(x_data["broken"]))

    def display_parameter_1(self):
        return "tool_flatfielder.coefficients.title", self.coefficients

    def display_parameter_2(self):
        return "tool_flatfielder.baselevel.title", self.baseline


class NonlinearSaturation(FlatFieldingModel):
    def __init__(self, saturation=None, response=None, offset=None):
        super().__init__()
        self.saturation = saturation
        self.response = response
        self.offset = offset

    def get_data(self):
        return {
            "saturation": self.saturation.tolist(),
            "response": self.response.tolist(),
            "offset": self.offset.tolist(),
            "broken": self.broken_pixels.tolist()
        }

    def set_data(self, x_data):
        self.saturation = np.array(x_data["saturation"])
        self.response = np.array(x_data["response"])
        self.broken_pixels = np.array(x_data["broken"])
        self.offset = np.array(x_data["offset"])

    def display_parameter_1(self):
        return "tool_flatfielder.saturation.title", self.saturation

    def display_parameter_2(self):
        return "tool_flatfielder.response.title", self.response

    def apply(self, pixel_data):
        inv_A = 1/self.saturation
        inv_A[self.saturation == 0] = 0
        inv_B = self.saturation/self.response
        inv_B[self.response == 0] = 0
        inv_B[self.saturation == 0] = 0
        ret = self.offset-np.log(1-(pixel_data)*inv_A)*inv_B
        ret[(1-(pixel_data)*inv_A)<=0] = 0
        return ret

    def apply_single(self, single_data,i,j):
        A = self.saturation[i,j]
        B = self.response[i,j]/self.saturation[i,j]
        if A==0:
            inv_A = 0
        else:
            inv_A = 1/A
        if B == 0:
            inv_B = 0
        else:
            inv_B = B
        ret = -np.log(1-single_data*inv_A)*inv_B
        ret[(1-single_data*inv_A)<=0] = 0
        return ret

    def get_broken_auto(self):
        return np.logical_or(np.abs(self.saturation) <= 1e-8, np.abs(self.saturation/self.response)<=1e-8)

