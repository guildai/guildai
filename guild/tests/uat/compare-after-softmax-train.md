# Compare after softmax train

`guild compare` is used to print a tabular report of runs, including
accuracy and loss.

    >>> run("guild compare --table")
    run  model          operation  started  time  status     label  step  accuracy  loss
    ...  mnist-softmax  train      ...      ...   completed         550   ...       ...
    <exit 0>
