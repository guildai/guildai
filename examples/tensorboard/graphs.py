import os

from datetime import datetime
from packaging import version

import tensorflow as tf
from tensorflow import keras

print("TensorFlow version: ", tf.__version__)
assert (
    version.parse(tf.__version__).release[0] >= 2
), "This notebook requires TensorFlow 2.0 or above."

train_epochs = 5
batch_size = 64
dropout = 0.2

# Define the model.
model = keras.models.Sequential(
    [
        keras.layers.Flatten(input_shape=(28, 28)),
        keras.layers.Dense(32, activation='relu'),
        keras.layers.Dropout(dropout),
        keras.layers.Dense(10, activation='softmax'),
    ]
)

model.compile(
    optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy']
)

(train_images, train_labels), _ = keras.datasets.fashion_mnist.load_data()
train_images = train_images / 255.0

# Define the Keras TensorBoard callback.
logdir = (
    os.getenv("TRAIN_LOGDIR")
    or ("logs/fit/" + datetime.now().strftime("%Y%m%d-%H%M%S"))
)
tensorboard_callback = keras.callbacks.TensorBoard(log_dir=logdir)

# Train the model.
model.fit(
    train_images,
    train_labels,
    batch_size=batch_size,
    epochs=train_epochs,
    callbacks=[tensorboard_callback],
)


# The function to be traced.
@tf.function
def my_func(x, y):
    # A simple hand-rolled layer.
    return tf.nn.relu(tf.matmul(x, y))


# Set up logging.
stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
logdir = os.getenv("FUNC_LOGDIR") or 'logs/func/%s' % stamp
writer = tf.summary.create_file_writer(logdir)

# Sample data for your function.
x = tf.random.uniform((3, 3))
y = tf.random.uniform((3, 3))

# Bracket the function call with
# tf.summary.trace_on() and tf.summary.trace_export().
tf.summary.trace_on(graph=True, profiler=True)
# Call only one tf.function when tracing.
z = my_func(x, y)
with writer.as_default():
    tf.summary.trace_export(name="my_func_trace", step=0, profiler_outdir=logdir)
