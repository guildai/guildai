'''Trains a simple deep NN on the MNIST dataset.

Gets to 98.40% test accuracy after 20 epochs
(there is *a lot* of margin for parameter tuning).
2 seconds per epoch on a K520 GPU.
'''

from __future__ import print_function

import argparse

from tensorflow import keras
from keras.datasets import mnist
from keras.models import Sequential
from keras.layers import Dense, Dropout
from tensorflow.keras.optimizers import RMSprop
from keras.utils import np_utils

p = argparse.ArgumentParser()
p.add_argument("--batch-size", type=int, default=128)
p.add_argument("--epochs", type=int, default=20)
p.add_argument("--learning-rate", type=float, default=0.001)
p.add_argument("--dropout", type=float, default=0.2)
p.add_argument("--inner-layers", type=int, default=1)
p.add_argument("--layer-size", type=int, default=512)
p.add_argument("--activation", choices=["relu", "sigmoid", "tanh"], default="relu")
p.add_argument("--10sec", action="store_true", dest="_10sec")

args = p.parse_args()
if args._10sec:
    args.epochs = 1

num_classes = 10

# the data, split between train and test sets
(x_train, y_train), (x_test, y_test) = mnist.load_data()

x_train = x_train.reshape(60000, 784)
x_test = x_test.reshape(10000, 784)
x_train = x_train.astype('float32')
x_test = x_test.astype('float32')
x_train /= 255
x_test /= 255
if args._10sec:
    x_train = x_train[:100]
    y_train = y_train[:100]
    x_test = x_test[:20]
    y_test = y_test[:20]

print(x_train.shape[0], 'train samples')
print(x_test.shape[0], 'test samples')

# convert class vectors to binary class matrices
y_train = np_utils.to_categorical(y_train, num_classes)
y_test = np_utils.to_categorical(y_test, num_classes)

model = Sequential()
model.add(Dense(args.layer_size, activation=args.activation, input_shape=(784,)))
model.add(Dropout(args.dropout))
for _ in range(args.inner_layers):
    model.add(Dense(args.layer_size, activation=args.activation))
    model.add(Dropout(args.dropout))
model.add(Dense(num_classes, activation='softmax'))

model.summary()

model.compile(
    loss='categorical_crossentropy',
    optimizer=RMSprop(learning_rate=args.learning_rate),
    metrics=['accuracy'],
)

history = model.fit(
    x_train,
    y_train,
    batch_size=args.batch_size,
    epochs=args.epochs,
    verbose=1,
    validation_data=(x_test, y_test),
)
score = model.evaluate(x_test, y_test, verbose=0)
print('Test loss:', score[0])
print('Test accuracy:', score[1])
