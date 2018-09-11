# Train Keras `mnist-mlp`

For this example, we'll use the full spelling of "train", which is to
run the `train` operation on the model.

    >>> run("guild run -y --no-gpus keras.mnist/mnist-mlp:train epochs=1",
    ...     timeout=300)
    Limiting available GPUs (CUDA_VISIBLE_DEVICES) to: <none>
    Resolving script dependency
    ...
    Using TensorFlow backend.
    ...
    Test loss: ...
    Test accuracy: ...
    <exit 0>
