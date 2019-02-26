# Compare after logreg train

`guild compare` is used to print a tabular report of runs, including
accuracy and loss.

    >>> run("guild compare --table")
    run  operation                started  time  status     label  epochs  batch-size  learning-rate  step  train_loss  train_acc  val_loss  val_acc
    ...  gpkg.mnist/logreg:train  ...      ...   completed         1       100         0.500000       550   ...         ...        ...       ...
