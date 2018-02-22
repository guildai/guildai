# Run info after `mnist-softmax` train

Use `guild runs info` to show information about the latest run:

    >>> run("guild runs info") # doctest: +REPORT_UDIFF
    id: ...
    operation: mnist/mnist-softmax:train
    status: completed
    started: ...
    stopped: ...
    rundir: ...
    command: ... softmax --datadir mnist-idx-data --rundir . --batch-size 100 --epochs 1
    exit_status: 0
    pid:
    <exit 0>

We can optionally show files, flags, and env for a run:

    >>> run("guild runs info --files --flags --env") # doctest: +REPORT_UDIFF
    id: ...
    operation: mnist/mnist-softmax:train
    status: completed
    started: ...
    stopped: ...
    rundir: ...
    command: ... guild.op_main softmax --datadir mnist-idx-data --rundir . --batch-size 100 --epochs 1
    exit_status: 0
    pid:
    environment:
      CMD_DIR: .../guild-uat
      GUILD_PLUGINS: cpu,disk,gpu,memory
      LANG: ...
      LOG_LEVEL: 20
      MODEL_DIR: .../site-packages/gpkg/mnist
      PATH: ...
      PWD: .../guild-uat
      PYTHONPATH: ...
      SCRIPT_DIR:
      TEMP: ...
    flags:
      batch-size: 100
      epochs: 1
    files:
      mnist-idx-data
      mnist-idx-data/t10k-images-idx3-ubyte.gz
      mnist-idx-data/t10k-labels-idx1-ubyte.gz
      mnist-idx-data/train-images-idx3-ubyte.gz
      mnist-idx-data/train-labels-idx1-ubyte.gz
      train
      train/events.out.tfevents...
      validate
      validate/events.out.tfevents...
    <exit 0>
