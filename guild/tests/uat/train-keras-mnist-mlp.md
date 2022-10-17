---
doctest: -PY3 +PY36 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Train Keras `mnist-mlp`

For this example, we'll use the full spelling of "train", which is to
run the `train` operation on the model.

    >>> run("guild run -y --no-gpus gpkg.keras.mnist/mlp:train epochs=1")
    Resolving script
    Using TensorFlow backend...
    Epoch 1/1...
    Test loss:...
    Test accuracy:...
    <exit 0>
