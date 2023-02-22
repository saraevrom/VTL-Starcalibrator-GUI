from common_GUI.tk_forms_assist import *
from common_GUI.tk_forms_assist.factory import create_value_field
from localization import get_locale
from tensorflow import keras
import tensorflow as tf
from .custom_structures import Residual


class Activation(ComboNode):
    DISPLAY_NAME = get_locale("app.model_builder.activation")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "linear"
    VALUES = list(sorted(["linear", "relu", "sigmoid", "softplus", "softsign", "tanh", "selu", "elu"]))


class DenseConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.dense")
    FIELD__units = create_value_field(IntNode, get_locale("app.model_builder.dense.count"), 1)
    FIELD__activation = Activation

    def get_data(self):
        data = super().get_data()
        return keras.layers.Dense(**data)


class NNPadding(ComboNode):
    DISPLAY_NAME = get_locale("app.model_builder.padding")
    SELECTION_READONLY = True
    DEFAULT_VALUE = "valid"
    VALUES = ["valid", "same"]

class Conv3DConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.conv3d")
    FIELD__conv_outputs = create_value_field(IntNode, get_locale("app.model_builder.convnd.outputs"), 1)
    FIELD__conv_X = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_X"), 3)
    FIELD__conv_Y = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_Y"), 3)
    FIELD__conv_T = create_value_field(IntNode, get_locale("app.model_builder.convnd.conv_T"), 8)
    FIELD__stride_X = create_value_field(IntNode, get_locale("app.model_builder.stride_X"), 1)
    FIELD__stride_Y = create_value_field(IntNode, get_locale("app.model_builder.stride_Y"), 1)
    FIELD__stride_T = create_value_field(IntNode, get_locale("app.model_builder.stride_T"), 1)
    FIELD__padding = NNPadding
    FIELD__activation = Activation

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


class MaxPooling3DConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.maxpool3d")
    FIELD__pool_X = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_X"), 2)
    FIELD__pool_Y = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_Y"), 2)
    FIELD__pool_T = create_value_field(IntNode, get_locale("app.model_builder.pool.pool_T"), 2)
    FIELD__stride_X = create_value_field(IntNode, get_locale("app.model_builder.stride_X"), 1)
    FIELD__stride_Y = create_value_field(IntNode, get_locale("app.model_builder.stride_Y"), 1)
    FIELD__stride_T = create_value_field(IntNode, get_locale("app.model_builder.stride_T"), 1)
    FIELD__padding = NNPadding

    def get_data(self):
        data = super().get_data()
        pool_X = data["pool_X"]
        pool_Y = data["pool_Y"]
        pool_T = data["pool_T"]
        stride_T = data["stride_T"]
        stride_X = data["stride_X"]
        stride_Y = data["stride_Y"]
        padding = data["padding"]
        return keras.layers.MaxPooling3D(pool_size=(pool_T, pool_X, pool_Y), strides=(stride_T, stride_X, stride_Y),
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

class LayerConstructor(AlternatingNode):
    DISPLAY_NAME = get_locale("app.model_builder.layer")
    SEL__dense = DenseConstructor
    SEL__conv3d = Conv3DConstructor
    SEL__conv2d = Conv2DConstructor
    SEL__maxpool3d = MaxPooling3DConstructor
    SEL__maxpool2d = MaxPooling2DConstructor
    SEL__expand_dim = ExpandDimsConstructor
    SEL__flatten = FlattenConstructor




class LayerSequenceConstructor(ArrayNode):
    DISPLAY_NAME = get_locale("app.model_builder.layers")
    ITEM_TYPE = LayerConstructor

class ResidialConstructor(FormNode):
    DISPLAY_NAME = get_locale("app.model_builder.residual")
    FIELD__layer_array = LayerSequenceConstructor

    def get_data(self):
        data = super().get_data()
        return Residual(**data)

LayerConstructor.SEL__residual = ResidialConstructor