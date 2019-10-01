# Run info after `logreg` train

Use `guild runs info` to show information about the latest run:

    >>> run("guild runs info") # doctest: +REPORT_UDIFF
    id: ...
    operation: gpkg.mnist/logreg:train
    from: gpkg.mnist==0.6.0
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: epochs=1
    sourcecode_digest: ...
    run_dir: ...
    command: ... guild.op_main logreg --data-dir mnist-idx-data --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5
    exit_status: 0
    pid:
    flags:
      batch-size: 100
      epochs: 1
      learning-rate: 0.5
    scalars:
      acc: ... (step 550)
      loss: ... (step 550)
      val#acc: ... (step 550)
      val#loss: ... (step 550)
    <exit 0>

We can optionally show env for a run:

    >>> run("guild runs info --env") # doctest: +REPORT_UDIFF
    id: ...
    operation: gpkg.mnist/logreg:train
    from: gpkg.mnist==0.6.0
    status: completed
    started: ...
    stopped: ...
    marked: no
    label: epochs=1
    sourcecode_digest: ...
    run_dir: ...
    command: ... guild.op_main logreg --data-dir mnist-idx-data --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5
    exit_status: 0
    pid:
    flags:
      batch-size: 100
      epochs: 1
      learning-rate: 0.5
    scalars:
      acc: ... (step 550)
      loss: ... (step 550)
      val#acc: ... (step 550)
      val#loss: ... (step 550)
    environment:
      CMD_DIR: ...
      GUILD_HOME: ...
      GUILD_OP: logreg:train
      GUILD_PKG: ...
      GUILD_PLUGINS: ...
      LANG: ...
      LOG_LEVEL: '20'
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
    <exit 0>

JSON output:

    >>> tmp = path(mkdtemp(), "info.json")
    >>> quiet("guild runs info --json > %s" % tmp)
    >>> cat_json(tmp)  # doctest: +REPORT_UDIFF
    {
        "command": "... -um guild.op_main logreg --data-dir mnist-idx-data
                    --run-dir . -- --batch-size 100 --epochs 1 --learning-rate 0.5",
        "exit_status": 0,
        "flags": {
            "batch-size": 100,
            "epochs": 1,
            "learning-rate": 0.5
        },
        "from": "gpkg.mnist==0.6.0",
        "id": "...",
        "label": "epochs=1",
        "marked": "no",
        "operation": "gpkg.mnist/logreg:train",
        "pid": "",
        "run_dir": "...",
        "scalars": {
            "acc": [
                ...,
                550
            ],
            "loss": [
                ...,
                550
            ],
            "val#acc": [
                ...,
                550
            ],
            "val#loss": [
                ...,
                550
            ]
        },
        "sourcecode_digest": "...",
        "started": "...",
        "status": "completed",
        "stopped": "..."
    }

With `--private-attrs`:

    >>> quiet("guild runs info --private-attrs --json > %s" % tmp)
    >>> cat_json(tmp)  # doctest: +REPORT_UDIFF
    {
        "command": "...",
        "exit_status": 0,
        "flags": {
            "batch-size": 100,
            "epochs": 1,
            "learning-rate": 0.5
        },
        "from": "gpkg.mnist==0.6.0",
        "id": "...",
        "label": "epochs=1",
        "marked": "no",
        "opdef": {
            "compare": [
                "flag:epochs",
                "flag:batch-size",
                "flag:learning-rate",
                "loss step as step",
                "loss as train_loss",
                "acc as train_acc",
                "val#loss as val_loss",
                "val#acc as val_acc"
            ],
            "description": "Train the logistic regression",
            "flags": {
                "batch-size": {
                    "default": 100,
                    "description": "Number of images to include in a training batch"
                },
                "epochs": {
                    "default": 5,
                    "description": "Number of epochs to train"
                },
                "learning-rate": {
                    "default": 0.5,
                    "description": "Learning rate"
                }
            },
            "flags-import": [],
            "main": "logreg --data-dir mnist-idx-data --run-dir .",
            "requires": "mnist-dataset"
        },
        "operation": "gpkg.mnist/logreg:train",
        "opref": "package:gpkg.mnist 0.6.0 logreg train",
        "pid": "",
        "run_dir": "...",
        "scalars": {
            "acc": [
                ...,
                550
            ],
            "loss": [
                ...,
                550
            ],
            "val#acc": [
                ...,
                550
            ],
            "val#loss": [
                ...,
                550
            ]
        },
        "sourcecode_digest": "...",
        "started": "...",
        "status": "completed",
        "stopped": "..."
    }
