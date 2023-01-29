---
doctest: -PY3 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Runs after `logreg` train

After we've trained `logreg` we have one run:

    >>> run("guild runs")
    [1:...]  gpkg.mnist/logreg:train  ... ...  completed  batch-size=100 epochs=1 learning-rate=0.5
    <exit 0>
