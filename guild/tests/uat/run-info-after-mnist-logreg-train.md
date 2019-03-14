# Run info after `logreg` train

Use `guild runs info` to show information about the latest run:

    >>> run("guild runs info") # doctest: +REPORT_UDIFF
    id: ...
    operation: gpkg.mnist/logreg:train
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    run_dir: ...
    command: ... guild.op_main logreg --data-dir mnist-idx-data --run-dir . --batch-size 100 --epochs 1 --learning-rate 0.5
    exit_status: 0
    pid:
    flags:
      batch-size: 100
      epochs: 1
      learning-rate: 0.5
    <exit 0>

We can optionally show files and env for a run:

    >>> run("guild runs info --files --env") # doctest: +REPORT_UDIFF
    id: ...
    operation: gpkg.mnist/logreg:train
    status: completed
    started: ...
    stopped: ...
    marked: no
    label:
    run_dir: ...
    command: ... guild.op_main logreg --data-dir mnist-idx-data --run-dir . --batch-size 100 --epochs 1 --learning-rate 0.5
    exit_status: 0
    pid:
    flags:
      batch-size: 100
      epochs: 1
      learning-rate: 0.5
    environment:
      CMD_DIR: ...
      GUILD_HOME: ...
      GUILD_OP: logreg:train
      GUILD_PKG: ...
      GUILD_PLUGINS: ...
      LANG: ...
      LOG_LEVEL: 20
      MODEL_DIR: .../site-packages/gpkg/mnist
      MODEL_PATH: .../site-packages/gpkg/mnist
      PATH: ...
      PWD: ...
      PYTHONPATH: ...
      REQUIREMENTS_PATH: ...
      RUN_DIR: ...
      RUN_ID: ...
      SCRIPT_DIR: ...
      TEMP: ...
    files:
      checkpoint
      events.out.tfevents...
      export
      export/saved_model.pb
      export/variables
      export/variables/variables.data-00000-of-00001
      export/variables/variables.index
      mnist-idx-data
      mnist-idx-data/t10k-images-idx3-ubyte
      mnist-idx-data/t10k-images-idx3-ubyte.gz
      mnist-idx-data/t10k-labels-idx1-ubyte
      mnist-idx-data/t10k-labels-idx1-ubyte.gz
      mnist-idx-data/train-images-idx3-ubyte
      mnist-idx-data/train-images-idx3-ubyte.gz
      mnist-idx-data/train-labels-idx1-ubyte
      mnist-idx-data/train-labels-idx1-ubyte.gz
      model.ckpt-550.data-00000-of-00001
      model.ckpt-550.index
      model.ckpt-550.meta
      val
      val/events.out.tfevents...
    <exit 0>
