import numpy as np
import json

from scipy.special import lambertw

class FlatFieldingModel(object):
    subclass_dict = None

    def __init__(self):
        self.broken_pixels = None

    def __str__(self):
        return type(self).__name__

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

    def reset_broken(self):
        self.broken_pixels = None

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
        save_data = self.dump()
        with open(file_path, "w") as fp:
            json.dump(save_data, fp, indent=4, sort_keys=True)

    def dump(self):
        class_name = type(self).__name__
        save_data = {
            "model": class_name,
            "parameters": self.get_data()
        }
        return save_data

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
        with open(file_path, "r") as fp:
            jsd = json.load(fp)
        instance = FlatFieldingModel.create_from_parameters(jsd)
        return instance

    @staticmethod
    def create_from_parameters(parameters):
        if FlatFieldingModel.subclass_dict is None:
            FlatFieldingModel.subclass_dict = {cls.__name__: cls for cls in FlatFieldingModel.__subclasses__()}
        model = FlatFieldingModel.subclass_dict[parameters["model"]]
        instance = model()
        instance.set_data(parameters["parameters"])
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
        self.get_broken()
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
        return "flatfielder.coefficients.title", self.coefficients

    def display_parameter_2(self):
        return "flatfielder.baselevel.title", self.baseline


class NonlinearSaturation(FlatFieldingModel):
    def __init__(self, saturation=None, response=None, offset=None):
        super().__init__()
        self.saturation = saturation
        self.response = response
        self.offset = offset

    def get_data(self):
        self.get_broken()
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
        return "flatfielder.saturation.title", self.saturation

    def display_parameter_2(self):
        return "flatfielder.response.title", self.response

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


class NonlinearPileup(FlatFieldingModel):
    def __init__(self, sensitivity=None, divider=None, prescaler=None):
        super().__init__()
        self.sensitivity = sensitivity
        self.divider = divider
        self.prescaler = prescaler

    def get_data(self):
        self.get_broken()
        return {
            "sensitivity": self.sensitivity.tolist(),
            "divider": self.divider.tolist(),
            "prescaler": self.prescaler,
            "broken": self.broken_pixels.tolist()
        }

    def set_data(self, x_data):
        self.sensitivity = np.array(x_data["sensitivity"])
        self.divider = np.array(x_data["divider"])
        self.broken_pixels = np.array(x_data["broken"])
        self.prescaler = x_data["prescaler"]

    def display_parameter_1(self):
        return "flatfielder.sensitivity.title", self.sensitivity

    def display_parameter_2(self):
        return "flatfielder.divider.title", self.divider

    def apply(self, pixel_data_in):
        pixel_data = pixel_data_in*self.prescaler
        upper_clamp = self.divider / np.e
        pixels_clip = np.clip(pixel_data, a_min=0, a_max=upper_clamp)
        pre = -self.divider / self.sensitivity * lambertw(-pixels_clip / self.divider).real
        pre = np.nan_to_num(pre)
        return pre

    def apply_single(self, single_data_in, i, j):
        single_data = single_data_in*self.prescaler
        divider = self.divider[i, j]
        sens = self.sensitivity[i, j]
        upper_clamp = divider / np.e
        clip = np.clip(single_data, a_min=0, a_max=upper_clamp)
        pre = -divider / sens * lambertw(-clip / divider, 0).real
        pre = np.nan_to_num(pre)
        return pre

    def get_broken_auto(self):
        return self.sensitivity <= 0


class Chain(FlatFieldingModel):
    def __init__(self, models=None):
        super().__init__()
        if models:
            self.models = models
        else:
            self.models = []

    def __str__(self):
        superstr = super().__str__()
        arr = ", ".join([item.__str__() for item in self.models])
        return f"{superstr}[{arr}]"

    def append_model(self, model):
        print("APPENDED", model)
        self.models.append(model)

    def amend_model(self, model):
        '''
        Edit last model if present
        :return:
        '''
        if self.models:
            self.models[-1] = model

    def get_data(self):
        self.get_broken()
        return {
            "models": [item.dump() for item in self.models],
            "broken": self.broken_pixels.tolist()
        }

    def set_data(self, x_data):
        self.models = [self.create_from_parameters(item) for item in x_data["models"]]
        self.broken_pixels = np.array(x_data["broken"])

    def apply(self, pixel_data):
        if self.models:
            workon = self.models[0].apply(pixel_data)
            for model in self.models[1:]:
                workon = model.apply(workon)
            return workon
        return pixel_data

    def apply_amending(self, pixel_data):
        if self.models:
            workon = self.models[0].apply(pixel_data)
            for model in self.models[1:-1]:
                workon = model.apply(workon)
            return workon
        return pixel_data

    def apply_single(self, pixel_data, i, j):
        if self.models:
            workon = self.models[0].apply_single(pixel_data, i, j)
            for model in self.models[1:]:
                workon = model.apply_single(workon, i, j)
            return workon
        return pixel_data

    def get_broken_auto(self):
        workon = np.full((16, 16), False)
        if self.models:
            for model in self.models:
                workon = model.get_broken_auto()
        return workon

    def display_parameter_1(self):
        if self.models:
            return self.models[-1].display_parameter_1()
        else:
            return super().display_parameter_1()

    def display_parameter_2(self):
        if self.models:
            return self.models[-1].display_parameter_2()
        else:
            return super().display_parameter_2()