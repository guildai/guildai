# Simple example

These tests illustrate Guild's various simplifications.

The code we'll be testing is in the `simple-mnist` example:

    >>> cd("examples/simple-mnist")

Let's examine the project models and operation.

The Guild file is a "simplified" format, which means it only defines
operations. The operations are part of an anonymous model (name is
empty) that is created implicitly when the Guild file is loaded.

We can quickly see this using the API:

    >>> from guild import guildfile
    >>> gf = guildfile.from_dir(cwd())
    >>> gf.models
    {'': <guild.guildfile.ModelDef ''>}
    >>> gf.models[''] is gf.default_model
    True

The anonymous model has the operations defined in the simplified Guild
file:

    >>> gf.default_model.operations
    [<guild.guildfile.OpDef 'evaluate'>,
     <guild.guildfile.OpDef 'train'>]

When we list the models defined for the project, we get an empty
list. This is because we don't present anonymous models to the user -
anonymous models merely make operations available.

    >>> run("guild models -p .", ignore="Refreshing project")
    <BLANKLINE>
    <exit 0>

However, we do see the operations:

    >>> run("guild ops -p .")
    evaluate  Evaluate a trained model
    train     Train on MNIST
    <exit 0>

The project has a default operation, which is defined in
guild.yml. Let's see what it wants to run by looking at a run preview:

    >>> run("guild run", timeout=2)
    You are about to run train
      batch_size: 100
      epochs: 10
    Continue? (Y/n)
    <exit ...>

## Running the default operation

We've see that we can run the train operation by default. Let's run it
for one epoch.

    >>> run("echo dummy && guild run epochs=1 --no-gpus -y")
    dummy
    ...
    Step 0: training=0...
    Step 0: validate=0...
    Step 20: training=0...
    Step 20: validate=0...
    ...
    Step 540: training=0...
    Step 540: validate=0...
    Saving trained model...
    <exit 0>

## Viewing results with compare

The `train` operation, defined in the Guild file, defines non-default columns:

    >>> run("guild compare --table 1")
    run  operation  started  time  status     label     step  train_loss  train_acc
    ...  train      ...      ...   completed  epochs=1  540   0...        0...
    <exit 0>

## Running scripts directly

We can run a Python script directly as an operation:

    >>> run("echo dummy && guild run train.py --no-gpus epochs=1 -y", timeout=120)
    dummy
    ...
    Step 0: training=0...
    Step 0: validate=0...
    Step 20: training=0...
    Step 20: validate=0...
    ...
    Step 540: training=0...
    Step 540: validate=0...
    Saving trained model...
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
    marked: no
    label:
    run_dir: ...
    command: ... -um guild.op_main train
             --batch_size 100
             --datadir data
             --epochs 1
             --rundir .
    exit_status: 0
    pid:
    objective: loss
    flags:
      batch_size: 100
      datadir: data
      epochs: 1
      prepare: no
      rundir: .
      test: no
    <exit 0>

Note the command, which uses the Python intreper (not listed
explicitly above) to run the script directly.

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

We can view the compare columns for the script op - these are default
for scripts:

    >>> run("guild compare -T 1")
    run  operation  started  time  status     label  batch_size  datadir  epochs  prepare  rundir  test   loss
    ...  train.py   ... ...  ...   completed         100         data     1       False    .       False  0...
    <exit 0>

    run  operation  started  time  status     label  step  loss  acc
    ...  train.py   ...      ...   completed         540   0...  0...
    <exit 0>

When we compare the last two runs (the `train` op and the `train.py` script):

    >>> run("guild compare -T 1 2")
    run  operation  started  time  status     label     batch_size  datadir  epochs  prepare  rundir  test   loss  step  train_loss  train_acc
    ...  train.py   ... ...  ...   completed            100         data     1       False    .       False  0...
    ...  train      ... ...  ...   completed  epochs=1                                                             540   0...        0...
    <exit 0>
