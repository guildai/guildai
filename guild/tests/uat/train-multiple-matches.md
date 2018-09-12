# Train multiple matches

Guild lets the user specify a partial model name for operations, but
if there are multiple matches for the specified term, Guild exits with
an error message.

    >>> run("guild run -y mnist:train epochs=1")
    guild: there are multiple models that match 'mnist'
    Try specifying one of the following:
      gpkg.mnist/mnist-cnn
      gpkg.mnist/mnist-samples
      gpkg.mnist/mnist-softmax
    <exit 1>
