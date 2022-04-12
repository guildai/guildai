---
doctest: -PY3 +PY36 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# MNIST example runs after intro train

Once we've trained the MNIST intro example, we can see an associated
run:

    >>> run("guild runs -Fo mnist-intro:train --limit 1")
    [1:...]  mnist-intro:train (...examples/models)  ...  completed  batch-size=100 epochs=1 lr=0.5
    <exit 0>
