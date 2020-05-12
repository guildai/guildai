import os

from datetime import datetime

import tensorflow as tf
from tensorflow import keras

# Hyperparameters
num_units = 16
dropout = 0.2
train_epochs = 5
optimizer = 'adam'

fashion_mnist = tf.keras.datasets.fashion_mnist

(x_train, y_train), (x_test, y_test) = fashion_mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0

model = tf.keras.models.Sequential(
    [
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(num_units, activation=tf.nn.relu),
        tf.keras.layers.Dropout(dropout),
        tf.keras.layers.Dense(10, activation=tf.nn.softmax),
    ]
)
model.compile(
    optimizer=optimizer, loss='sparse_categorical_crossentropy', metrics=['accuracy'],
)

logdir = os.getenv("LOGDIR") or "logs/image/" + datetime.now().strftime("%Y%m%d-%H%M%S")
tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir)


model.fit(
    x_train,
    y_train,
    epochs=train_epochs,
    callbacks=[tensorboard_callback],
    validation_data=(x_test, y_test),
)
