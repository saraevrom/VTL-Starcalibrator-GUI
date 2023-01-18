from tensorflow import keras
import tensorflow as tf
from keras import layers




def create_lambda(index):
    if index==0:
        return layers.Lambda(lambda x: tf.expand_dims(x[:, :8, :8], -1))
    elif index==1:
        return layers.Lambda(lambda x: tf.expand_dims(x[:, :8, 8:], -1))
    elif index==10:
        return layers.Lambda(lambda x: tf.expand_dims(x[:, 8:, :8], -1))
    elif index==11:
        return layers.Lambda(lambda x: tf.expand_dims(x[:, 8:, 8:], -1))

class TriggerModel(keras.Model):
    def __init__(self):
        super().__init__()
        self.pmt_layers = []
        self.create_pmt(0) #00
        self.create_pmt(1) #01
        self.create_pmt(10) #10
        self.create_pmt(11) #11

        self.common_concat = layers.Concatenate()
        self.common_dense1 = layers.Dense(100, activation="relu")
        self.common_dense_output = layers.Dense(2, activation="softmax")


    def create_pmt(self, index):
        #Layer, Accepts train, Accepts mask
        sequence = [
            [create_lambda(index), True, True],
            [layers.LayerNormalization(axis=0), True, False],
            [layers.Conv3D(2, (8, 3, 3)), True, True],
            [keras.layers.MaxPooling3D(pool_size=(16, 2, 2)), True, True],
            [keras.layers.Flatten(), True, True]
        ]
        self.pmt_layers.append(sequence)

    def calculate_pmt(self,inputs,index,training,mask):
        res = inputs
        for layer in self.pmt_layers[index]:
            kwargs = dict()
            if layer[1]:
                kwargs["training"] = training
            if layer[2]:
                kwargs["mask"] = mask
            res = layer[0](res, **kwargs)
        return res

    def call(self, inputs, training=False, mask=None):
        pmts = [self.calculate_pmt(inputs, i, training, mask) for i in range(4)]
        res = self.common_concat(pmts)
        res = self.common_dense1(res)
        res = self.common_dense_output(res)
        return res