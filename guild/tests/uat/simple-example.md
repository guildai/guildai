# Simple example

These tests illustrate Guild's various simplifications.

The code we'll be testing is in the `simple-mnist` example:

    >>> cd("examples/simple-mnist")

We can run a Python script directly as an operation:

    >>> run("echo dummy && guild run train.py epochs=1 -y")
    dummy
    ...
    Step 0: training=0...
    Step 0: validate=0...
    Step 20: training=0...
    Step 20: validate=0...
    ...
    Step 540: training=0...
    Step 540: validate=0...
    Saving trained model
    <exit 0>

The operation is represented simply as the script name:

    >>> run("guild runs")
    [1:...]   train.py  ... ...  completed
    ...
    <exit 0>

The operation is like any other. We can view info:

    >>> run("guild runs info")
    id: ...
    operation: train.py
    status: completed
    started: ...
    stopped: ...
    run_dir: ...
    command: ... -u .../examples/simple-mnist/train.py --epochs 1
    exit_status: 0
    pid:
    <exit 0>

Note the command, which uses the Python intreper (not listed
explicitly above) to run the script directly.

The flag value for `epochs` is passed through as command option.

Here are the flags:

    >>> run("guild runs info -g")
    id: ...
    operation: train.py
    ...
    flags:
      epochs: 1
    <exit 0>

The run writes a number of scalars, which we can view as info with the
`-S` option:

    >>> run("guild runs info -S")
    id: ...
    operation: train.py
    ...
    scalars:
      acc
      biases/max_1
      biases/mean_1
      biases/min_1
      biases/stddev
      loss
      weights/max_1
      weights/mean_1
      weights/min_1
      weights/stddev
      val#acc
      val#biases/max_1
      val#biases/mean_1
      val#biases/min_1
      val#biases/stddev
      val#loss
      val#weights/max_1
      val#weights/mean_1
      val#weights/min_1
      val#weights/stddev
    <exit 0>

We can view the compare columns:

    >>> run("guild compare -t 1")
    run  operation  started  time  status     label  step  loss  acc  val_loss  val_acc
    ...  train.py   ...      ...   completed         540   0...  0... 0...      0...
    <exit 0>
