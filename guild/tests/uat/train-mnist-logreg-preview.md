# Train `logreg` preview

By default Guild operations show the user a preview, allowing her to
review the setting before continuing.

Because the prompt waits for user input, we need to terminate the
process using a timeout:

    >>> run("guild run logreg:train", timeout=2)
    You are about to run gpkg.mnist/logreg:train
      batch-size: 100
      epochs: 5
      learning-rate: 0.5
    Continue? (Y/n)
    <exit ...>
