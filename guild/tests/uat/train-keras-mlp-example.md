# Train Keras MLP example

The keras plugin supports a single `train` operation for Keras models
that it detects. We can use the `mnist_mlp` Keras example to
illustrate.

    >>> cd("guild-examples/keras/mnist")

Let's train the model with one epoch:

    >>> run("guild train -y mnist_mlp epochs=1")
    Using TensorFlow backend.
    ...
    60000 train samples
    10000 test samples
    _________________________________________________________________
    Layer (type)                 Output Shape              Param #
    =================================================================
    dense_1 (Dense)              (None, 512)               401920
    _________________________________________________________________
    dropout_1 (Dropout)          (None, 512)               0
    _________________________________________________________________
    dense_2 (Dense)              (None, 512)               262656
    _________________________________________________________________
    dropout_2 (Dropout)          (None, 512)               0
    _________________________________________________________________
    dense_3 (Dense)              (None, 10)                5130
    =================================================================
    Total params: 669,706
    Trainable params: 669,706
    Non-trainable params: 0
    _________________________________________________________________
    Train on 60000 samples, validate on 10000 samples
    Epoch 1/1
    <BLANKLINE>
    ...
    Test loss: ...
    Test accuracy: ...
    <exit 0>
