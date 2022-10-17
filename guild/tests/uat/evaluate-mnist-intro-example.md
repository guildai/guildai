---
doctest: -PY3 +PY36 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Evaluate MNIST intro example

Once an `mnist-intro` model is trained, we can run the `evaluate`
operation to test it against all of the test data.

    >>> cd(example("models"))

    >>> run("guild run intro:evaluate -y --no-gpus")
    Resolving data
    Resolving train
    Using run ...
    INFO: [tensorflow] Restoring parameters from ./model/export...
    Test accuracy=0...
    <exit 0>
