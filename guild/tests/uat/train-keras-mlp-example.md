# Train Keras MLP example

Keras models can be trained simply by running them.

    >>> cd(example("keras"))

Lets run the `mnist_mlp.py` script:

    >>> run("guild run mnist_mlp.py -y --no-gpus epochs=1",
    ...     timeout=180, ignore=("WARNING", "Refreshing"))
    Masking available GPUs (CUDA_VISIBLE_DEVICES='')
    Using TensorFlow backend...
    60000/60000 ...
    Test loss: ...
    Test accuracy: ...
    <exit 0>

Here's the run info with all scalars:

    >>> run("guild runs info --all-scalars")
    id: ...
    scalars:
      accuracy:
        avg: ... (step ...)
        first: ... (step 1)
        last: ... (step 1)
        max: ... (step 1)
        min: ... (step 1)
        total: ... (step ...)
      loss:
        avg: ... (step ...)
        first: ... (step 1)
        last: ... (step 1)
        max: ... (step 1)
        min: ... (step 1)
        total: ... (step ...)
      test_accuracy:
        ...
      test_loss:
        ...
      val_accuracy:
        ...
      val_loss:
        ...
    <exit 0>

And files (empty list):

    >>> run("guild ls")
    ???:
      weights.01-0...hdf5
    <exit 0>
