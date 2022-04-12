---
doctest: -PY3 +PY36 +PY37 # 2022-04-11 these tests fail on github actions because TF 1.14 fails to install. We need to update to a more current tensorflow version that has wheels available.
---

# Compare after logreg train

`guild compare` is used to print a tabular report of runs, including
accuracy and loss.

    >>> run("guild compare --table")
    run  operation                started  time  status     label                                      epochs  batch-size  learning-rate  step  train_loss  train_acc  val_loss  val_acc
    ...  gpkg.mnist/logreg:train  ...      ...   completed  batch-size=100 epochs=1 learning-rate=0.5  1       100         0.5            550   ...         ...        ...       ...
    <exit 0>
