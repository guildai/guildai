# Train `mnist-softmax` preview

By default Guild operations show the user a preview, allowing her to
review the setting before continuing.

Because the prompt waits for user input, we need to terminate the
process using a timeout:

    >>> run("guild run mnist-softmax:train", timeout=2)
    You are about to run gpkg.mnist/mnist-softmax:train
      batch-size: 100
      epochs: 10
    Continue? (Y/n)
    <exit ...>
