# Simple example

These tests illustrate Guild's various simplifications.

The code we'll be testing is in the `tensorflow` example:

    >>> cd(example("tensorflow"))

Let's examine the project models and operation.

The Guild file is a "simplified" format, which means it only defines
operations. The operations are part of an anonymous model (name is
empty) that is created implicitly when the Guild file is loaded.

We can quickly see this using the API:

    >>> from guild import guildfile
    >>> gf = guildfile.for_dir(cwd())
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

    >>> run("guild models")
    <BLANKLINE>
    <exit 0>

However, we do see the operations:

    >>> run("guild ops")
    evaluate  Evaluate a trained MNIST classifier
    train     Train MNIST classifier
    <exit 0>

The project has a default operation, which is defined in
guild.yml. Let's see what it wants to run by looking at a run preview:

    >>> run("guild run", timeout=2)
    You are about to run train
      batch_size: 100
      epochs: 10
    Continue? (Y/n)
    <exit ...>

## Run the default operation

We've see that we can run the train operation by default. Let's run it
for one epoch.

    >>> run("guild run epochs=1 --no-gpus -y")
    ???
    Step 20: ...
    Step 540: ...
    <exit 0>

## View results with compare

The `train` operation, defined in the Guild file, defines non-default columns:

    >>> run("guild compare --table 1")
    run  operation  started  time  status     label                    step  train_loss  train_acc
    ...  train      ...      ...   completed  batch_size=100 epochs=1  540   0...        0...
    <exit 0>

## View results with runs info

    >>> run("guild runs info")
    id: ...
    operation: train
    from: .../tensorflow/guild.yml
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: batch_size=100 epochs=1
    sourcecode_digest: ...
    vcs_commit: ...
    run_dir: ...
    command: ... -um guild.op_main mnist -- --batch_size 100 --epochs 1
    exit_status: 0
    pid:
    tags:
    flags:
      batch_size: 100
      epochs: 1
    scalars:
      acc: ... (step 540)
      biases/max_1: ... (step 540)
      biases/mean_1: ... (step 540)
      biases/min_1: ... (step 540)
      biases/stddev: ... (step 540)
      loss: ... (step 540)
      weights/max_1: ... (step 540)
      weights/mean_1: ... (step 540)
      weights/min_1: ... (step 540)
      weights/stddev: ... (step 540)
      val#acc: ... (step 540)
      val#biases/max_1: ... (step 540)
      val#biases/mean_1: ... (step 540)
      val#biases/min_1: ... (step 540)
      val#biases/stddev: ... (step 540)
      val#loss: ... (step 540)
      val#weights/max_1: ... (step 540)
      val#weights/mean_1: ... (step 540)
      val#weights/min_1: ... (step 540)
      val#weights/stddev: ... (step 540)
    <exit 0>

The `train` operation enables all plugins, so we have additional
scalars that we can view by including the `-s` option to `runs info`.

    >>> run("guild runs info -s")
    id: ...
    scalars:
      acc:
        avg: ... (step 28)
        first: ... (step 0)
        last: ... (step 540)
        max: ... (step 0)
        min: ... (step 0)
        total: ... (step 28)
      biases/max_1:
        ...
      biases/mean_1:
        ...
      biases/min_1:
        ...
      biases/stddev:
        ...
      loss:
        ...
      sys/...
      weights/...
      val#biases/...
      val#biases/mean_1...
      val#biases/min_1...
      val#biases/stddev...
      val#loss...
      val#sys/...
    <exit 0>

## Running scripts directly

We can run a Python script directly as an operation:

    >>> run("guild run mnist.py --no-gpus epochs=1 -y", timeout=120)
    ???
    Step 20:...
    Step 540:...
    <exit 0>

The operation is represented simply as the script name:

    >>> run("guild runs --limit 1")
    [1:...]   mnist.py  ... ...  completed
    ...
    <exit 0>

The operation is like any other.

View using runs info:

    >>> run("guild runs info") # doctest: +REPORT_UDIFF
    id: ...
    operation: mnist.py
    from: .../examples/tensorflow
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: batch_size=100 datadir=data epochs=1 prepare=no rundir=. test=no
    sourcecode_digest: ...
    vcs_commit:...
    run_dir: ...
    command: ... -um guild.op_main mnist
             --batch_size 100
             --datadir data
             --epochs 1
             --rundir .
    exit_status: 0
    pid:
    tags:
    flags:
      batch_size: 100
      datadir: data
      epochs: 1
      prepare: no
      rundir: .
      test: no
    scalars:
      acc: ... (step 540)
      biases/max_1: ... (step 540)
      biases/mean_1: ... (step 540)
      biases/min_1: ... (step 540)
      biases/stddev: ... (step 540)
      loss: ... (step 540)
      weights/max_1: ... (step 540)
      weights/mean_1: ... (step 540)
      weights/min_1: ... (step 540)
      weights/stddev: ... (step 540)
      val#acc: ... (step 540)
      val#biases/max_1: ... (step 540)
      val#biases/mean_1: ... (step 540)
      val#biases/min_1: ... (step 540)
      val#biases/stddev: ... (step 540)
      val#loss: ... (step 540)
      val#weights/max_1: ... (step 540)
      val#weights/mean_1: ... (step 540)
      val#weights/min_1: ... (step 540)
      val#weights/stddev: ... (step 540)
    <exit 0>

Note the command, which uses the Python intreper (not listed
explicitly above) to run the script directly.

We can view the compare columns for the script op - these are default
for scripts:

    >>> run("guild compare -t 1")
    run  operation  started  time  status     label                                                             batch_size  datadir  epochs  prepare  rundir  test  step  acc  biases/max_1  biases/mean_1  biases/min_1  biases/stddev  loss  weights/max_1  weights/mean_1  weights/min_1  weights/stddev
    ...  mnist.py   ... ...  ...   completed  batch_size=100 datadir=data epochs=1 prepare=no rundir=. test=no  100         data     1       no       .       no    540   ...
    <exit 0>

When we compare the last two runs (the `train` op and the `mnist.py` script):

    >>> run("guild compare -t 1 2")
    run  operation  started  time  status     label                                                             batch_size  datadir  epochs  prepare  rundir  test  step  acc  biases/max_1  biases/mean_1  biases/min_1  biases/stddev  loss  weights/max_1  weights/mean_1  weights/min_1  weights/stddev  train_loss  train_acc
    ...  mnist.py   ... ...  ...   completed  batch_size=100 datadir=data epochs=1 prepare=no rundir=. test=no  100         data     1       no       .       no    540   ...
    ...  train      ... ...  ...   completed  batch_size=100 epochs=1                                                                                               540   ...
    <exit 0>

Compare with CSV:

    >>> run("guild compare --csv - 1 2", ignore="Wrote")
    run,operation,started,time,status,label,batch_size,datadir,epochs,prepare,rundir,test,step,acc,biases/max_1,biases/mean_1,biases/min_1,biases/stddev,loss,weights/max_1,weights/mean_1,weights/min_1,weights/stddev,train_loss,train_acc
    ...,mnist.py,...,...,completed,batch_size=100 datadir=data epochs=1 prepare=no rundir=. test=no,100,data,1,False,.,False,540,...
    ...,train,...,...,completed,batch_size=100 epochs=1,,,,,,,540,...
    <exit 0>

Generate a CSV file:

    >>> tmp_dir = mkdtemp()
    >>> csv_path = path(tmp_dir, "compare.csv")

    >>> run("guild compare --csv '%s' 1 2" % csv_path)
    Wrote 2 row(s) to .../compare.csv
    <exit 0>

    >>> cat(csv_path)
    run,operation,started,time,status,label,batch_size,datadir,epochs,prepare,rundir,test,step,acc,biases/max_1,biases/mean_1,biases/min_1,biases/stddev,loss,weights/max_1,weights/mean_1,weights/min_1,weights/stddev,train_loss,train_acc
    ...,mnist.py,...,...,completed,batch_size=100 datadir=data epochs=1 prepare=no rundir=. test=no,100,data,1,False,.,False,540,...
    ...,train,...,...,completed,batch_size=100 epochs=1,,,,,,,540,...
