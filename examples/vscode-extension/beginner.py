import tensorflow as tf

mnist = tf.keras.datasets.mnist

epochs = 10
dropout = 0.2
layer_size = 128

(x_train, y_train), (x_test, y_test) = mnist.load_data()
x_train, x_test = x_train / 255.0, x_test / 255.0

model = tf.keras.models.Sequential(
    [
        tf.keras.layers.Flatten(input_shape=(28, 28)),
        tf.keras.layers.Dense(layer_size, activation='relu'),
        tf.keras.layers.Dropout(dropout),
        tf.keras.layers.Dense(10, activation='softmax'),
    ]
)

model.compile(
    optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy']
)

model.fit(x_train, y_train, epochs=epochs)
model.evaluate(x_test, y_test)
