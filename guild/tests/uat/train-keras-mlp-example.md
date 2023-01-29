---
doctest: -PY3 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Train Keras MLP example

Keras models can be trained simply by running them.

    >>> cd(example("keras"))

Lets run the `mnist_mlp.py` script:

    >>> run("guild run mnist_mlp.py -y --no-gpus epochs=1",
    ...     ignore=("WARNING", "Refreshing"))
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

    >>> run("guild ls -n")
    README.md
    guild.yml
    mnist_mlp.py
    requirements.txt
    weights.01-0...hdf5
    <exit 0>
