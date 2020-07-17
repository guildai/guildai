'''Trains a simple deep NN on the MNIST dataset.

Gets to 98.40% test accuracy after 20 epochs
(there is *a lot* of margin for parameter tuning).
2 seconds per epoch on a K520 GPU.
'''

from __future__ import print_function

import json

import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from keras.optimizers import RMSprop

class Config(object):
    def __init__(self, filename):
        self.__dict__.update(json.load(open(filename)))

config = Config("config.json")

if config._10sec:
    config.epochs = 1

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(config.train_count, config.reshape_size)
x_test = x_test.reshape(config.test_count, config.reshape_size)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
if config._10sec:
    x_train = x_train[:100]
    y_train = y_train[:100]
    x_test = x_test[:20]
    y_test = y_test[:20]

print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = keras.utils.to_categorical(y_train, config.num_classes)
y_test = keras.utils.to_categorical(y_test, config.num_classes)

model = Sequential()
model.add(Dense(config.layer_size, activation=config.activation,
                input_shape=(config.reshape_size,)))
model.add(Dropout(config.dropout))
for _ in range(config.inner_layers):
    model.add(Dense(config.layer_size, activation=config.activation))
    model.add(Dropout(config.dropout))
model.add(Dense(config.num_classes, activation=config.output_activation))

model.summary()

model.compile(loss='categorical_crossentropy',
              optimizer=RMSprop(learning_rate=config.learning_rate),
              metrics=['accuracy'])

history = model.fit(x_train, y_train,
                    batch_size=config.batch_size,
                    epochs=config.epochs,
                    verbose=1,
                    validation_data=(x_test, y_test))
score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])
