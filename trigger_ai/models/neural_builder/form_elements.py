from vtl_common.common_GUI.tk_forms_assist import *
from vtl_common.common_GUI.tk_forms_assist.factory import create_value_field, kwarg_builder
from vtl_common.localization import get_locale
from tensorflow import keras
import tensorflow as tf
from .custom_structures import Residual, TrainableScaling, PMTSplit, Conv2DPlus1


class Activation(ComboNode):
    DISPLAY_NAME = get_locale("app.model_builder.activation")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "linear"
    VALUES = list(sorted(["linear", "relu", "sigmoid", "softplus", "softsign", "tanh", "selu", "elu"]))


@kwarg_builder(keras.layers.Dense)
class DenseConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.dense")
    FIELD__units = create_value_field(IntNode, get_locale("app.model_builder.dense.count"), 1)
    FIELD__activation = Activation



class NNPadding(ComboNode):
    DISPLAY_NAME = get_locale("app.model_builder.padding")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "valid"
    VALUES = ["valid", "same"]

class Conv3DLikeConstructor(FormNode):
    FIELD__conv_outputs = create_value_field(IntNode, get_locale("app.model_builder.convnd.outputs"), 1)
    FIELD__conv_X = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_X"), 3)
    FIELD__conv_Y = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_Y"), 3)
    FIELD__conv_T = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_T"), 8)
    FIELD__stride_X = create_value_field(IntNode, get_locale("app.model_builder.stride_X"), 1)
    FIELD__stride_Y = create_value_field(IntNode, get_locale("app.model_builder.stride_Y"), 1)
    FIELD__stride_T = create_value_field(IntNode, get_locale("app.model_builder.stride_T"), 1)
    FIELD__padding = NNPadding
    FIELD__activation = Activation


class Conv3DConstructor(Conv3DLikeConstructor):
    DISPLAY_NAME = get_locale("app.model_builder.conv3d")
    def get_data(self):
        data = super().get_data()
        conv_outputs = data["conv_outputs"]
        conv_T = data["conv_T"]
        conv_X = data["conv_X"]
        conv_Y = data["conv_Y"]
        stride_T = data["stride_T"]
        stride_X = data["stride_X"]
        stride_Y = data["stride_Y"]
        padding = data["padding"]
        return keras.layers.Conv3D(conv_outputs, (conv_T, conv_X, conv_Y),
                                   strides=(stride_T, stride_X, stride_Y),
                                   padding=padding, activation=data["activation"])

class Conv2plus1DConstructor(Conv3DLikeConstructor):
    DISPLAY_NAME = get_locale("app.model_builder.conv2plus1d")
    FIELD__activation_int = create_value_field(Activation, get_locale("app.model_builder.activation_intermediate"),
                                               "relu")

    def get_data(self):
        data = super().get_data()
        conv_outputs = data["conv_outputs"]
        conv_T = data["conv_T"]
        conv_X = data["conv_X"]
        conv_Y = data["conv_Y"]
        stride_T = data["stride_T"]
        stride_X = data["stride_X"]
        stride_Y = data["stride_Y"]
        padding = data["padding"]
        return Conv2DPlus1(conv_outputs, (conv_T, conv_X, conv_Y),
                           strides=(stride_T, stride_X, stride_Y),
                           padding=padding, activation_main=data["activation"],
                           activation_intermediate=data["activation_int"])


class Conv2DConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.conv2d")
    FIELD__conv_outputs = create_value_field(IntNode, get_locale("app.model_builder.convnd.outputs"), 1)
    FIELD__conv_X = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_X"), 3)
    FIELD__conv_Y = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_Y"), 3)
    FIELD__stride_X = create_value_field(IntNode, get_locale("app.model_builder.stride_X"), 1)
    FIELD__stride_Y = create_value_field(IntNode, get_locale("app.model_builder.stride_Y"), 1)
    FIELD__padding = NNPadding
    FIELD__activation = Activation

    def get_data(self):
        data = super().get_data()
        conv_outputs = data["conv_outputs"]
        conv_X = data["conv_X"]
        conv_Y = data["conv_Y"]
        stride_X = data["stride_X"]
        stride_Y = data["stride_Y"]
        padding = data["padding"]
        return keras.layers.Conv2D(conv_outputs, (conv_X, conv_Y),
                                   strides=(stride_X, stride_Y), padding=padding, activation=data["activation"])

class Stride(FormNode):
    DISPLAY_NAME = ""
    FIELD__stride_X = create_value_field(IntNode, get_locale("app.model_builder.stride_X"), 1)
    FIELD__stride_Y = create_value_field(IntNode, get_locale("app.model_builder.stride_Y"), 1)
    FIELD__stride_T = create_value_field(IntNode, get_locale("app.model_builder.stride_T"), 1)

class StrideOption(OptionNode):
    DISPLAY_NAME = get_locale("app.model_builder.stride")
    ITEM_TYPE = Stride
    DEFAULT_VALUE = None

class MaxPooling3DConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.maxpool3d")
    FIELD__pool_X = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_X"), 2)
    FIELD__pool_Y = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_Y"), 2)
    FIELD__pool_T = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_T"), 2)
    FIELD__stride = StrideOption
    FIELD__padding = NNPadding

    def get_data(self):
        data = super().get_data()
        pool_X = data["pool_X"]
        pool_Y = data["pool_Y"]
        pool_T = data["pool_T"]
        stride=data["stride"]
        padding = data["padding"]
        return keras.layers.MaxPooling3D(pool_size=(pool_T, pool_X, pool_Y), strides=stride,
                                         padding=padding)


class MaxPooling2DConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.maxpool2d")
    FIELD__pool_X = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_X"), 2)
    FIELD__pool_Y = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_Y"), 2)
    FIELD__stride_X = create_value_field(IntNode, get_locale("app.model_builder.stride_X"), 1)
    FIELD__stride_Y = create_value_field(IntNode, get_locale("app.model_builder.stride_Y"), 1)
    FIELD__padding = NNPadding

    def get_data(self):
        data = super().get_data()
        pool_X = data["pool_X"]
        pool_Y = data["pool_Y"]
        stride_X = data["stride_X"]
        stride_Y = data["stride_Y"]
        padding = data["padding"]
        return keras.layers.MaxPooling2D(pool_size=(pool_X, pool_Y), strides=(stride_X, stride_Y),
                                         padding=padding)


class ActivationConstructor(Activation):
    def get_data(self):
        data = super().get_data()
        return keras.layers.Activation(data)

class FlattenConstructor(LabelNode):
    DISPLAY_NAME = get_locale("app.model_builder.flatten")

    def get_data(self):
        return keras.layers.Flatten()

class ExpandDimsConstructor(IntNode):
    DISPLAY_NAME = get_locale("app.model_builder.expand")
    DEFAULT_VALUE = -1

    def get_data(self):
        val = super().get_data()
        return tf.keras.layers.Lambda(lambda x: tf.expand_dims(x, val))


@kwarg_builder(TrainableScaling)
class ScaleConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.scale")

    FIELD__use_offset = create_value_field(BoolNode, get_locale("app.model_builder.scale.use_offset"), True)


class BatchNormInit(ComboNode):
    SELECTION_READONLY = True
    VALUES = ["zeros", "ones"]

@kwarg_builder(keras.layers.BatchNormalization)
class BatchNormalizationConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.batch_norm")
    FIELD__axis = create_value_field(IntNode,get_locale("app.model_builder.batch_norm.axis"),-1)
    FIELD__momentum = create_value_field(FloatNode, get_locale("app.model_builder.batch_norm.momentum"), 0.99)
    FIELD__epsilon = create_value_field(FloatNode, get_locale("app.model_builder.batch_norm.epsilon"), 0.001)
    FIELD__center = create_value_field(BoolNode, get_locale("app.model_builder.batch_norm.center"), True)
    FIELD__scale = create_value_field(BoolNode, get_locale("app.model_builder.batch_norm.scale"), True)
    FIELD__beta_initializer=create_value_field(BatchNormInit,
                                               get_locale("app.model_builder.batch_norm.beta_initializer"), "zeros")
    FIELD__gamma_initializer=create_value_field(BatchNormInit,
                                                get_locale("app.model_builder.batch_norm.gamma_initializer"), "ones")

class LayerConstructor(AlternatingNode):
    DISPLAY_NAME = get_locale("app.model_builder.layer")
    SEL__dense = DenseConstructor
    SEL__conv3d = Conv3DConstructor
    SEL__conv2plus1d = Conv2plus1DConstructor
    SEL__conv2d = Conv2DConstructor
    SEL__maxpool3d = MaxPooling3DConstructor
    SEL__maxpool2d = MaxPooling2DConstructor
    SEL__activation = ActivationConstructor
    SEL__expand_dim = ExpandDimsConstructor
    SEL__flatten = FlattenConstructor
    SEL__scale = ScaleConstructor
    SEL__batch_norm = BatchNormalizationConstructor



class LayerSequenceConstructor(ArrayNode):
    DISPLAY_NAME = get_locale("app.model_builder.layers")
    ITEM_TYPE = LayerConstructor


@kwarg_builder(Residual)
class ResidialConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.residual")
    FIELD__main = create_value_field(LayerSequenceConstructor,
                                            get_locale("app.model_builder.residual.main"))
    FIELD__shortcut = create_value_field(LayerSequenceConstructor,
                                            get_locale("app.model_builder.residual.shortcut"))



LayerConstructor.SEL__residual = ResidialConstructor


class SequenceMultiplied(LayerSequenceConstructor):
    def get_data(self):
        return super().get_data(), super().get_data(), super().get_data(), super().get_data()


class SplitConstructor(FormNode):
    FIELD__share = create_value_field(BoolNode, get_locale("app.model_builder.split_share"), False)
    FIELD__sequence = SequenceMultiplied
    
    def get_data(self):
        data = super().get_data()
        if data["share"]:
            dat = data["sequence"][0]
            return PMTSplit(pmt_tuple=(dat, dat, dat, dat))
        else:
            return PMTSplit(pmt_tuple=data["sequence"])

LayerConstructor.SEL__splitmerge = SplitConstructor