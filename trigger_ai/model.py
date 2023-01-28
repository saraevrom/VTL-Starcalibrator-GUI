import tensorflow as tf


def create_lambda(index):
    if index==0:
        return tf.keras.layers.Lambda(lambda x: x[:, :, :8, :8])
    elif index==1:
        return tf.keras.layers.Lambda(lambda x: x[:, :, :8, 8:])
    elif index==10:
        return tf.keras.layers.Lambda(lambda x: x[:, :, 8:, :8])
    elif index==11:
        return tf.keras.layers.Lambda(lambda x: x[:, :, 8:, 8:])


def create_trigger_model(frames):
    inputs = tf.keras.Input(shape=(frames, 16, 16))
    print(inputs.shape)
    pmt = []
    for i in [0,1,10,11]:
        cut = create_lambda(i)(inputs)
        print(cut.shape)
        normed = tf.keras.layers.LayerNormalization(axis=1)(cut)
        preconv = tf.keras.layers.Lambda(lambda x: tf.expand_dims(x, -1))(normed)
        conv = tf.keras.layers.Conv3D(2, (8, 3, 3))(preconv)
        pooled = tf.keras.layers.MaxPooling3D(pool_size=(16, 2, 2))(conv)
        flat = tf.keras.layers.Flatten()(pooled)
        pmt.append(flat)

    united = tf.keras.layers.Concatenate()(pmt)
    hidden = tf.keras.layers.Dense(100, activation="relu")(united)
    output = tf.keras.layers.Dense(2, activation="softmax")(hidden)
    return tf.keras.Model(inputs, output)




if __name__=="__main__":
    model = create_trigger_model(128)
    model.summary()